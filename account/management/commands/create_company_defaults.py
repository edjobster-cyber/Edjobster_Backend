from django.core.management.base import BaseCommand
from account.models import Company
from settings.models import Pipeline, Module, Webform, CandidateEvaluationCriteria


class Command(BaseCommand):
    help = 'Create default pipeline, modules, webforms and evaluation criteria for existing companies'

    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        created_count = 0

        for company in companies:
            created = self.create_defaults_for_company(company)
            if created:
                created_count += 1
                self.stdout.write(f"Created defaults for company: {company.name} (ID: {company.id})")

        self.stdout.write(self.style.SUCCESS(f'Successfully created defaults for {created_count} companies'))

    def create_defaults_for_company(self, company):
        """Create default data for a company if not exists"""
        created_any = False

        # Create Default Pipeline if not exists
        if not Pipeline.objects.filter(company=company, name="Default Pipeline").exists():
            pipeline = Pipeline()
            pipeline.company = company
            pipeline.name = "Default Pipeline"
            pipeline.save()
            created_any = True

        # Create Candidates Module if not exists
        if not Module.objects.filter(company=company, module_type='candidate').exists():
            webform = Module()
            webform.company = company
            webform.name = "Candidates"
            webform.module_type = 'candidate'
            webform.form = [{"id": 1743743713455, "name": "Personal Details", "label": "Personal Details", "fields": [{"id": 1743743715923, "name": "first_name", "type": "Single Line", "label": "First Name", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Name"}, {"id": 1743743718492, "name": "middle_name", "type": "Single Line", "label": "Middle Name", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Name"}, {"id": 1743744177852, "name": "last_name", "type": "Single Line", "label": "Last Name", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Name"}, {"id": 1743744213605, "name": "email", "type": "Email", "label": "Email ID", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Mail"}, {"id": 1743744215190, "name": "mobile", "type": "Phone", "label": "Mobile", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Phone number"}, {"id": 1744106414639, "name": "alternate_mobile", "type": "Phone", "label": "Alternate Mobile", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Alternate Phone number"}, {"id": 1743744221278, "name": "date_of_birth", "type": "Date", "label": "Date Of Birth", "options": [], "isdelete": False, "required": True, "placeholder": "Enter DOB"}, {"id": 1743744221279, "name": "age", "type": "Number", "label": "Age", "options": [], "isdelete": False, "required": False, "placeholder": "Enter Age"}, {"id": 1743744221280, "name": "gender", "type": "Pick List", "label": "Gender", "options": ["Male", "Female", "Other"], "isdelete": False, "required": True, "placeholder": "Select Gender"}, {"id": 1743744221281, "name": "marital_status", "type": "Pick List", "label": "Marital Status", "options": ["Single", "Married", "Divorced", "Widow"], "isdelete": True, "required": True, "placeholder": "Select Marital Status"}]}, {"id": 1743743713965, "name": "Professional Details", "label": "Professional Details", "fields": [{"id": 1743744234567, "name": "highest_qualification", "type": "Pick List", "label": "Highest Qualification", "options": ["High School", "Diploma", "Bachelor's Degree", "Master's Degree", "PhD"], "isdelete": False, "required": True, "placeholder": "Select Qualification"}, {"id": 1743744245678, "name": "experience", "type": "Number", "label": "Experience (Years)", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Experience"}, {"id": 1743744256789, "name": "current_ctc", "type": "Number", "label": "Current CTC", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Current CTC"}, {"id": 1743744267890, "name": "expected_ctc", "type": "Number", "label": "Expected CTC", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Expected CTC"}, {"id": 1743744278901, "name": "notice_period", "type": "Pick List", "label": "Notice Period", "options": ["Immediate", "15 Days", "30 Days", "60 Days", "90 Days"], "isdelete": False, "required": True, "placeholder": "Select Notice Period"}, {"id": 1743744289012, "name": "current_location", "type": "Single Line", "label": "Current Location", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Location"}, {"id": 1743744290123, "name": "preferred_location", "type": "Single Line", "label": "Preferred Location", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Preferred Location"}]}]
            webform.save()
            created_any = True

        # Create Job Openings Module if not exists
        if not Module.objects.filter(company=company, module_type='job_opening').exists():
            webform = Module()
            webform.company = company
            webform.name = "Job Openings"
            webform.module_type = 'job_opening'
            webform.form = [
                {
                    "id": 1744786434889,
                    "name": "Create Job",
                    'label': "Create Job",
                    "fields": [
                        {
                            "id": 1744786440082,
                            "name": "title",
                            "type": "Single Line",
                            "label": "Job Title",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Enter Job TItle"
                        },
                        {
                            "id": 1744786618271,
                            "name": "vacancies",
                            "type": "Number",
                            "label": "Number of Vacancies",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Enter Number of Vacancies"
                        },
                        {
                            "id": 1744786726119,
                            "name": "department",
                            "type": "Pick List",
                            "label": "Department",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Enter Department"
                        },
                        {
                            "id": 1744803220732,
                            "name": "owner",
                            "type": "Pick List",
                            "label": "Owner",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Select Owner"
                        },
                        {
                            "id": 1744803317300,
                            "name": "members",
                            "type": "Multi Select",
                            "label": "Team Member",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Select Team Member"
                        },
                        {
                            "id": 1744786783795,
                            "name": "type",
                            "type": "Pick List",
                            "label": "Type",
                            "options": [
                                "Full Time",
                                "Part Time"
                            ],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Select Tyep"
                        },
                        {
                            "id": 1744786843652,
                            "name": "nature",
                            "type": "Pick List",
                            "label": "Job Nature",
                            "options": [
                                "Remote",
                                "Physical"
                            ],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Select Job Nature"
                        },
                        {
                            "id": 1744787101161,
                            "name": "educations",
                            "type": "Pick List",
                            "label": "Education",
                            "options": [
                                "HighSchool",
                                "JuniorCollege",
                                "Bachelors",
                                "Masters"
                            ],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Select Education"
                        },
                        {
                            "id": 1744787598403,
                            "name": "exp_min",
                            "type": "Number",
                            "label": "Work Ex. min. (years)",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Enter Work Ex"
                        },
                        {
                            "id": 1744787645294,
                            "name": "exp_max",
                            "type": "Number",
                            "label": "Work Ex. max. (years)",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Enter Max Work"
                        },
                        {
                            "id": 1744787720348,
                            "name": "salary_min",
                            "type": "Number",
                            "label": "Salary (Minimum)",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Enter Salary Minimum"
                        },
                        {
                            "id": 1744787769508,
                            "name": "salary_max",
                            "type": "Number",
                            "label": "Salary (Maximum)",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Enter Salary Maximum"
                        },
                        {
                            "id": 1744787803786,
                            "name": "currency",
                            "type": "Pick List",
                            "label": "Currency",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Currency"
                        },
                        {
                            "id": 1744787841146,
                            "name": "salary_type",
                            "type": "Pick List",
                            "label": "Salary Type",
                            "options": [
                                "Daily",
                                "Weekly",
                                "Monthly",
                                "Yearly"
                            ],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Salary Type"
                        },
                        {
                            "id": 1744787899154,
                            "name": "pipeline",
                            "type": "Pick List",
                            "label": "Pipeline",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Pipeline"
                        },
                        {
                            "id": 1744787404529,
                            "name": "speciality",
                            "type": "Tags",
                            "label": "Key Skills",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Select Speciality"
                        },
                    ]
                },
                {
                    "id": 1752475274569,
                    "name": "Address Information",
                    "label": "Address Information",
                    "fields": [
                        {
                            "id": 1752239452649,
                            "name": "country",
                            "type": "Pick List",
                            "label": "Country",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "isEditable": True,
                            "placeholder": "Country"
                        },
                        {
                            "id": 1752239455534,
                            "name": "state",
                            "type": "Pick List",
                            "label": "State",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "isEditable": True,
                            "placeholder": "State"
                        },
                        {
                            "id": 1752239459823,
                            "name": "city",
                            "type": "Pick List",
                            "label": "City",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "isEditable": True,
                            "placeholder": "City"
                        },
                        {
                            "id": 1752475364328,
                            "name": "pincode",
                            "type": "Number",
                            "label": "Pincode",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "isEditable": True,
                            "placeholder": "Pincode"
                        }
                    ]
                },
                {
                    "id": 1752475312081,
                    "name": "Description Information",
                    "label": "Description Information",
                    "fields": [
                        {
                            "id": 1746180241835,
                            "name": "description",
                            "type": "Description",
                            "label": "Job Description",
                            "options": [],
                            "isdelete": False,
                            "required": True,
                            "placeholder": "Job Description"
                        }
                    ]
                }
            ]
            webform.save()
            created_any = True

        # Create Interviews Module if not exists
        if not Module.objects.filter(company=company, module_type='interview').exists():
            webform = Module()
            webform.company = company
            webform.name = "Interviews"
            webform.module_type = 'interview'
            webform.form = [
                {
                    "id": 1760336752768,
                    "name": "basic_info",
                    "label": "Basic Info",
                    "fields": [
                        {
                            "id": 1760336777385,
                            "name": "interview_title",
                            "type": "Single Line",
                            "label": "Interview Title",
                            "options": [],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Interview Title"
                        },
                        {
                            "id": 1760348939874,
                            "name": "job",
                            "type": "Pick List",
                            "label": "Select Job",
                            "options": [],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Select Job"
                        },
                        {
                            "id": 1760336817918,
                            "name": "candidate",
                            "type": "Multi Select",
                            "label": "Select Candidate(s)",
                            "options": [],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Select Candidate(s)"
                        },
                        {
                            "id": 1760336909538,
                            "name": "interview_type",
                            "type": "Pick List",
                            "label": "Interview Type",
                            "options": ["Online", "Offline", "Phone", "Panel"],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Interview Type"
                        },
                        {
                            "id": 1760337120170,
                            "name": "mode_of_interview",
                            "type": "Pick List",
                            "label": "Mode of Interview",
                            "options": ["Zoom", "Microsoft Teams", "Google Meet", "In-person", "Other"],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Mode of Interview"
                        },
                        {
                            "id": 1760508432505,
                            "name": "interview_link",
                            "type": "Single Line",
                            "label": "Interview Link",
                            "options": [],
                            "required": False,
                            "isEditable": True,
                            "isdelete": False,
                            "placeholder": "Interview Link"
                        },
                        {
                            "id": 1760508455534,
                            "name": "interview_location",
                            "type": "Pick List",
                            "label": "Interview Location",
                            "options": [],
                            "required": False,
                            "isEditable": True,
                            "isdelete": False,
                            "placeholder": "Interview Location"
                        },
                        {
                            "id": 1760337241155,
                            "name": "interview_round",
                            "type": "Pick List",
                            "label": "Interview Round",
                            "options": ["Screening", "Technical", "Managerial", "HR", "Final"],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Interview Round"
                        }
                    ],
                    "isDelete": False
                },
                {
                    "id": 1760337321714,
                    "name": "interviewers",
                    "label": "Interviewer(s)",
                    "fields": [
                        {
                            "id": 1760337378723,
                            "name": "interviewers",
                            "type": "Multi Select",
                            "label": "Select Interviewer(s) from Platform",
                            "options": [],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Select Interviewer(s) from Platform"
                        }
                    ],
                    "isDelete": False
                },
                {
                    "id": 1760337400067,
                    "name": "schedule",
                    "label": "Schedule",
                    "fields": [
                        {
                            "id": 1760337455757,
                            "name": "date",
                            "type": "Date",
                            "label": "Date",
                            "options": [],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Date"
                        },
                        {
                            "id": 1760338014026,
                            "name": "time",
                            "type": "Time",
                            "label": "Time",
                            "options": [],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Time"
                        },
                        {
                            "id": 1760337556807,
                            "name": "duration",
                            "type": "Pick List",
                            "label": "Duration",
                            "options": [
                                "15 minutes",
                                "30 minutes",
                                "45 minutes",
                                "60 minutes",
                                "90 minutes",
                                "120 minutes"
                            ],
                            "required": False,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Duration"
                        },
                        {
                            "id": 1760337519361,
                            "name": "time_zone",
                            "type": "Pick List",
                            "label": "Time Zone",
                            "options": [],
                            "required": True,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Time Zone"
                        }
                    ],
                    "isDelete": False
                },
                {
                    "id": 1760337691381,
                    "name": "additional_information",
                    "label": "Additional Information",
                    "fields": [
                        {
                            "id": 1760337725409,
                            "name": "notes_for_interviewer_private",
                            "type": "Multi-Line",
                            "label": "Notes for Interviewer (Private)",
                            "options": [],
                            "required": False,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Notes for Interviewer (Private)"
                        },
                        {
                            "id": 1760337744391,
                            "name": "notes_for_candidate_public",
                            "type": "Multi-Line",
                            "label": "Notes for Candidate (Public)",
                            "options": [],
                            "required": False,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Notes for Candidate (Public)"
                        }
                    ],
                    "isDelete": False
                },
                {
                    "id": 1760337772999,
                    "name": "Reminder Settings",
                    "label": "Reminder Settings",
                    "fields": [
                        {
                            "id": 1760338334493,
                            "name": "select_reminders",
                            "type": "Multiple Radio Select",
                            "label": "Select Reminders",
                            "options": ["24 hours before", "1 hour before", "15 minutes before"],
                            "required": False,
                            "isEditable": False,
                            "isdelete": False,
                            "placeholder": "Select Reminders"
                        }
                    ],
                    "isDelete": False
                }
            ]
            webform.save()
            created_any = True

        # Create Assessment Module if not exists
        if not Module.objects.filter(company=company, module_type='assessment').exists():
            webform = Module()
            webform.company = company
            webform.name = "Assessment"
            webform.module_type = 'assessment'
            webform.form = [{"id": 1744804418450, "name": "Assessment", "label": "Assessment Information", "fields": []}]
            webform.save()
            created_any = True

        # Create Default Webform if not exists
        if not Webform.objects.filter(company=company).exists():
            default_webform = Webform()
            default_webform.company = company
            default_webform.name = "Default Webform"
            default_webform.form = [{"id": 1743743713455, "name": "Personal Details", "label": "Personal Details", "fields": [{"id": 1772538662026, "name": "first_name", "type": "Single Line", "label": "First Name", "options": [], "required": True, "placeholder": "Enter Name"}, {"id": 1772538665369, "name": "middle_name", "type": "Single Line", "label": "Middle Name", "options": [], "required": False, "placeholder": "Enter Name"}, {"id": 1772538665730, "name": "last_name", "type": "Single Line", "label": "Last Name", "options": [], "required": True, "placeholder": "Enter Name"}, {"id": 1772538666210, "name": "email", "type": "Email", "label": "Email ID", "options": [], "required": True, "placeholder": "Enter Mail"}, {"id": 1772538668959, "name": "mobile", "type": "Phone", "label": "Mobile", "options": [], "required": True, "placeholder": "Enter Phone number"}, {"id": 1772538669276, "name": "alternate_mobile", "type": "Phone", "label": "Alternate Mobile", "options": [], "required": False, "placeholder": "Enter Alternate Phone number"}, {"id": 1772538669620, "name": "date_of_birth", "type": "Date", "label": "Date Of Birth", "options": [], "required": True, "placeholder": "Enter DOB"}, {"id": 1772538670751, "name": "age", "type": "Number", "label": "Age", "options": [], "required": False, "placeholder": "Enter Age"}]}, {"id": 1743743713965, "name": "Professional Details", "label": "Professional Details", "fields": [{"id": 1772538677642, "name": "exp_years", "type": "Number", "label": "Experience in years", "options": [], "required": False, "placeholder": "Enter Year Of Experience"}, {"id": 1772538677958, "name": "highest_qualification", "type": "Pick List", "label": "Highest Qualification held", "options": ["Secondary School", "High School", "Diploma", "Post Graduate Diploma"], "required": True, "placeholder": "Select Highest Qualification"}, {"id": 1772538678273, "name": "current_employer", "type": "Single Line", "label": "Current Employer", "options": [], "required": False, "placeholder": "Enter Company Name"}, {"id": 1772538678600, "name": "current_designation", "type": "Single Line", "label": "Current Designation", "options": [], "required": False, "placeholder": "Enter Designation"}]}]
            default_webform.save()
            created_any = True

        # Create Default Evaluation Criteria if not exists
        if not CandidateEvaluationCriteria.objects.filter(company=company).exists():
            default_prompt = {
                "core_skills": 35,
                "relevant_experience": 30,
                "tools_and_technologies": 15,
                "responsibilities": 10,
                "education_certifications": 10
            }
            CandidateEvaluationCriteria.objects.create(
                company=company,
                prompt=default_prompt
            )
            created_any = True

        return created_any
