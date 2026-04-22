import os
import django
from unittest.mock import MagicMock, patch
import unittest
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edjobster.settings')
django.setup()

from settings.decorators import handle_career_site_ai_credits
from settings.models import Company, Feature, FeatureUsage, CreditWallet, CreditHistory
from job.models import Job

class TestCreditsDecorator(unittest.TestCase):

    def setUp(self):
        self.usage_codes = ["Rjms"]
        self.company = MagicMock(spec=Company)
        self.company.id = 1
        self.company.name = "TestCompany"

    @patch('settings.models.Company.objects.get')
    @patch('settings.models.Feature.objects.get')
    @patch('settings.models.FeatureUsage.objects.filter')
    @patch('settings.models.CreditWallet.objects.select_for_update')
    @patch('settings.models.CreditHistory.objects.create')
    @patch('job.models.Job.objects.get')
    def test_decorator_deducts_on_zero_score(self, mock_job_get, mock_history, mock_wallet_select, mock_usage_filter, mock_feature_get, mock_company_get):
        # Setup Mocks
        mock_company_get.return_value = self.company
        
        mock_feature = MagicMock(spec=Feature)
        mock_feature_get.return_value = mock_feature
        
        mock_usage = MagicMock(spec=FeatureUsage)
        mock_usage.used_credit = 5
        mock_usage_filter.return_value.exists.return_value = True
        mock_usage_filter.return_value.__iter__.return_value = [mock_usage]
        
        mock_wallet = MagicMock(spec=CreditWallet)
        mock_wallet.used_credit = 10
        mock_wallet_select.return_value.get_or_create.return_value = (mock_wallet, False)

        # Mock Job
        mock_job = MagicMock(spec=Job)
        mock_job.company = self.company
        mock_job_get.return_value = mock_job

        # Define a test function with zero result
        @handle_career_site_ai_credits(self.usage_codes)
        def dummy_rjms_func(job_id):
            return {"rjms": 0} # Zero score

        # Call the decorated function
        result = dummy_rjms_func(job_id=123)

        # Assertions
        self.assertEqual(result["rjms"], 0)
        # Verify credit deduction logic was called
        mock_wallet.save.assert_called_once()
        self.assertEqual(mock_wallet.used_credit, 15) # 10 + 5
        mock_history.assert_called_once()

    @patch('job.models.Job.objects.get')
    @patch('settings.models.FeatureUsage.objects.filter')
    @patch('settings.models.Feature.objects.get')
    @patch('settings.models.CreditWallet.objects.select_for_update')
    def test_decorator_extracts_job_id_from_background_args(self, mock_wallet_select, mock_feature_get, mock_usage_filter, mock_job_get):
        # Mocking for avoid deduction logic crash
        mock_usage_filter.return_value.exists.return_value = False
        
        mock_job = MagicMock(spec=Job)
        mock_job.company = self.company
        mock_job_get.return_value = mock_job

        @handle_career_site_ai_credits(self.usage_codes)
        def run_rjms_background(candidate_id, job_id, resume_text, assessment_result, sms):
            return None

        # Call with positional args as it would be from threading.Thread
        run_rjms_background(1001, 123, "resume", {}, 80.0)
        
        # Verify it used the second argument as job_id
        mock_job_get.assert_called_with(id=123)

    @patch('django.db.transaction.atomic')
    def test_decorator_handles_error_response(self, mock_atomic):
        @handle_career_site_ai_credits(self.usage_codes)
        def error_func(job_id):
            return {"error": "Failed"}

        result = error_func(job_id=123)
        
        # Should NOT trigger deduction if error in result
        mock_atomic.assert_not_called()
        self.assertEqual(result["error"], "Failed")

if __name__ == '__main__':
    unittest.main()
