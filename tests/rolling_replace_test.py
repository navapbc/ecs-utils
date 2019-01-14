"""Test case for ecs_utils."""
import copy
from unittest import TestCase
from unittest.mock import patch

import scripts.rolling_replace as rolling_replace

# note: we override time.time()
rolling_replace.TIMEOUT_S = 10
rolling_replace.DRAIN_TIMEOUT_S = 10
# reduce polling time to speed tests
rolling_replace.SLEEP_TIME_S = 0

GOOD_SERVICE = {
    'serviceArns': ['cluster-foo/service/foo'],
    'services': [{
        'serviceName': 'service-foo',
        'runningCount': 2,
        'desiredCount': 2,
    }]
}

INSTANCE_ARNS = {
    'containerInstanceArns': ['biz', 'baz'],
    'nextoken': None
}

DESCRIBE_INSTANCES = {
    'containerInstances': [
        {
            'ec2InstanceId': 'biz',
            'status': 'ACTIVE',
            'runningTasksCount': 0,
            'attributes': [{'name': 'ecs.ami-id', 'value': 'ami1'}]
        }
    ]
}

# postive base test case
# batch of 2, 1 instance each batch, 2nd batch takes 2 tries
MOCK_RESPONSES = []
batch1 = copy.deepcopy(DESCRIBE_INSTANCES)
MOCK_RESPONSES.append(batch1)
MOCK_RESPONSES.append(batch1)

batch2 = copy.deepcopy(DESCRIBE_INSTANCES)
batch2['containerInstances'][0]['ec2InstanceId'] = 'baz'
batch2_iter2 = copy.deepcopy(batch2)  # running count 0
batch2['containerInstances'][0]['runningTasksCount'] = 1
MOCK_RESPONSES += [batch2, batch2]
MOCK_RESPONSES += [batch2_iter2, batch2_iter2]


class RollingTestCase(TestCase):
    """Test the roling_replace module."""

    def setUp(self):
        # time will advance by 1sec every polling iteration
        self.patcher = patch('time.time')
        self.mock_time = self.patcher.start()
        self.mock_time.side_effect = list(range(100))
        self.addCleanup(self.patcher.stop)

    @patch('scripts.ecs_utils.poll_cluster_state')
    @patch('boto3.client')
    def test_replace_positive(self, mock_boto, mock_poll):
        mock_client = mock_boto.return_value
        mock_poll.return_value = True
        mock_client.list_services.return_value = GOOD_SERVICE
        mock_client.list_container_instances.return_value = INSTANCE_ARNS
        mock_client.describe_container_instances.side_effect = MOCK_RESPONSES
        rolling_replace.rolling_replace_instances(
            mock_client, mock_client, 'cluster-foo', 2, '', False
        )

    @patch("scripts.utils.print_warning")
    @patch('scripts.ecs_utils.poll_cluster_state')
    @patch('boto3.client')
    def test_replace_warn_ami(self, mock_boto, mock_poll, mock_warn):
        mock_client = mock_boto.return_value
        mock_poll.return_value = True
        mock_client.list_services.return_value = GOOD_SERVICE
        mock_client.list_container_instances.return_value = INSTANCE_ARNS
        mock_client.describe_container_instances.side_effect = MOCK_RESPONSES
        rolling_replace.rolling_replace_instances(
            mock_client, mock_client, 'cluster-foo', 2, 'ami1', False
        )
        mock_warn.assert_called_with(
            'biz already uses ami_id ami1. Skipping.')

    @patch('scripts.ecs_utils.poll_cluster_state')
    @patch('boto3.client')
    def test_replace_check_ami(self, mock_boto, mock_poll):
        mock_client = mock_boto.return_value
        mock_poll.return_value = True
        mock_client.list_services.return_value = GOOD_SERVICE
        mock_client.list_container_instances.return_value = INSTANCE_ARNS
        mock_client.describe_container_instances.side_effect = MOCK_RESPONSES
        rolling_replace.rolling_replace_instances(
            mock_client, mock_client, 'cluster-foo', 2, 'ami2', False
        )

    @patch('scripts.ecs_utils.poll_cluster_state')
    @patch('boto3.client')
    def test_replace_still_running(self, mock_boto, mock_poll):
        mock_client = mock_boto.return_value
        mock_poll.return_value = True
        mock_client.list_services.return_value = GOOD_SERVICE
        mock_client.list_container_instances.return_value = INSTANCE_ARNS
        responses = copy.deepcopy(MOCK_RESPONSES)
        # modify response to make batch2 chronically bad
        responses[4]['containerInstances'][0]['runningTasksCount'] = 1
        responses[5]['containerInstances'][0]['runningTasksCount'] = 1
        bad_response = responses[4]
        responses += [bad_response]*100
        mock_client.describe_container_instances.side_effect = responses
        with self.assertRaises(rolling_replace.RollingTimeoutException):
            rolling_replace.rolling_replace_instances(
                mock_client, mock_client, 'cluster-foo', 2, '', False
            )

    @patch("scripts.utils.print_warning")
    @patch('scripts.ecs_utils.poll_cluster_state')
    @patch('boto3.client')
    def test_replace_prevent_downtime(self, mock_boto, mock_poll, mock_warn):
        mock_client = mock_boto.return_value
        mock_poll.return_value = True
        mock_client.list_services.return_value = GOOD_SERVICE
        mock_client.list_container_instances.return_value = INSTANCE_ARNS
        with self.assertRaises(rolling_replace.RollingException):
            # batch size of 1 will take your service down
            rolling_replace.rolling_replace_instances(
                mock_client, mock_client, 'cluster-foo', 1, '', False
            )
        mock_warn.assert_called_with(
            'Terminating 2 instances will cause downtime.'
        )

    @patch('boto3.client')
    def test_replace_no_service(self, mock_boto):
        mock_client = mock_boto.return_value
        with self.assertRaises(rolling_replace.RollingException):
            rolling_replace.rolling_replace_instances(
                mock_client, mock_client, 'cluster-foo', 3, '', False
            )
