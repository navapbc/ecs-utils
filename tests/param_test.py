"""Test case for param"""
import botocore
import unittest
from unittest import TestCase
from unittest.mock import patch
from scripts.param import delete_param, put_param, get_param

class ParamTestCase(TestCase):
    """Test the kms command line utility."""

    @patch('boto3.client')
    def test_put_param(self,mock_boto):
        mock_client = mock_boto.return_value
        error_response = {'Error': {'Code': 'ParameterAlreadyExists'}}

        mock_client.put_parameter.side_effect = botocore.exceptions.ClientError(error_response, 'put_parameter')


        with self.assertRaises(SystemExit) as cm:
            put_param('foo', 'bar', 'us-east-1')

    @patch('boto3.client')
    def test_get_param(self, mock_boto):
        error_response = {'Error': {'Code': 'ParameterNotFound'}}

        mock_client = mock_boto.return_value
        mock_client.get_parameter.return_value = 'test'
        self.assertEqual(get_param('foo','us-east-1'), 'test')
        mock_client.get_parameter.side_effect = botocore.exceptions.ClientError(error_response,'put_parameter')
        with self.assertRaises(SystemExit):
            get_param('foo', 'us-east-1')

    @patch('boto3.client')
    def test_delete_param(self, mock_boto):
        error_response = {'Error': {'Code': 'ParameterNotFound'}}

        mock_client = mock_boto.return_value
        mock_client.delete_parameter.side_effect = botocore.exceptions.ClientError(error_response,'put_parameter')
        with self.assertRaises(SystemExit):
            delete_param('foo', 'us-east-1')

if __name__ == '__main__':
    unittest.main()
