#!/usr/bin/env python3
"""
Wrapper to encrypt/decrypt data with KMS.
"""
import boto3
import base64
import argparse
import json
import sys

from scripts import utils


def parse_args():
    parser = argparse.ArgumentParser(description='KMS encryption/decryption')
    parser.add_argument('action',
                        action='store',
                        choices=['encrypt', 'decrypt'],
                        help='encrypt/decrypt blob')
    parser.add_argument('--region','-r', required=True,
                        help='AWS region')
    parser.add_argument('--context','-c', required=True,
                        help='KMS Encryption Context, quoted json')
    parser.add_argument('--alias','-a',
                        help='alias for creating kms key')
    parser.add_argument('data',
                        help='The data to encrypt/decrypt')
    return parser.parse_args()


def encrypt(data, alias, context, region):
    """generates a kms encrypted data blob"""
    if isinstance(data, str):
        plaintext = str.encode(data, 'ascii')
    else:
        plaintext = data
    client = boto3.client('kms', region)
    key_id = get_kms_key_id(alias, region)
    kms_encryption = client.encrypt(
        KeyId=key_id,
        Plaintext=plaintext,
        EncryptionContext=context
    )
    utils.printInfo(f'Encryption using keyId {key_id} with context: {context}')
    return base64.b64encode(kms_encryption['CiphertextBlob']).decode('ascii')


def decrypt(blob, context, region):
    """decrypts a kms encrypted data blob"""

    client = boto3.client('kms', region)
    kms_decryption = client.decrypt(
        CiphertextBlob=base64.b64decode(blob),
        EncryptionContext=context
    )

    return kms_decryption['Plaintext']

def get_kms_key_id(alias, region):
    alias = f'alias/{alias}'
    kms_key_id = find_key_id_by_alias(region, alias)
    if not kms_key_id:
        utils.printWarning(f'No KMS key found for alias: {alias}')
    return kms_key_id

def find_key_id_by_alias(region, alias):
    client = boto3.client('kms', region)
    # TODO: fix bug where it won't find the key alias if you have over 100 kms
    # keys.
    # http://boto3.readthedocs.io/en/latest/reference/services/kms.html
    # (KMS.Client.list_aliases)
    aliases = client.list_aliases(Limit=100)
    foundAliases = list(
        filter(lambda x: x['AliasName'] == alias, aliases.get('Aliases')))

    if len(foundAliases) < 1:
        return None
    return foundAliases[0].get('TargetKeyId')


def main():
    args = parse_args()
    if args.data:
        if len(args.data) < 8:
            utils.printError('Secrets should be 8 characters or greater')
            sys.exit(1)
    if (args.action == 'encrypt'):
        if not args.alias:
            utils.printError('You must provide --alias to encrypt')
            sys.exit(1)
        print(encrypt(args.data, args.alias, json.loads(args.context), args.region))
    elif (args.action == 'decrypt'):
        print(decrypt(args.data, json.loads(args.context), args.region))
    else:
        utils.printError('Commands are encrypt/decrypt')
        sys.exit(1)


if __name__ == '__main__':
    main()
