#!/usr/bin/env python3
"""
Helper methods for ECS scripts
"""
import boto3
import sys
import time

from scripts import utils


# polling interval
SLEEP_TIME_S = 5

print_progress = utils.printProgress

class TimeoutException(Exception):
    pass

def print_events(response, size=10):
    for service_response in response.get('services'):
        events = service_response.get('events')
        i = 0
        for event in events:
            msg = event.get('message')
            dt = event.get('createdAt')
            utils.printWarning(f'{dt} {msg}')
            i += 1
            if i >= size: break

def deployment_is_stable(deployment, start_time, stale_s):
    dt = deployment.get('createdAt').strftime('%s')
    running = deployment.get('runningCount')
    desired = deployment.get('desiredCount')
    status = deployment.get('status')
    age_s =  start_time - int(dt)
    if stale_s and (age_s > stale_s):
        utils.printWarning(f'Deployment state info may be stale ({int(age_s)}s), waiting for a newer info')
        return False
    if (running == desired) and status == 'PRIMARY':
        return True
    return False

def has_recent_event(service_response, start_time, stale_s):
    events = service_response.get('events')
    if not events:
        return False
    event = events[0]
    dt = event['createdAt'].strftime('%s')
    age_s =  start_time - int(dt)
    if age_s > stale_s:
        utils.printWarning(f'Most recent event is stale ({int(age_s)}s)')
        return False
    return True

def service_is_stable(service_response):
    running = service_response.get('runningCount')
    desired = service_response.get('desiredCount')
    if desired == running:
        return True
    utils.printProgress()
    return False

# After tasks show as RUNNING they may not be healthy, you must check that.
def tasks_are_healthy(ecs_client, cluster_name, service_name):

    next_token = ''
    healthy = 0
    while True:
        task_response = ecs_client.list_tasks(
            cluster=cluster_name, serviceName=service_name,
            nextToken=next_token, maxResults=100
        )
        tasks = task_response.get('taskArns')
        next_token = task_response.get('nextToken')

        for task in ecs_client.describe_tasks(cluster=cluster_name, tasks=tasks).get('tasks'):
            task_arn = task.get('taskArn')
            status = task.get('healthStatus')
            if status != 'HEALTHY':
                utils.printWarning(f'task {task_arn} status: {status}')
                return False
            healthy += 1
        if not next_token: break

    utils.printInfo(f'{service_name} all {healthy} tasks are healthy')
    return True


def poll_cluster_state(ecs_client, cluster_name, service_names, polling_timeout, stale_s=None):
    """ 
    Poll services in an ECS cluster for steady state.
    """

    utils.printInfo(f'Polling services: {service_names} in cluster: {cluster_name}, timeout {polling_timeout}s')
    start_time = time.time()
    prev_event_msg = ''
    services = service_names.copy()
    last_response = []
    while services:
        time.sleep(SLEEP_TIME_S)
        if (time.time() - start_time) > polling_timeout:
            print_events(last_response)
            raise TimeoutException(f'Polling timed out! Check {service_names} status.')

        response = ecs_client.describe_services(cluster=cluster_name, services=services)
        last_response = response
        if not response.get('services'):
            utils.printWarning('describe_services got an empty services response')
            continue
        for service_response in response.get('services'):
            if stale_s:
                # check that the service has started to change based on events
                if not has_recent_event(service_response, start_time, stale_s):
                    continue
            service_name = service_response.get('serviceName')
            if service_is_stable(service_response):
                if not tasks_are_healthy(ecs_client, cluster_name, service_name):
                    utils.printWarning(f'{service_name} tasks are still not healthy')
                    continue
                services.remove(service_name)
                elapsed = int(time.time() - start_time)
                utils.printSuccess(f'{service_name} is in a steady state. Elapsed: {elapsed}s')

def poll_deployment_state(ecs_client, cluster_name, service_name, polling_timeout, stale_s=None):
    """ 
    Poll service in an ECS cluster for a complete deployment.
    """

    utils.printInfo(f'Polling service: {service_name} in cluster: {cluster_name}')
    start_time = time.time()
    prev_event_msg = ''
    last_response = []
    while True:
        time.sleep(SLEEP_TIME_S)
        response = ecs_client.describe_services(cluster=cluster_name, services=[service_name])
        last_response = response
        if not response.get('services'):
            utils.printWarning('describe_services got an empty services response')
            continue
        service_response = response.get('services')[0]

        deployments = service_response.get('deployments')
        if deployment_is_stable(deployments[0], start_time, stale_s):
            if not tasks_are_healthy(ecs_client, cluster_name, service_name):
                utils.printWarning(f'{service_name} tasks are still not healthy')
                continue
            elapsed = int(time.time() - start_time)
            utils.printSuccess(f'{service_name} deploy is complete. Elapsed: {elapsed}s')
            break

        if (time.time() - start_time) > polling_timeout:
            print_events(last_response)
            raise TimeoutException(f'Polling timed out! Check {service_name} status.')


