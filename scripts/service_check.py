#!/usr/bin/env python3
"""
Polls until a deployed ECS service to verify a completed deployment.
(i.e. ECS has completed its scheduling instructions)
NOTE: this should be run immediately after a service update.
If the script detects a deployment that is not recent it considers it
"stale", if older than STALE_S
"""
import argparse
import boto3
import sys
import time

from scripts import utils
from scripts import ecs_utils

STALE_S = 120
POLLING_TIMEOUT = 300

def parse_args():
    parser = argparse.ArgumentParser(description = 'Checks an ECS service status')
    parser.add_argument('app_name',
        help='ECS service name, e.g. basic-app')
    parser.add_argument('--cluster-name', required=True,
            help='ECS cluster name, e.g. cluster-a')
    parser.add_argument('--region', required=True,
            help='AWS region, e.g. us-east-1')
    parser.add_argument('--stale-s', default=STALE_S,
            help='Ignore events older than --stale_s (seconds). default 60s')
    parser.add_argument('--timeout-s', default=POLLING_TIMEOUT,
            help='Polling timeout --timeout_s (seconds). default 300s')
    return parser.parse_args()

def main():
    args = parse_args()
    region = args.region
    ecs_client = boto3.client('ecs', region)
    ecs_utils.poll_deployment_state(
        ecs_client, args.cluster_name, args.app_name,
        polling_timeout=int(args.timeout_s), stale_s=int(args.stale_s)
    )
    

if __name__ == '__main__':
    main()
