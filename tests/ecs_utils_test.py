"""Test case for ecs_utils."""
import copy
import datetime
import unittest
from unittest import TestCase
from unittest.mock import patch

import scripts.ecs_utils as ecs_utils

# speed up the polling
ecs_utils.SLEEP_TIME_S = 0
# note: we override time.time()
POLL_S = 10

GOOD_SERVICE = {
    'services': [{
        'serviceName': 'service-foo',
        'runningCount': 2,
        'desiredCount': 2,
        'deployments': [{
            'runningCount': 2,
            'desiredCount': 2,
            'status': 'PRIMARY',
            'rolloutState': 'COMPLETED',
            'createdAt': datetime.time()
        }]
    }]
}

INPROGRESS_SERVICE = copy.deepcopy(GOOD_SERVICE)
INPROGRESS_SERVICE['services'][0]['deployments'][0]['rolloutState'] = 'IN_PROGRESS'

BAD_SERVICE = copy.deepcopy(GOOD_SERVICE)
BAD_SERVICE['services'][0]['deployments'][0]['status'] = 'BAD'
BAD_SERVICE['services'][0]['deployments'][0]['rolloutState'] = 'BAD'
BAD_SERVICE['services'][0]['runningCount'] = 1

INACTIVE_SERVICE = copy.deepcopy(GOOD_SERVICE)
INACTIVE_SERVICE['services'][0]['desiredCount'] = 0
INACTIVE_SERVICE['services'][0]['runningCount'] = 0 


BAD_TASKS = {'tasks': [
    {'healthStatus': 'HEALTHY', 'taskArn': 'foo'},
    {'healthStatus': 'UNHEALTHY', 'taskArn': 'bar'}
]}

GOOD_TASKS = {'tasks': [
    {'healthStatus': 'HEALTHY', 'taskArn': 'foo'},
    {'healthStatus': 'HEALTHY', 'taskArn': 'bar'}
]}

TASKS = {
    'taskArns': ['foo', 'bar'],
    'nextoken': None
}

EMPTY_TASKS = copy.deepcopy(TASKS)
EMPTY_TASKS['taskArns'] = []


class EcsTestCase(TestCase):
    """Test the ecs utils module."""

    def setUp(self):
        # time will advance by 1sec every polling iteration
        self.patcher = patch('time.time')
        self.mock_time = self.patcher.start()
        self.mock_time.side_effect = list(range(100))
        self.addCleanup(self.patcher.stop)

    @patch('boto3.client')
    def test_poll_cluster_positive(self, mock_boto):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.list_tasks.return_value = TASKS
        mock_client.describe_tasks.return_value = GOOD_TASKS
        ecs_utils.poll_cluster_state(mock_client, 'cluster-foo', ['service-foo'], POLL_S)

    @patch('boto3.client')
    def test_poll_cluster_new_arn(self, mock_boto):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.list_tasks.return_value = TASKS
        mock_client.describe_tasks.return_value = GOOD_TASKS
        ecs_utils.poll_cluster_state(mock_client, 'cluster-foo', ['cluster-foo/service-foo'], POLL_S)

    @patch('boto3.client')
    def test_poll_cluster_matching_cluster_and_service_name(self, mock_boto):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.list_tasks.return_value = TASKS
        mock_client.describe_tasks.return_value = GOOD_TASKS
        ecs_utils.poll_cluster_state(mock_client, 'service-foo', ['service-foo'], POLL_S)


    @patch('boto3.client')
    def test_poll_cluster_with_inactive_service(self, mock_boto):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = INACTIVE_SERVICE
        mock_client.list_tasks.return_value = EMPTY_TASKS
        mock_client.describe_tasks.side_effect = Exception('Tasks cannot be empty.')
        ecs_utils.poll_cluster_state(mock_client, 'cluster-foo', ['service-foo'], POLL_S)

    @patch('scripts.ecs_utils.print_events')
    @patch('boto3.client')
    def test_poll_cluster_timeout(self, mock_boto, mock_print_events):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = BAD_SERVICE
        with self.assertRaises(ecs_utils.TimeoutException):
            ecs_utils.poll_cluster_state(mock_client, 'cluster-foo', ['service-foo'], POLL_S)


    @patch('scripts.ecs_utils.print_events')
    @patch('boto3.client')
    def test_poll_cluster_bad_tasks(self, mock_boto, mock_print_events):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.list_tasks.return_value = TASKS
        mock_client.describe_tasks.return_value = BAD_TASKS
        with self.assertRaises(ecs_utils.TimeoutException):
            ecs_utils.poll_cluster_state(mock_client, 'cluster-foo', ['service-foo'], POLL_S)

    @patch('scripts.ecs_utils.print_events')
    @patch('boto3.client')
    def test_poll_deployment_positive(self, mock_boto, mock_print_events):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.list_tasks.return_value = TASKS
        mock_client.describe_tasks.side_effect = [BAD_TASKS, GOOD_TASKS]
        ecs_utils.poll_deployment_state(mock_client, 'cluster-foo', 'service-foo', POLL_S)

    @patch('scripts.ecs_utils.print_events')
    @patch('boto3.client')
    def test_poll_deployment_in_progres_timeout(self, mock_boto, mock_print_events):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = INPROGRESS_SERVICE
        with self.assertRaises(ecs_utils.TimeoutException):
            ecs_utils.poll_deployment_state(mock_client, 'cluster-foo', ['service-foo'], POLL_S)

    @patch('scripts.ecs_utils.print_events')
    @patch('boto3.client')
    def test_poll_deployment_bad_deploy(self, mock_boto, mock_print_events):
        mock_client = mock_boto.return_value

        mock_client.describe_services.return_value = BAD_SERVICE
        mock_client.list_tasks.return_value = TASKS
        with self.assertRaises(ecs_utils.TimeoutException):
            ecs_utils.poll_deployment_state(mock_client, 'cluster-foo', 'service-foo', POLL_S)

    @patch('scripts.ecs_utils.print_events')
    @patch('boto3.client')
    def test_poll_deployment_bad_tasks(self, mock_boto, mock_print_events):
        mock_client = mock_boto.return_value
        mock_client.describe_services.return_value = GOOD_SERVICE
        mock_client.list_tasks.return_value = TASKS
        mock_client.describe_tasks.side_effect = [BAD_TASKS] * 50
        with self.assertRaises(ecs_utils.TimeoutException):
            ecs_utils.poll_deployment_state(mock_client, 'cluster-foo', 'service-foo', POLL_S)
