#!/usr/bin/env python3
"""
Script to manage AWS param store values.
"""
import botocore
import boto3
import argparse
import sys
import json

from scripts import utils
from scripts import kms_crypt as kms


def parse_args():
    parser = argparse.ArgumentParser(
        description='Manage AWS Parameter store params'
    )
    parser.add_argument(
        'action',
        action='store',
        choices=['list', 'get', 'put', 'delete'],
        help='List, retrieve, store, or delete parameters'
    )
    parser.add_argument(
        'name',
        help='Full name of the parameter to retrieve or store',
        nargs='?'
    )
    parser.add_argument(
        'value',
        help='Value to set for the parameter',
        nargs='?'
    )
    parser.add_argument(
        '--region', '-r',
        help='AWS region'
    )
    parser.add_argument(
        '--force', '-f',
        help='Overwrite existing parameter',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--verbose', '-v',
        help='Print additional output',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--plaintext', '-p',
        help='Retrieve value in ssm as plaintext (default is decrypt)',
        action='store_true',
        default=False
    )
    parser.add_argument('--kms-key-alias', '-a',
                        help='KMS key alias for storing a value encrypted',
                        default=None
                        )
    return parser.parse_args()


class ParamException(Exception):
    pass

def list_params(namespace, region):
    """ List all parameters, filtered by the namespace"""
    ssm = boto3.client('ssm', region)
    return ssm.describe_parameters(
        Filters=[{
            'Key': 'Name',
            'Values': [namespace]
        }]
    )


def print_params_verbose(params):
    """ Print detailed parameter information """
    out_format = '{:<20} {:<15} {:<20} {:<4} {:<22} {}'
    print(out_format.format('  Parameter', ' Type',
                            ' Modified By', 'Ver', ' Date', '  Description'))
    for entry in params['Parameters']:
        print(out_format.format(
            entry['Name'],
            entry['Type'],
            entry['LastModifiedUser'].split('/')[1],
            entry['Version'],
            entry['LastModifiedDate'].strftime('%b %d, %Y %I:%M%p'),
            entry['Description'])
        )


def print_params_simple(params):
    """ Print found parameters as ENV variables """
    for entry in params['Parameters']:
        print(entry['Name'])


def put_param(name, value, region, kms_key_alias=None,
              overwrite=False, plaintext=True):
    """Store the name and value"""
    ssm = boto3.client('ssm', region)

    try:
        if kms_key_alias:
            kms_key = kms.get_kms_key_id(
                kms_key_alias, region
            )
            if not kms_key:
                raise ParamException(
                    f'No key found for alias {kms_key_alias} {region}'
                )
            result = ssm.put_parameter(
                Name=name,
                Description=name,
                Value=value,
                Type='SecureString',
                KeyId=kms_key,
                Overwrite=overwrite
            )
        else:
            utils.print_warning('Creating without encryption')
            result = ssm.put_parameter(
                Name=name,
                Description=name,
                Value=value,
                Type='String',
                Overwrite=overwrite
            )

        utils.print_info(json.dumps(result))
    except botocore.exceptions.ClientError as e:
        if (e.response['Error']['Code'] == 'ParameterAlreadyExists'):
            utils.print_error(
                f'setting "{name}" already exists, use -f to overwrite.')
            sys.exit(1)
        raise e


def get_param(name, region, decrypt=True):
    """Retrieve parameter."""
    ssm = boto3.client('ssm', region)
    try:
        return ssm.get_parameter(Name=name, WithDecryption=decrypt)
    except botocore.exceptions.ClientError as e:
        if (e.response['Error']['Code'] == 'ParameterNotFound'):
            utils.print_error(f'Cannot find {name}')
            sys.exit(1)
        raise e


def delete_param(name, region):
    """Remove SSM parameter."""
    ssm = boto3.client('ssm', region)
    try:
        utils.print_info(json.dumps(ssm.delete_parameter(Name=name)))
    except botocore.exceptions.ClientError as e:
        if (e.response['Error']['Code'] == 'ParameterNotFound'):
            utils.print_error(f'Cannot find {name}')
            sys.exit(1)
            raise e


def main():
    args = parse_args()

    if args.name is None:
        utils.print_error('Please supply parameter name.')
        exit(1)

    if (args.action == 'list'):
        params = list_params(args.name, args.region)
        if args.verbose:
            print_params_verbose(params)
        else:
            print_params_simple(params)
    elif (args.action == 'get'):
        print(
            get_param(
                args.name, args.region, decrypt=(
                    not args.plaintext)
            ).get('Parameter').get('Value')
        )
    elif (args.action == 'put'):
        if args.value is None:
            utils.print_error('Please supply parameter value.')
            sys.exit(1)
        put_param(args.name, args.value, args.region, args.kms_key_alias,
                  overwrite=args.force, plaintext=args.plaintext)
    elif (args.action == 'delete'):
        delete_param(args.name, args.region)


if __name__ == '__main__':
    main()
