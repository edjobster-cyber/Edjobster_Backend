import json
from django.core.management.base import BaseCommand
from settings.models import Plan, BillingCycle, PlanPricing, Feature, PlanFeatureCredit, FeatureUsage

class Command(BaseCommand):
    help = 'Load initial data for plans, billing cycles, pricing, features, and credits'

    def handle(self, *args, **kwargs):
        data = {
    "plan": [
        {
            "id": 1,
            "name": "14 Day FREE Trial",
            "description": "14 days free trial with basic features",
            "is_active": True
        },
        {
            "id": 2,
            "name": "Starter",
            "description": "Starter plan with essential features",
            "is_active": True
        },
        {
            "id": 3,
            "name": "Growth",
            "description": "Growth plan with advanced features",
            "is_active": True
        },
        {
            "id": 4,
            "name": "Pro",
            "description": "Professional plan with all features",
            "is_active": True
        }
    ],
    "billingCycle": [
        {
            "id": 1,
            "name": "Monthly",
            "duration_in_months": 1.0
        },
        {
            "id": 2,
            "name": "Half-Yearly",
            "duration_in_months": 6.0
        },
        {
            "id": 3,
            "name": "Annually",
            "duration_in_months": 12.0
        },
        {
            "id": 4,
            "name": "14 Days",
            "duration_in_months": 0.460273
        }
    ],
    "planPricing": [
        {
            "id": 1,
            "plan_id": 2,
            "billing_cycle_id": 1,
            "price": 3999.0,
            "offer": None
        },
        {
            "id": 2,
            "plan_id": 2,
            "billing_cycle_id": 2,
            "price": 21999.0,
            "offer": None
        },
        {
            "id": 3,
            "plan_id": 2,
            "billing_cycle_id": 3,
            "price": 39999.0,
            "offer": None
        },
        {
            "id": 4,
            "plan_id": 3,
            "billing_cycle_id": 1,
            "price": 6999.0,
            "offer": None
        },
        {
            "id": 5,
            "plan_id": 3,
            "billing_cycle_id": 2,
            "price": 39999.0,
            "offer": None
        },
        {
            "id": 6,
            "plan_id": 3,
            "billing_cycle_id": 3,
            "price": 69999.0,
            "offer": None
        },
        {
            "id": 7,
            "plan_id": 4,
            "billing_cycle_id": 1,
            "price": 9999.0,
            "offer": None
        },
        {
            "id": 8,
            "plan_id": 4,
            "billing_cycle_id": 2,
            "price": 54999.0,
            "offer": None
        },
        {
            "id": 9,
            "plan_id": 4,
            "billing_cycle_id": 3,
            "price": 99999.0,
            "offer": None
        },
        {
            "id": 10,
            "plan_id": 1,
            "billing_cycle_id": 4,
            "price": 0.0,
            "offer": None
        }
    ],
    "feature": [
        {
            "id": 1,
            "code": "Job_modules",
            "name": "Job",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 2,
            "code": "candidate_modules",
            "name": "Candidate",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 3,
            "code": "interview_modules",
            "name": "Interview",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 4,
            "code": "notes",
            "name": "Notes",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 5,
            "code": "tasks",
            "name": "Tasks",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 6,
            "code": "events",
            "name": "events",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 7,
            "code": "JOB_POST",
            "name": "Job Post",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        },
        {
            "id": 8,
            "code": "AI_CREDITS",
            "name": "AI Credits",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        },
        {
            "id": 9,
            "code": "Resume_Parcing_using_AI",
            "name": "Resume Parcing (using AI)",
            "description": "",
            "isdayli": True,
            "iscredit": False,
            "iswithoutcredit": False
        },
        {
            "id": 10,
            "code": "Candidate_Evaluation",
            "name": "Candidate Evaluation",
            "description": "",
            "isdayli": True,
            "iscredit": False,
            "iswithoutcredit": False
        },
        {
            "id": 11,
            "code": "Employer_Branding",
            "name": "Employer Branding",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 12,
            "code": "Career_Site",
            "name": "Career Site",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 13,
            "code": "Free_Job_Boards_Integration",
            "name": "Free Job Boards Integratio",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 14,
            "code": "Jobs_on_Google_Search",
            "name": "Jobs on Google Search",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 15,
            "code": "Interview_feedback_form",
            "name": "Interview feedback form",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 16,
            "code": "Web_Forms",
            "name": "Forms for candidates",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        },
        {
            "id": 17,
            "code": "auto_response_rules",
            "name": "Auto response rules",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 18,
            "code": "simple_search",
            "name": "Simple search",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 19,
            "code": "unsubscribe_link",
            "name": "Unsubscribe link",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 20,
            "code": "standard_reports",
            "name": "Standard reports",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 21,
            "code": "Custom_Fields",
            "name": "Custom Fields",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        },
        {
            "id": 22,
            "code": "company_user",
            "name": "Profiles",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        },
        {
            "id": 23,
            "code": "mail",
            "name": "Mail",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 24,
            "code": "Email_SMTP_IMPS",
            "name": "Email SMTP/IMPS",
            "description": "",
            "isdayli": False,
            "iscredit": False,
            "iswithoutcredit": True
        },
        {
            "id": 25,
            "code": "file_storage_per_organization",
            "name": "File Storage per organization",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        },
        {
            "id": 26,
            "code": "Email_Templates",
            "name": "Email Templates",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        },
        {
            "id": 27,
            "code": "total_records",
            "name": "Data Storage (records in all modules)",
            "description": "",
            "isdayli": False,
            "iscredit": True,
            "iswithoutcredit": False
        }
    ],
    "planFeatureCredit": [
        {"id": 1, "plan_id": 1, "feature_id": 1, "credit_limit": 0},
        {"id": 2, "plan_id": 1, "feature_id": 2, "credit_limit": 0},
        {"id": 3, "plan_id": 1, "feature_id": 3, "credit_limit": 0},
        {"id": 4, "plan_id": 1, "feature_id": 4, "credit_limit": 0},
        {"id": 6, "plan_id": 1, "feature_id": 5, "credit_limit": 0},
        {"id": 7, "plan_id": 1, "feature_id": 6, "credit_limit": 0},
        {"id": 8, "plan_id": 1, "feature_id": 7, "credit_limit": 1},
        {"id": 9, "plan_id": 1, "feature_id": 8, "credit_limit": 10},
        {"id": 10, "plan_id": 1, "feature_id": 9, "credit_limit": 1},
        {"id": 11, "plan_id": 1, "feature_id": 10, "credit_limit": 1},
        {"id": 12, "plan_id": 1, "feature_id": 13, "credit_limit": 0},
        {"id": 13, "plan_id": 1, "feature_id": 14, "credit_limit": 0},
        {"id": 14, "plan_id": 1, "feature_id": 16, "credit_limit": 1},
        {"id": 15, "plan_id": 1, "feature_id": 17, "credit_limit": 0},
        {"id": 16, "plan_id": 1, "feature_id": 18, "credit_limit": 0},
        {"id": 17, "plan_id": 1, "feature_id": 26, "credit_limit": 1},
        {"id": 18, "plan_id": 1, "feature_id": 20, "credit_limit": 0},
        {"id": 19, "plan_id": 1, "feature_id": 22, "credit_limit": 1},
        {"id": 20, "plan_id": 1, "feature_id": 23, "credit_limit": 0},
        {"id": 21, "plan_id": 1, "feature_id": 24, "credit_limit": 0},
        {"id": 22, "plan_id": 1, "feature_id": 25, "credit_limit": 256},
        {"id": 23, "plan_id": 2, "feature_id": 1, "credit_limit": 0},
        {"id": 24, "plan_id": 2, "feature_id": 2, "credit_limit": 0},
        {"id": 25, "plan_id": 2, "feature_id": 3, "credit_limit": 0},
        {"id": 26, "plan_id": 2, "feature_id": 4, "credit_limit": 0},
        {"id": 27, "plan_id": 2, "feature_id": 5, "credit_limit": 0},
        {"id": 28, "plan_id": 2, "feature_id": 6, "credit_limit": 0},
        {"id": 29, "plan_id": 2, "feature_id": 7, "credit_limit": 20},
        {"id": 30, "plan_id": 2, "feature_id": 8, "credit_limit": 20},
        {"id": 31, "plan_id": 2, "feature_id": 9, "credit_limit": 300},
        {"id": 32, "plan_id": 2, "feature_id": 10, "credit_limit": 300},
        {"id": 33, "plan_id": 2, "feature_id": 12, "credit_limit": 0},
        {"id": 34, "plan_id": 2, "feature_id": 13, "credit_limit": 0},
        {"id": 35, "plan_id": 2, "feature_id": 14, "credit_limit": 0},
        {"id": 36, "plan_id": 2, "feature_id": 16, "credit_limit": 3},
        {"id": 37, "plan_id": 2, "feature_id": 18, "credit_limit": 0},
        {"id": 38, "plan_id": 2, "feature_id": 26, "credit_limit": 5},
        {"id": 39, "plan_id": 2, "feature_id": 20, "credit_limit": 0},
        {"id": 40, "plan_id": 2, "feature_id": 21, "credit_limit": 10},
        {"id": 41, "plan_id": 2, "feature_id": 22, "credit_limit": 4},
        {"id": 42, "plan_id": 2, "feature_id": 23, "credit_limit": 0},
        {"id": 43, "plan_id": 2, "feature_id": 24, "credit_limit": 0},
        {"id": 44, "plan_id": 2, "feature_id": 25, "credit_limit": 1064},
        {"id": 45, "plan_id": 3, "feature_id": 1, "credit_limit": 0},
        {"id": 46, "plan_id": 3, "feature_id": 2, "credit_limit": 0},
        {"id": 47, "plan_id": 3, "feature_id": 3, "credit_limit": 0},
        {"id": 48, "plan_id": 3, "feature_id": 4, "credit_limit": 0},
        {"id": 49, "plan_id": 3, "feature_id": 5, "credit_limit": 0},
        {"id": 50, "plan_id": 3, "feature_id": 6, "credit_limit": 0},
        {"id": 51, "plan_id": 3, "feature_id": 7, "credit_limit": 80},
        {"id": 52, "plan_id": 3, "feature_id": 8, "credit_limit": 80},
        {"id": 53, "plan_id": 3, "feature_id": 9, "credit_limit": 800},
        {"id": 54, "plan_id": 3, "feature_id": 10, "credit_limit": 800},
        {"id": 55, "plan_id": 3, "feature_id": 12, "credit_limit": 0},
        {"id": 56, "plan_id": 3, "feature_id": 11, "credit_limit": 0},
        {"id": 57, "plan_id": 3, "feature_id": 13, "credit_limit": 0},
        {"id": 58, "plan_id": 3, "feature_id": 14, "credit_limit": 0},
        {"id": 59, "plan_id": 3, "feature_id": 15, "credit_limit": 0},
        {"id": 60, "plan_id": 3, "feature_id": 16, "credit_limit": 8},
        {"id": 61, "plan_id": 3, "feature_id": 17, "credit_limit": 0},
        {"id": 62, "plan_id": 3, "feature_id": 18, "credit_limit": 0},
        {"id": 63, "plan_id": 3, "feature_id": 26, "credit_limit": 20},
        {"id": 64, "plan_id": 3, "feature_id": 19, "credit_limit": 0},
        {"id": 65, "plan_id": 3, "feature_id": 20, "credit_limit": 0},
        {"id": 66, "plan_id": 3, "feature_id": 21, "credit_limit": 10},
        {"id": 67, "plan_id": 3, "feature_id": 22, "credit_limit": 4},
        {"id": 68, "plan_id": 3, "feature_id": 23, "credit_limit": 0},
        {"id": 69, "plan_id": 3, "feature_id": 24, "credit_limit": 0},
        {"id": 70, "plan_id": 3, "feature_id": 25, "credit_limit": 2128},
        {"id": 71, "plan_id": 4, "feature_id": 1, "credit_limit": 0},
        {"id": 72, "plan_id": 4, "feature_id": 2, "credit_limit": 0},
        {"id": 73, "plan_id": 4, "feature_id": 3, "credit_limit": 0},
        {"id": 74, "plan_id": 4, "feature_id": 4, "credit_limit": 0},
        {"id": 75, "plan_id": 4, "feature_id": 5, "credit_limit": 0},
        {"id": 76, "plan_id": 4, "feature_id": 6, "credit_limit": 0},
        {"id": 77, "plan_id": 4, "feature_id": 7, "credit_limit": 250},
        {"id": 78, "plan_id": 4, "feature_id": 8, "credit_limit": 250},
        {"id": 79, "plan_id": 4, "feature_id": 9, "credit_limit": 2500},
        {"id": 80, "plan_id": 4, "feature_id": 10, "credit_limit": 2500},
        {"id": 81, "plan_id": 4, "feature_id": 12, "credit_limit": 0},
        {"id": 82, "plan_id": 4, "feature_id": 11, "credit_limit": 0},
        {"id": 83, "plan_id": 4, "feature_id": 13, "credit_limit": 0},
        {"id": 84, "plan_id": 4, "feature_id": 14, "credit_limit": 0},
        {"id": 85, "plan_id": 4, "feature_id": 15, "credit_limit": 0},
        {"id": 86, "plan_id": 4, "feature_id": 16, "credit_limit": 20},
        {"id": 87, "plan_id": 4, "feature_id": 17, "credit_limit": 0},
        {"id": 88, "plan_id": 4, "feature_id": 18, "credit_limit": 0},
        {"id": 89, "plan_id": 4, "feature_id": 19, "credit_limit": 0},
        {"id": 90, "plan_id": 4, "feature_id": 20, "credit_limit": 0},
        {"id": 91, "plan_id": 4, "feature_id": 21, "credit_limit": 30},
        {"id": 92, "plan_id": 4, "feature_id": 22, "credit_limit": 10},
        {"id": 93, "plan_id": 4, "feature_id": 23, "credit_limit": 0},
        {"id": 94, "plan_id": 4, "feature_id": 24, "credit_limit": 0},
        {"id": 95, "plan_id": 4, "feature_id": 25, "credit_limit": 3192},
        {"id": 96, "plan_id": 1, "feature_id": 27, "credit_limit": 5000},
        {"id": 97, "plan_id": 2, "feature_id": 27, "credit_limit": 1000000},
        {"id": 98, "plan_id": 3, "feature_id": 27, "credit_limit": 1000000},
        {"id": 99, "plan_id": 4, "feature_id": 27, "credit_limit": 500000}
    ],
    "featureUsage": [
        {
            "id": 1,
            "code": "Generate_Job_Description",
            "name": "Generate Job Description",
            "feature_id": 8,
            "used_credit": 1
        },
        {
            "id": 2,
            "code": "Generate_Assessment_Questionaire",
            "name": "Generate Assessment Questionaire",
            "feature_id": 8,
            "used_credit": 2
        },
        {
            "id": 3,
            "code": "Resume_Parcing_using_AI",
            "name": "Resume Parcing (using AI)",
            "feature_id": 8,
            "used_credit": 3
        },
        {
            "id": 4,
            "code": "AI_Outreach_Email_Follow_ups",
            "name": "AI Outreach(Email) & Follow-ups",
            "feature_id": 8,
            "used_credit": 1
        },
        {
            "id": 5,
            "code": "Rjms",
            "name": "RJMS",
            "feature_id": 8,
            "used_credit": 2
        },
        {
            "id": 6,
            "code": "assessment_check",
            "name": "Assessment Chake",
            "feature_id": 8,
            "used_credit": 2
        }
    ]
}

        for item in data.get("plan", []):
            obj, created = Plan.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "is_active": item["is_active"],
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Plan {obj.name} updated." if not created else f"Plan {obj.name} created."))

        for item in data.get("billingCycle", []):
            obj, created = BillingCycle.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"],
                    "duration_in_months": item["duration_in_months"]
                }
            )
            self.stdout.write(self.style.SUCCESS(f"BillingCycle {obj.name} updated." if not created else f"BillingCycle {obj.name} created."))

        for item in data.get("planPricing", []):
            obj, created = PlanPricing.objects.update_or_create(
                id=item["id"],
                defaults={
                    "plan_id": item["plan_id"],
                    "billing_cycle_id": item["billing_cycle_id"],
                    "price": item["price"],
                    "offer": item["offer"]
                }
            )
            self.stdout.write(self.style.SUCCESS(f"PlanPricing {obj.id} updated." if not created else f"PlanPricing {obj.id} created."))

        for item in data.get("feature", []):
            obj, created = Feature.objects.update_or_create(
                id=item["id"],
                defaults={
                    "code": item["code"],
                    "name": item["name"],
                    "description": item["description"],
                    "isdayli": item["isdayli"],
                    "iscredit": item["iscredit"],
                    "iswithoutcredit": item["iswithoutcredit"]
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Feature {obj.name} updated." if not created else f"Feature {obj.name} created."))

        for item in data.get("planFeatureCredit", []):
            obj, created = PlanFeatureCredit.objects.update_or_create(
                id=item["id"],
                defaults={
                    "plan_id": item["plan_id"],
                    "feature_id": item["feature_id"],
                    "credit_limit": item["credit_limit"]
                }
            )
            self.stdout.write(self.style.SUCCESS(f"PlanFeatureCredit {obj.id} updated." if not created else f"PlanFeatureCredit {obj.id} created."))

        for item in data.get("featureUsage", []):
            obj, created = FeatureUsage.objects.update_or_create(
                id=item["id"],
                defaults={
                    "code": item["code"],
                    "name": item["name"],
                    "feature_id": item["feature_id"],
                    "used_credit": item["used_credit"]
                }
            )
            self.stdout.write(self.style.SUCCESS(f"FeatureUsage {obj.name} updated." if not created else f"FeatureUsage {obj.name} created."))
