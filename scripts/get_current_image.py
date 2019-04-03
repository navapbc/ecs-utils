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
    parser = argparse.ArgumentParser(description='create KMS key')

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
        print(f'Service lookup failed: {err}')
        sys.exit(1)

    try: 
        image = client.describe_task_definition(
            taskDefinition=task_definition
        ).get('taskDefinition').get('containerDefinitions')[0].get('image')
    except Exception as err:
        print(f'Task lookup failed: {err}')
        sys.exit(1)
    
    return image


def main():
    args = parse_args()
    client = boto3.client('ecs', args.region)
    print(get_ecs_image_url(client, args.cluster, args.service))


if __name__ == '__main__':
    main()
