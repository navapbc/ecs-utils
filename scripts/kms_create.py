#!/usr/bin/env python3
"""
Wrapper for creating KMS keys.
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
    parser.add_argument('--alias','-a', required=True,
                        help='alias for creating kms key')
    return parser.parse_args()



def create_kms_key(region, alias):
    """creates a KMS key and optionally aliases it"""

    client = boto3.client('kms', region)
    key_id = client.create_key(Description='KMS key')['KeyMetadata']['KeyId']
    if alias:
        client.create_alias(AliasName=f'alias/{alias}', TargetKeyId=key_id)
    return key_id


def main():
    args = parse_args()
    print(create_kms_key(args.region, args.alias))


if __name__ == '__main__':
    main()
