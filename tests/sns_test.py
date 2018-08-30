"""Test case for sns."""

import unittest
from unittest import TestCase
from unittest.mock import patch

from scripts.sns import set_up_sns


class SnsTestCase(TestCase):
    """Test the sns command line utility."""
    @patch("boto3.client")
    @patch("boto3.resource")
    @patch("builtins.input")
    @patch("scripts.utils.printSuccess")
    def test_setup(self, mock_print, mock_input, mock_resource, mock_client):
        mock_sns = mock_client.return_value
        mock_input.return_value = True

        mock_sns.list_subscriptions_by_topic.return_value = {
            "Subscriptions": [{
                "Protocol": "email",
                "Endpoint": "test@test.com",
                "SubscriptionArn": "arn123"
            }]
        }

        set_up_sns({"region": "a", "alert_email": "test@test.com", "sns-topic": "test-topic"})
        mock_print.assert_called_with(
            "Done creating SNS topic & subscription for alerts.")


if __name__ == '__main__':
    unittest.main()
