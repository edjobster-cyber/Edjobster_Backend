from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from .models import GeneratedLetter, LetterSettings
from unittest.mock import patch
from account.models import Account, Company
import json

class LetterGenerationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name="Test Company")
        self.user = Account.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="password123",
            company_id=self.company.id
        )
        self.client.force_login(self.user)

    @patch('letters.views.generate_and_save_letter')
    def test_offer_letter_generator(self, mock_generate):
        mock_generate.return_value = ({"content": "Generated Offer Letter"}, None)
        url = reverse('generate-offer-letter')
        data = {
            'candidate_full_name': 'John Doe',
            'candidate_first_name': 'John',
            'company_name': 'Test Company'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        mock_generate.assert_called_once()

    @patch('letters.views.generate_and_save_letter')
    def test_appointment_letter_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Appointment Letter", None)
        url = reverse('generate-appointment-letter')
        data = {
            'employee_full_name': 'John Doe',
            'company_name': 'Test Company'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_confirmation_letter_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Confirmation Letter", None)
        url = reverse('generate-confirmation-letter')
        data = {
            'employee_full_name': 'John Doe',
            'company_name': 'Test Company'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_experience_letter_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Experience Letter", None)
        url = reverse('generate-experience-letter')
        data = {
            'employee_full_name': 'John Doe',
            'company_name': 'Test Company'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_increment_letter_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Increment Letter", None)
        url = reverse('generate-increment-letter')
        data = {
            'employee_full_name': 'John Doe',
            'company_name': 'Test Company'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_relieving_letter_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Relieving Letter", None)
        url = reverse('generate-relieving-letter')
        data = {
            'employee_full_name': 'John Doe',
            'company_name': 'Test Company'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_leave_policy_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Leave Policy", None)
        url = reverse('generate-leave-policy')
        data = {
            'company_name': 'Test Company',
            'policy_effective_date': '01/01/2026'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_wfh_policy_generator(self, mock_generate):
        mock_generate.return_value = ("Generated WFH Policy", None)
        url = reverse('generate-wfh-policy')
        data = {
            'company_name': 'Test Company',
            'policy_effective_date': '01/01/2026'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_freelancer_contract_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Freelancer Contract", None)
        url = reverse('generate-freelancer-contract')
        data = {
            'company_name': 'Test Company',
            'freelancer_full_name': 'Jane Smith'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_nda_generator(self, mock_generate):
        mock_generate.return_value = ("Generated NDA", None)
        url = reverse('generate-nda')
        data = {
            'company_name': 'Test Company',
            'counterparty_full_name': 'Jane Smith'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_onboarding_letter_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Onboarding Plan", None)
        url = reverse('generate-onboarding')
        data = {
            'employee_full_name': 'John Doe',
            'role_title': 'Developer'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_evp_builder_generator(self, mock_generate):
        mock_generate.return_value = ("Generated EVP Letter", None)
        url = reverse('generate-evp-builder')
        data = {
            'company_name': 'Test Company',
            'target_role_family': 'Engineering'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_employer_branding_post_generator(self, mock_generate):
        mock_generate.return_value = ("Generated Branding Post", None)
        url = reverse('generate-branding-post')
        data = {
            'company_name': 'Test Company',
            'platform': 'LinkedIn'
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

    @patch('letters.views.generate_and_save_letter')
    def test_offer_letter_generator_with_nested_payload(self, mock_generate):
        mock_generate.return_value = ({"content": "Generated Offer Letter"}, None)
        url = reverse('generate-offer-letter')
        data = {
            "candidate_full_name": "Ayush Kamani",
            "candidate_first_name": "ayush",
            "candidate_address": "24\n123",
            "acceptance_deadline": "2026-03-09",
            "company_name": "Acme Technologies Pvt. Ltd.",
            "ctc_amount": "10000",
            "department": "test",
            "employment_type": "Full-time",
            "offer_date": "2026-03-09",
            "probation_months": "3",
            "reporting_manager": "test",
            "role_title": "test",
            "signatory": {
                "name": "Priya Sharma",
                "title": "Head of Human Resources",
                "email": "priya.sharma@acmetech.com",
                "phone": "+91 98765 43210"
            },
            "start_date": "",
            "weekly_off": ["Saturday", "Sunday"],
            "work_days": "5",
            "work_hours": "8",
            "work_location": "test",
            "work_model": "Onsite",
            "work_timing": "9:00 AM - 6:00 PM"
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # Verify signatory details were passed correctly in the prompt (mock call)
        args, kwargs = mock_generate.call_args
        prompt = args[2]
        self.assertIn("Signatory Name: Priya Sharma", prompt)
        self.assertIn("Signatory Title: Head of Human Resources", prompt)
        self.assertIn("Weekly Off: **Saturday, Sunday**", prompt)

class LetterSettingsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="Test Company")
        self.user = Account.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="password123",
            company=self.company
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('letter-settings')

    def test_get_letter_settings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['signatory_name'], None) # Default

    def test_patch_letter_settings(self):
        data = {
            "signatory_name": "Priya Sharma",
            "signatory_title": "Head of Human Resources",
            "header_tagline": "Custom tagline"
        }
        response = self.client.patch(self.url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['signatory_name'], "Priya Sharma")
        
        # Verify persistence
        settings = LetterSettings.objects.get(company=self.company)
        self.assertEqual(settings.signatory_name, "Priya Sharma")
        self.assertEqual(settings.header_tagline, "Custom tagline")
