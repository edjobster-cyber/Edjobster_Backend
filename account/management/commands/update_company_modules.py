from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from account.models import Company
from settings.models import Pipeline, Module, Webform, CandidateEvaluationCriteria


class Command(BaseCommand):
    help = 'Update or create module data for all companies. Can update existing modules or add new module types.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing module form data (default: only creates missing)',
        )
        parser.add_argument(
            '--module-type',
            type=str,
            help='Specific module type to update (candidate, job_opening, interview, assessment)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Update only for specific company ID',
        )

    def handle(self, *args, **options):
        update_existing = options['update_existing']
        specific_module = options['module_type']
        dry_run = options['dry_run']
        company_id = options['company_id']

        # Get companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id)
            if not companies.exists():
                raise CommandError(f'Company with ID {company_id} not found')
        else:
            companies = Company.objects.all()

        total_companies = companies.count()
        self.stdout.write(f"Processing {total_companies} companies...")

        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

        for company in companies:
            try:
                with transaction.atomic():
                    result = self.process_company(
                        company,
                        update_existing=update_existing,
                        specific_module=specific_module,
                        dry_run=dry_run
                    )
                    stats['created'] += result.get('created', 0)
                    stats['updated'] += result.get('updated', 0)
                    stats['skipped'] += result.get('skipped', 0)
            except Exception as e:
                stats['errors'] += 1
                self.stderr.write(
                    self.style.ERROR(f"Error processing company {company.name} (ID: {company.id}): {str(e)}")
                )

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("SUMMARY:"))
        self.stdout.write(f"  Companies processed: {total_companies}")
        self.stdout.write(f"  Modules created: {stats['created']}")
        if update_existing:
            self.stdout.write(f"  Modules updated: {stats['updated']}")
        self.stdout.write(f"  Modules skipped: {stats['skipped']}")
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f"  Errors: {stats['errors']}"))

    def process_company(self, company, update_existing=False, specific_module=None, dry_run=False):
        """Process all modules for a single company"""
        results = {'created': 0, 'updated': 0, 'skipped': 0}

        # Define all module types and their form data
        module_definitions = {
            # 'candidate': {
            #     'name': 'Candidates',
            #     'form': self.get_candidate_form()
            # },
            # 'job_opening': {
            #     'name': 'Job Openings',
            #     'form': self.get_job_opening_form()
            # },
            'interview': {
                'name': 'Interviews',
                'form': self.get_interview_form()
            },
            # 'assessment': {
            #     'name': 'Assessment',
            #     'form': self.get_assessment_form()
            # }
        }

        # Filter to specific module if requested
        if specific_module:
            if specific_module not in module_definitions:
                raise CommandError(f"Invalid module type: {specific_module}")
            module_definitions = {specific_module: module_definitions[specific_module]}

        # Process each module type
        for module_type, definition in module_definitions.items():
            existing = Module.objects.filter(company=company, module_type=module_type).first()

            if existing:
                if update_existing:
                    if not dry_run:
                        existing.name = definition['name']
                        existing.form = definition['form']
                        existing.save()
                    results['updated'] += 1
                    self.stdout.write(
                        f"  {'[DRY-RUN] ' if dry_run else ''}Updated {module_type} module for {company.name}"
                    )
                else:
                    results['skipped'] += 1
                    self.stdout.write(
                        f"  Skipped {module_type} module for {company.name} (already exists)"
                    )
            else:
                if not dry_run:
                    Module.objects.create(
                        company=company,
                        module_type=module_type,
                        name=definition['name'],
                        form=definition['form']
                    )
                results['created'] += 1
                self.stdout.write(
                    f"  {'[DRY-RUN] ' if dry_run else ''}Created {module_type} module for {company.name}"
                )

        # Also ensure default pipeline exists
        self.ensure_default_pipeline(company, dry_run)

        # Ensure default evaluation criteria exists
        self.ensure_default_evaluation_criteria(company, dry_run)

        return results

    def ensure_default_pipeline(self, company, dry_run=False):
        """Ensure default pipeline exists for company"""
        if not Pipeline.objects.filter(company=company, name="Default Pipeline").exists():
            if not dry_run:
                Pipeline.objects.create(company=company, name="Default Pipeline")
            self.stdout.write(
                f"  {'[DRY-RUN] ' if dry_run else ''}Created default pipeline for {company.name}"
            )

    def ensure_default_evaluation_criteria(self, company, dry_run=False):
        """Ensure default evaluation criteria exists for company"""
        if not CandidateEvaluationCriteria.objects.filter(company=company).exists():
            if not dry_run:
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
            self.stdout.write(
                f"  {'[DRY-RUN] ' if dry_run else ''}Created default evaluation criteria for {company.name}"
            )

    def get_candidate_form(self):
        """Return candidate module form structure"""
        return [
            {
                "id": 1743743713455,
                "name": "Personal Details",
                "label": "Personal Details",
                "fields": [
                    {"id": 1743743715923, "name": "first_name", "type": "Single Line", "label": "First Name", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Name"},
                    {"id": 1743743718492, "name": "middle_name", "type": "Single Line", "label": "Middle Name", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Name"},
                    {"id": 1743744177852, "name": "last_name", "type": "Single Line", "label": "Last Name", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Name"},
                    {"id": 1743744213605, "name": "email", "type": "Email", "label": "Email ID", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Mail"},
                    {"id": 1743744215190, "name": "mobile", "type": "Phone", "label": "Mobile", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Phone number"},
                    {"id": 1744106414639, "name": "alternate_mobile", "type": "Phone", "label": "Alternate Mobile", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Alternate Phone number"},
                    {"id": 1743744221278, "name": "date_of_birth", "type": "Date", "label": "Date Of Birth", "options": [], "isdelete": False, "required": True, "placeholder": "Enter DOB"},
                    {"id": 1743744221279, "name": "age", "type": "Number", "label": "Age", "options": [], "isdelete": False, "required": False, "placeholder": "Enter Age"},
                    {"id": 1743744221280, "name": "gender", "type": "Pick List", "label": "Gender", "options": ["Male", "Female", "Other"], "isdelete": False, "required": True, "placeholder": "Select Gender"},
                    {"id": 1743744221281, "name": "marital_status", "type": "Pick List", "label": "Marital Status", "options": ["Single", "Married", "Divorced", "Widow"], "isdelete": True, "required": True, "placeholder": "Select Marital Status"}
                ]
            },
            {
                "id": 1743743713965,
                "name": "Professional Details",
                "label": "Professional Details",
                "fields": [
                    {"id": 1743744221282, "name": "exp_years", "type": "Number", "label": "Experience in years", "options": [], "isdelete": False, "required": False, "placeholder": "Enter Year Of Experience"},
                    {"id": 1743744221283, "name": "highest_qualification", "type": "Pick List", "label": "Highest Qualification held", "options": ["Secondary School", "High School", "Diploma", "Post Graduate Diploma"], "isdelete": False, "required": True, "placeholder": "Select Highest Qualification"},
                    {"id": 1743744221284, "name": "current_employer", "type": "Single Line", "label": "Current Employer", "options": [], "isdelete": False, "required": False, "placeholder": "Current Employer"},
                    {"id": 1743744221285, "name": "current_salary", "type": "Number", "label": "Current Salary", "options": [], "isdelete": False, "required": False, "placeholder": "Current Salary"},
                    {"id": 1743744221286, "name": "expected_salary", "type": "Number", "label": "Expected Salary", "options": [], "isdelete": False, "required": False, "placeholder": "Expected Salary"}
                ]
            }
        ]

    def get_job_opening_form(self):
        """Return job opening module form structure"""
        return [
            {
                "id": 1744786434889,
                "name": "Create Job",
                "label": "Create Job",
                "fields": [
                    {"id": 1744786440082, "name": "title", "type": "Single Line", "label": "Job Title", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Job TItle"},
                    {"id": 1744786618271, "name": "vacancies", "type": "Number", "label": "Number of Vacancies", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Number of Vacancies"},
                    {"id": 1744786726119, "name": "department", "type": "Pick List", "label": "Department", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Department"},
                    {"id": 1744803220732, "name": "owner", "type": "Pick List", "label": "Owner", "options": [], "isdelete": False, "required": True, "placeholder": "Select Owner"},
                    {"id": 1744803317300, "name": "members", "type": "Multi Select", "label": "Team Member", "options": [], "isdelete": False, "required": True, "placeholder": "Select Team Member"},
                    {"id": 1744786783795, "name": "type", "type": "Pick List", "label": "Type", "options": ["Full Time", "Part Time"], "isdelete": False, "required": True, "placeholder": "Select Tyep"},
                    {"id": 1744786843652, "name": "nature", "type": "Pick List", "label": "Job Nature", "options": ["Remote", "Physical"], "isdelete": False, "required": True, "placeholder": "Select Job Nature"},
                    {"id": 1744787101161, "name": "educations", "type": "Pick List", "label": "Education", "options": ["HighSchool", "JuniorCollege", "Bachelors", "Masters"], "isdelete": False, "required": True, "placeholder": "Select Education"},
                    {"id": 1744787598403, "name": "exp_min", "type": "Number", "label": "Work Ex. min. (years)", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Work Ex"},
                    {"id": 1744787645294, "name": "exp_max", "type": "Number", "label": "Work Ex. max. (years)", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Max Work"},
                    {"id": 1744787720348, "name": "salary_min", "type": "Number", "label": "Salary (Minimum)", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Salary Minimum"},
                    {"id": 1744787769508, "name": "salary_max", "type": "Number", "label": "Salary (Maximum)", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Salary Maximum"},
                    {"id": 1744787803786, "name": "currency", "type": "Pick List", "label": "Currency", "options": [], "isdelete": False, "required": True, "placeholder": "Currency"},
                    {"id": 1744787841146, "name": "salary_type", "type": "Pick List", "label": "Salary Type", "options": ["Daily", "Weekly", "Monthly", "Yearly"], "isdelete": False, "required": True, "placeholder": "Salary Type"},
                    {"id": 1744787899154, "name": "pipeline", "type": "Pick List", "label": "Pipeline", "options": [], "isdelete": False, "required": True, "placeholder": "Pipeline"},
                    {"id": 1744787404529, "name": "speciality", "type": "Tags", "label": "Key Skills", "options": [], "isdelete": False, "required": True, "placeholder": "Select Speciality"}
                ]
            },
            {
                "id": 1752475274569,
                "name": "Address Information",
                "label": "Address Information",
                "fields": [
                    {"id": 1752239452649, "name": "country", "type": "Pick List", "label": "Country", "options": [], "isdelete": False, "required": True, "isEditable": True, "placeholder": "Country"},
                    {"id": 1752239455534, "name": "state", "type": "Pick List", "label": "State", "options": [], "isdelete": False, "required": True, "isEditable": True, "placeholder": "State"},
                    {"id": 1752239459823, "name": "city", "type": "Pick List", "label": "City", "options": [], "isdelete": False, "required": True, "isEditable": True, "placeholder": "City"},
                    {"id": 1752475364328, "name": "pincode", "type": "Number", "label": "Pincode", "options": [], "isdelete": False, "required": True, "isEditable": True, "placeholder": "Pincode"}
                ]
            },
            {
                "id": 1752475312081,
                "name": "Description Information",
                "label": "Description Information",
                "fields": [
                    {"id": 1746180241835, "name": "description", "type": "Description", "label": "Job Description", "options": [], "isdelete": False, "required": True, "placeholder": "Job Description"}
                ]
            }
        ]

    def get_interview_form(self):
        """Return interview module form structure"""
        return [
            {
                "id": 1760336752768,
                "name": "basic_info",
                "label": "Basic Info",
                "fields": [
                    {"id": 1760336777385, "name": "interview_title", "type": "Single Line", "label": "Interview Title", "options": [], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Interview Title"},
                    {"id": 1760336909538, "name": "interview_type", "type": "Pick List", "label": "Interview Type", "options": ["Online", "Offline", "Phone", "Panel"], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Interview Type"},
                    {"id": 1760337120170, "name": "mode_of_interview", "type": "Pick List", "label": "Mode of Interview", "options": ["Zoom", "Microsoft Teams", "Google Meet", "In-person", "Other"], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Mode of Interview"},
                    {"id": 1760508432505, "name": "interview_link", "type": "URL", "label": "Interview Link", "options": [], "isdelete": False, "required": False, "isEditable": True, "placeholder": "Interview Link"},
                    {"id": 1760508455534, "name": "interview_location", "type": "Pick List", "label": "Interview Location", "options": [], "isdelete": False, "required": False, "isEditable": True, "placeholder": "Interview Location"},
                    {"id": 1760348939874, "name": "job", "type": "Pick List", "label": "Select Job", "options": [], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Select Job"},
                    {"id": 1760336817918, "name": "candidate", "type": "Multi Select", "label": "Select Candidate(s)", "options": [], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Select Candidate(s)"},
                    {"id": 1760337241155, "name": "interview_round", "type": "Pick List", "label": "Interview Round", "options": ["Screening", "Technical", "Managerial", "HR", "Final"], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Interview Round"}
                ],
                "isDelete": False
            },
            {
                "id": 1760337321714,
                "name": "interviewers",
                "label": "Interviewer(s)",
                "fields": [
                    {"id": 1760337378723, "name": "interviewers", "type": "Multi Select", "label": "Select Interviewer(s) from Platform", "options": [], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Select Interviewer(s) from Platform"},
                    {"id": 1775712191215, "name": "panel", "type": "Checkbox", "label": "Panel", "options": [], "isdelete": False, "required": False, "isEditable": False,"placeholder": ""}
                ],
                "isDelete": False
            },
            {
                "id": 1760337400067,
                "name": "schedule",
                "label": "Schedule",
                "fields": [
                    {"id": 1760337455757, "name": "date", "type": "Date", "label": "Date", "options": [], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Date"},
                    {"id": 1760338014026, "name": "time", "type": "Time", "label": "Time", "options": [], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Time"},
                    {"id": 1760337556807, "name": "duration", "type": "Pick List", "label": "Duration", "options": ["15 minutes", "30 minutes", "45 minutes", "60 minutes", "90 minutes", "120 minutes"], "isdelete": False, "required": False, "isEditable": False, "placeholder": "Duration"},
                    {"id": 1760337519361, "name": "time_zone", "type": "Pick List", "label": "Time Zone", "options": [], "isdelete": False, "required": True, "isEditable": False, "placeholder": "Time Zone"}
                ],
                "isDelete": False
            },
            {
                "id": 1760337691381,
                "name": "additional_information",
                "label": "Additional Information",
                "fields": [
                    {"id": 1760337725409, "name": "notes_for_interviewer_private", "type": "Multi-Line", "label": "Notes for Interviewer (Private)", "options": [], "isdelete": False, "required": False, "isEditable": False, "placeholder": "Notes for Interviewer (Private)"},
                    {"id": 1760337744391, "name": "notes_for_candidate_public", "type": "Multi-Line", "label": "Notes for Candidate (Public)", "options": [], "isdelete": False, "required": False, "isEditable": False, "placeholder": "Notes for Candidate (Public)"}
                ],
                "isDelete": False
            },
            {
                "id": 1760337772999,
                "name": "Reminder Settings",
                "label": "Reminder Settings",
                "fields": [
                    {"id": 1760338334493, "name": "select_reminders", "type": "Multiple Radio Select", "label": "Select Reminders", "options": ["24 hours before", "1 hour before", "15 minutes before"], "isdelete": False, "required": False, "isEditable": False, "placeholder": "Select Reminders"}
                ],
                "isDelete": False
            }
        ]

    def get_assessment_form(self):
        """Return assessment module form structure"""
        return [
            {
                "id": 1744804418450,
                "name": "Assessment",
                "label": "Assessment Information",
                "fields": []
            }
        ]
