#!/usr/bin/env python3
"""
rolling_replace.py Rolling ASG replacement script

This script provides a pattern for replacing EC2 instances in an Autoscaling
group running ECS. It assumes you have already updated the launch cfg.
(e.g. updated the desired AMI id). This script does not update the launch cfg.

See README.md to understand the proper usage of this script

"""
import argparse
import boto3
import math
import time

from scripts import utils
from scripts import ecs_utils

SLEEP_TIME_S = 5
# polling timeout for ECS steady state after instance launch, or for draining
# note, in some cases, instances will not finish draining until the previous
# batch of instances are live.
TIMEOUT_S = 1200

def parse_args():
    parser = argparse.ArgumentParser(
        description='Does a rolling replacement of an ASG'
    )
    parser.add_argument('--cluster-name', required=True,
                        help='ECS cluster name e.g. cluster-a')
    parser.add_argument('--region', required=True,
                        help='AWS region')
    parser.add_argument('--batches', required=False, default=3,
                        help='Number of batches in replacing instances')
    parser.add_argument('--ami-id',
                        help='AMI ID to verify in new instances.')
    parser.add_argument('--drain-timeout-s',
                        default=TIMEOUT_S,
                        help='Time to wait for instances to complete draining.')
    parser.add_argument('--force', '-f',
                        help="Ignore downtime warning due to capacity.",
                        default=False,
                        action='store_true',
                        )
    return parser.parse_args()


class RollingException(Exception):
    pass


class RollingTimeoutException(Exception):
    pass


def get_ami_id(instance):
    for attr in instance.get('attributes'):
        if attr.get('name') == 'ecs.ami-id':
            return attr.get('value')
    raise RollingException('No ami id found for this instance.')


def get_services(ecs_client, cluster_name):
    services = []
    service_arns = ecs_client.list_services(
        cluster=cluster_name
    ).get('serviceArns')
    for service_arn in service_arns:
        services.append(service_arn.split('service/')[1])
    return services


def get_container_instance_arns(ecs_client, cluster_name):
    instance_arns = []
    next_token = ''
    while True:
        instances = ecs_client.list_container_instances(
            cluster=cluster_name, maxResults=100, nextToken=next_token)
        arns = instances.get('containerInstanceArns')
        instance_arns += arns
        next_token = instances.get('nextToken')
        if not next_token:
            break
    return instance_arns


def get_already_updated_instances(ecs_response, ami_id):
    instances = []

    for container_instance in ecs_response.get('containerInstances'):
        instance_id = container_instance.get('ec2InstanceId')
        status = container_instance.get('status')
        if status == 'DRAINING':
            # unexpected but we should proceed with terminating it
            # because we already verified that the services were in a steady
            # state.
            utils.print_warning(f'{instance_id} was already draining')
            continue
        this_ami_id = get_ami_id(container_instance)
        utils.print_info(f'Instance to drain: {instance_id}/{this_ami_id}')
        if this_ami_id == ami_id:
            utils.print_warning(
                f'{instance_id} already uses ami_id {ami_id}. Skipping.'
            )
            instances.append(instance_id)
    return instances


def batch_instances(instances, batch_count):
    batches = []
    for i in range(0, len(instances), batch_count):
        batches.append(instances[i:i + batch_count])
    return batches


def rolling_replace_instances(ecs, ec2, cluster_name, batches, ami_id, force, drain_timeout_s):

    replace_start_time = time.time()
    services = get_services(ecs, cluster_name)
    if not services:
        raise RollingException('No services found in cluster. exiting.')
    utils.print_info(
        f'Checking cluster {cluster_name}, services {str(services)} are stable'
    )
    ecs_utils.poll_cluster_state(
        ecs, cluster_name, services, polling_timeout=120
    )
    instances = get_container_instance_arns(ecs, cluster_name)
    # batches determines the number of instances you want to replace at once.
    # Choose conservatively, as this process temporarily reduces your capacity.
    # But note each batch can be time consuming (up to 10m per batch)

    batch_count = math.ceil(len(instances) / batches)
    utils.print_info(f'You have {len(instances)} instances.')
    utils.print_info(f'Terminating in batches of {batch_count}')
    if len(instances) <= batch_count:
        utils.print_warning(
            f'Terminating {batch_count} instances will cause downtime.'
        )
        if not force:
            raise RollingException('Quitting, use --force to over-ride.')
    instance_batches = batch_instances(instances, batch_count)
    for to_drain in instance_batches:
        if len(to_drain) > 100:
            utils.print_error('Batch size exceeded 100, try using more batches.')
            raise RollingException(
                f'Quitting, batch size exceeded 100: {batch_count}.'
            )
        response = ecs.describe_container_instances(
            cluster=cluster_name, containerInstances=to_drain)

        if not response.get('containerInstances'):
            raise RollingException('No containerInstances found.')

        # don't drain or teriminate any instances that are already up to date
        # (if the user provided the --ami-id flag)
        done_instances = get_already_updated_instances(response, ami_id)
        if len(done_instances) == len(to_drain):
            # move on if the whole batch is already up to date
            continue

        # drain instances in this batch
        ecs.update_container_instances_state(cluster=cluster_name,
                                             status='DRAINING',
                                             containerInstances=to_drain)
        utils.print_info(f'Wait for drain to complete with {drain_timeout_s}s timeout...')
        start_time = time.time()
        while len(done_instances) < len(to_drain):
            if (time.time() - start_time) > drain_timeout_s:
                raise RollingTimeoutException('Waiting for instance to complete draining. Giving up.')
            time.sleep(SLEEP_TIME_S)
            response = ecs.describe_container_instances(
                cluster=cluster_name, containerInstances=to_drain)
            for container_instance in response.get('containerInstances'):
                instance_id = container_instance.get('ec2InstanceId')
                running_tasks = container_instance.get('runningTasksCount')
                if running_tasks > 0:
                    utils.print_progress()
                    continue
                if instance_id not in done_instances:
                    utils.print_info(f'{instance_id} is drained, terminate!')
                    ec2.terminate_instances(InstanceIds=[instance_id])
                    done_instances.append(instance_id)
        # new instance will take as much as 10m to go into service
        # then we wait for ECS to resume a steady state before moving on
        ecs_utils.poll_cluster_state(ecs, cluster_name,
                                     services, polling_timeout=drain_timeout_s)
    utils.print_success(f'EC2 instance replacement process complete! {int(time.time() - replace_start_time)}s elapsed')


def main():
    args = parse_args()
    ecs = boto3.client('ecs', args.region)
    ec2 = boto3.client('ec2', args.region)
    rolling_replace_instances(ecs, ec2, args.cluster_name,
                              int(args.batches), args.ami_id, args.force,
                              int(args.drain_timeout_s))


if __name__ == '__main__':
    main()
