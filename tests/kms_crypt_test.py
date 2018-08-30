"""Test case for kms."""

import unittest
from unittest import TestCase
from unittest.mock import patch

from scripts.kms_crypt import encrypt, decrypt


class KmsTestCase(TestCase):
    """Test the kms command line utility."""
    @patch('boto3.client')
    @patch('base64.b64encode')
    def test_encrypt(self, mock_base64, mock_boto):
        mock_client = mock_boto.return_value
        encrypted_blob = b'\x01\x02\x02\x00xK\x7f]\xa4\xa1\xd4Kl\rg'
        mock_client.encrypt.return_value = {'CiphertextBlob': encrypted_blob}
        mock_base64.return_value = b'abc123'


        encrypt({'foo': 'bar'}, '1234', 'us-east-1', 'test')
        mock_base64.assert_called_with(encrypted_blob)

    @patch('boto3.client')
    @patch('base64.b64decode')
    def test_decrypt(self, mock_base64, mock_boto):
        mock_client = mock_boto.return_value
        mock_client.decrypt.return_value = {'Plaintext': b'abc123'}
        mock_base64.return_value = b'abc123'

        decrypt('abc123', {'foo': 'bar'}, 'us-east-1')
        mock_client.decrypt.assert_called_with(
            CiphertextBlob=b'abc123',
            EncryptionContext={'foo': 'bar'})


if __name__ == '__main__':
    unittest.main()
