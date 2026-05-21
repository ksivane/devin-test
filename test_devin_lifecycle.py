import unittest
from unittest.mock import patch, MagicMock
import importlib.util
import os
import sys

# Workaround for hyphen in filename
spec = importlib.util.spec_from_file_location("devin_pr", "./devin-pr.py")
devin_pr = importlib.util.module_from_spec(spec)
sys.modules["devin_pr"] = devin_pr
spec.loader.exec_module(devin_pr)

class TestDevinSessionLifecycle(unittest.TestCase):

    @patch('devin_pr.requests.post')
    def test_create_session_success(self, mock_post):
        """Test successful creation of a Devin session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"session_id": "test_id", "url": "http://test.url"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        pr_url = "https://github.com/owner/repo/pull/1"
        result = devin_pr.create_session(pr_url)

        self.assertEqual(result["session_id"], "test_id")
        self.assertEqual(result["url"], "http://test.url")
        mock_post.assert_called_once()
        # Verify that the PR URL is in the prompt
        args, kwargs = mock_post.call_args
        self.assertIn(pr_url, kwargs['json']['prompt'])

    @patch('devin_pr.requests.get')
    def test_get_session_success(self, mock_get):
        """Test successful retrieval of session status."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "running", "status_detail": "doing_things"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        devin_id = "test_id"
        result = devin_pr.get_session(devin_id)

        self.assertEqual(result["status"], "running")
        self.assertEqual(result["status_detail"], "doing_things")
        mock_get.assert_called_once()
        self.assertIn(devin_id, mock_get.call_args[0][0])

    @patch('devin_pr.get_session')
    @patch('devin_pr.requests.post')
    def test_resume_session_success(self, mock_post, mock_get_session):
        """Test successful resumption of a session."""
        # Mock the post request to resume
        mock_post_response = MagicMock()
        mock_post_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_response

        # Mock the subsequent get_session call
        mock_get_session.return_value = {"session_id": "test_id", "status": "running"}

        pr_url = "https://github.com/owner/repo/pull/1"
        devin_id = "test_id"
        result = devin_pr.resume_session(devin_id, pr_url)

        self.assertEqual(result["session_id"], "test_id")
        mock_post.assert_called_once()
        mock_get_session.assert_called_once_with(devin_id)
        # Verify message payload
        args, kwargs = mock_post.call_args
        self.assertIn(pr_url, kwargs['json']['message'])

if __name__ == '__main__':
    unittest.main()
