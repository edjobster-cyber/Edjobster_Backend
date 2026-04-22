import os
import django
from unittest.mock import MagicMock, patch, mock_open
import json

# Setup Django before any model imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edjobster.settings')
django.setup()

# 1. Mock the decorator BEFORE importing the modules that use it
def mock_decorator(usage_codes):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Patch the decorator in settings.decorators
with patch('settings.decorators.handle_career_site_ai_credits', side_effect=mock_decorator):
    # Now we can safely import the modules
    import unittest
    from candidates.candidate_evaluation import generate_rjms
    from candidates.assessmentchacke import check_assessment, AIScoringService

class TestCandidateEvaluation(unittest.TestCase):

    def setUp(self):
        self.resume_text = "Experienced Software Engineer with Python skills."
        self.assessment_data = json.dumps({"q1": "Python skills", "score": 85})
        self.job_id = 1
        self.company = "TestCompany"
        self.sms = 85.0

    @patch('candidates.candidate_evaluation.Job.objects.filter')
    @patch('candidates.candidate_evaluation.CandidateEvaluationCriteria.objects.get')
    @patch('candidates.candidate_evaluation.client.chat.completions.create')
    def test_generate_rjms_success(self, mock_openai, mock_criteria, mock_job_filter):
        # Mock Job
        mock_job = MagicMock()
        mock_job.dynamic_job_data = json.dumps({"title": "Software Engineer"})
        mock_job_filter.return_value.only.return_value.first.return_value = mock_job

        # Mock Criteria
        mock_crit = MagicMock()
        mock_crit.prompt = {"python": 50, "django": 50}
        mock_criteria.return_value = mock_crit

        # Mock OpenAI Response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "sections": {"python": {"score": 90, "explanation": ["Good python"]}},
            "rjms": 90,
            "sms": 85,
            "variance": 5,
            "consistency": "Consistent"
        })
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_openai.return_value = mock_response

        # Call function
        result = generate_rjms(self.resume_text, self.assessment_data, self.job_id, self.company, self.sms)

        # Assertions
        self.assertEqual(result['rjms'], 90)
        self.assertEqual(result['consistency'], 'Consistent')
        mock_openai.assert_called_once()

    @patch('candidates.candidate_evaluation.Job.objects.filter')
    def test_generate_rjms_job_not_found(self, mock_job_filter):
        mock_job_filter.return_value.only.return_value.first.return_value = None
        result = generate_rjms(self.resume_text, self.assessment_data, self.job_id, self.company, self.sms)
        self.assertEqual(result, {"error": "Job not found"})

class TestAssessmentCheck(unittest.TestCase):

    def setUp(self):
        self.client_assessment = [
            {
                "id": 1,
                "type": "MULTIPLE_CHOICE_SINGLE",
                "question": "What is Python?",
                "options": [{"text": "Language", "points": 10}, {"text": "Snake", "points": 0}],
                "max_points": 10,
                "scoring_config": {"weightage": 50}
            },
            {
                "id": 2,
                "type": "MULTIPLE_CHOICE_MULTI",
                "question": "Choose tools",
                "options": [{"text": "Git", "points": 5}, {"text": "Docker", "points": 5}],
                "max_points": 10,
                "scoring_config": {"weightage": 50}
            }
        ]
        self.user_answers = {
            "data": {
                "questions": [
                    {"id": 1, "candidateAnswer": "Language"},
                    {"id": 2, "candidateAnswer": ["Git", "Docker"]}
                ]
            }
        }

    def test_check_assessment_success(self):
        results = check_assessment(self.user_answers, self.client_assessment, company=self.company, job_id=self.job_id)
        
        # We expect 2 question results + 1 summary result
        self.assertEqual(len(results), 3)
        
        # Check first question (MCQ Single)
        self.assertEqual(results[0]['points_earned'], 10)
        self.assertEqual(results[0]['status'], "✅ Correct")
        
        # Check second question (MCQ Multi)
        self.assertEqual(results[1]['points_earned'], 10)
        
        # Check summary
        summary = results[-1]
        self.assertEqual(summary['status'], "SUMMARY")
        self.assertEqual(summary['total_points'], 20)
        self.assertEqual(summary['weighted_percentage'], 100.0)

    def test_check_assessment_knockout(self):
        # Add a knockout question
        self.client_assessment[0]['scoring_config']['knockout'] = True
        self.user_answers['data']['questions'][0]['candidateAnswer'] = "Snake"
        
        results = check_assessment(self.user_answers, self.client_assessment, company=self.company, job_id=self.job_id)
        
        self.assertEqual(results[0]['status'], "🚫 Knockout")
        self.assertTrue(results[-1]['disqualified'])

    @patch('candidates.assessmentchacke.AIScoringService.score_open_ended')
    def test_check_assessment_open_ended(self, mock_score):
        open_ended_q = {
            "id": 3,
            "type": "OPEN_ENDED",
            "question": "Describe experience",
            "max_points": 10,
            "scoring_config": {"weightage": 10, "keywords": ["python"]}
        }
        self.client_assessment.append(open_ended_q)
        self.user_answers['data']['questions'].append({"id": 3, "candidateAnswer": "I use python."})
        
        mock_score.return_value = {"points": 8.0, "feedback": "Good job"}
        
        results = check_assessment(self.user_answers, self.client_assessment, company=self.company, job_id=self.job_id)
        
        self.assertEqual(results[2]['points_earned'], 8.0)
        self.assertEqual(results[2]['status'], "✅ Good")

if __name__ == '__main__':
    unittest.main()
