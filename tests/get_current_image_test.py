"""Test case for get-current-image"""
import botocore
import unittest
from unittest import TestCase
from unittest.mock import patch
from scripts.get_current_image import get_ecs_image_url

GOOD_SERVICE = {
    'services': [{
        'taskDefinition': 'arn:aws:test_task_definition',
    }]
}

GOOD_TASKD = {
    'taskDefinition': {
        'containerDefinitions' : [{
            'image': '123.amazonaws.com/test_service:latest'
        }]
    }
}


class ImageTestCase(TestCase):
    """Test the ecs image utility."""

    @patch('boto3.client')
    def test_positive(self,mock_boto):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.describe_task_definition.return_value = GOOD_TASKD
        image = get_ecs_image_url(mock_client, 'cluster-foo', 'service-foo')
        mock_client.describe_task_definition.assert_called_with(taskDefinition='arn:aws:test_task_definition')
        assert(image == '123.amazonaws.com/test_service:latest')

    @patch('boto3.client')
    def test_no_task(self,mock_boto):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.describe_task_definition.return_value = {}
        with self.assertRaises(AttributeError):
            get_ecs_image_url(mock_client, 'cluster-foo', 'service-foo')

if __name__ == '__main__':
    unittest.main()