#!/usr/bin/env python3
"""
Returns the latest image running in an ECS service
"""
import boto3
import base64
import argparse
import sys

from scripts import utils


def parse_args():
    parser = argparse.ArgumentParser(description='Get the current docker image for an ECS service.')

    parser.add_argument('--region','-r', required=True,
                        help='AWS region')
    parser.add_argument('--cluster','-c',
                        help='ECS cluster name')
    parser.add_argument('--service','-s',
                        help='ECS service name')
    return parser.parse_args()



def get_ecs_image_url(client, cluster, service):
    """Gets the current docker image url of an ECS service"""

    try:
        task_definition = client.describe_services(
            cluster=cluster, services=[service]
        ).get('services')[0].get('taskDefinition')
    except Exception as err:
        sys.stderr.write(f'Service lookup failed: {err}')
        raise err

    try: 
        image = client.describe_task_definition(
            taskDefinition=task_definition
        ).get('taskDefinition').get('containerDefinitions')[0].get('image')
    except Exception as err:
        sys.stderr.write(f'Task lookup failed: {err}')
        raise err
    
    return image

def get_client(region):
    return boto3.client('ecs', region)

def main():
    args = parse_args()
    client = get_client(args.region)
    sys.stdout.write(get_ecs_image_url(client, args.cluster, args.service))


if __name__ == '__main__':
    main()
