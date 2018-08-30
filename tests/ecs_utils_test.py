"""Test case for ecs_utils."""
import botocore
import unittest
from unittest import TestCase
from unittest.mock import patch
import scripts.ecs_utils as ecs_utils

class EcsTestCase(TestCase):
    """Test the ecs utils module."""

    @patch('boto3.client')
    def test_poll_cluster_state(self, mock_boto):
        mock_client = mock_boto.return_value
        ecs_utils.poll_cluster_state(mock_client, 'cluster-foo', ['service-foo'], 10, 10)

