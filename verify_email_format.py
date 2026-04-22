import os
import sys
import re
from unittest.mock import MagicMock, patch

# Mock Django settings and models before importing the target function
sys.modules['django.conf'] = MagicMock()
sys.modules['settings.models'] = MagicMock()
sys.modules['django.template.loader'] = MagicMock()

# Now import the function to test
# We need to add the project path to sys.path
project_path = '/mnt/bac58a27-cbda-474f-ad94-75e91adbb52f/Edjobster_Backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from common.format_email_body import format_email_body_bulke_mailSend

def test_format_email_body():
    print("Starting verification tests...")

    # 1. Mock Data
    mock_candidate = MagicMock(spec=['first_name', 'last_name', 'webform_candidate_data'])
    del mock_candidate.__iter__
    mock_candidate.first_name = "John"
    mock_candidate.last_name = "Doe"
    mock_candidate.webform_candidate_data = {
        "Personal Details": {"mobile": "1234567890"}
    }

    mock_job1 = MagicMock()
    mock_job1.title = "Software Engineer"
    mock_job1.company.name = "Tech Corp"
    mock_job1.dynamic_job_data = {
        "Create Job": {"title": "Software Engineer"}
    }

    mock_job2 = MagicMock()
    mock_job2.title = "Senior Developer"
    mock_job2.company.name = "Innovate Ltd"
    mock_job2.dynamic_job_data = {
        "Create Job": {"title": "Senior Developer"}
    }

    mock_account = MagicMock()
    mock_account.first_name = "Admin"
    mock_account.company.name = "EdJobster"

    # Mock QuerySet behavior for jobs
    mock_jobs = [mock_job1, mock_job2]

    # Mock Module.objects.filter
    with patch('settings.models.Module.objects.filter') as mock_filter:
        mock_filter.return_value.values_list.return_value = [] # No dynamic modules for now

        # Test Case 1: Direct attributes
        body = "Hello ${candidate_first_name}, the job is ${job_title} at ${job_company}."
        expected = "Hello John, the job is Software Engineer, Senior Developer at Tech Corp, Innovate Ltd."
        
        result = format_email_body_bulke_mailSend(
            body=body,
            candidate=mock_candidate,
            job=mock_jobs,
            account=mock_account
        )
        print(f"Test Case 1 (Direct attributes): {'PASSED' if result == expected else 'FAILED'}")
        if result != expected:
            print(f"  Expected: {expected}")
            print(f"  Result:   {result}")

        # Test Case 2: Custom placeholders
        body = "Alert: ${custom_alert}"
        placeholders = {"custom_alert": "Urgent Action Required"}
        expected = "Alert: Urgent Action Required"
        
        result = format_email_body_bulke_mailSend(
            body=body,
            placeholders=placeholders
        )
        print(f"Test Case 2 (Custom placeholders): {'PASSED' if result == expected else 'FAILED'}")
        if result != expected:
            print(f"  Result: {result}")

        # Test Case 3: Mixed mapping
        body = "Hi ${candidate_first_name}, apply for ${job_opening_title}."
        # Note: job_opening_title should map to title due to my fix forparts[1] == "opening"
        expected = "Hi John, apply for Software Engineer, Senior Developer."
        
        result = format_email_body_bulke_mailSend(
            body=body,
            candidate=mock_candidate,
            job=mock_jobs
        )
        print(f"Test Case 3 (job_opening_title): {'PASSED' if result == expected else 'FAILED'}")
        if result != expected:
            print(f"  Result: {result}")

if __name__ == "__main__":
    try:
        test_format_email_body()
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
