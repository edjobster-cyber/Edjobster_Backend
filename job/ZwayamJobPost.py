from job.models import Job
import json
import requests
from django.template.loader import render_to_string
from settings.models import ZwayamAmplifyKey

# ==========================
# MAIN HANDLER
# ==========================
def handle(job_id, api_key):
    try:
        job = Job.objects.get(id=job_id)
        print(f"Processing job ID: {job_id}")
        
        if not hasattr(job, 'dynamic_job_data') or not job.dynamic_job_data:
            print(f"Error: Job {job_id} is missing dynamic_job_data")
            return {
                'status': 'error',
                'message': 'Job is missing required dynamic_job_data',
                'job_id': job_id
            }

        job_data = format_job_data(job)
        response = post_to_zwayam(job_data, api_key)

        if response.status_code == 200:
            print("Job posted successfully to Zwayam")
            print("Response:", response.text)
        else:
            print(f"Failed to post job. Status code: {response.status_code}")
            print("Response:", response.text)

    except Job.DoesNotExist:
        print(f"Job with ID {job_id} does not exist")
    except Exception as e:
        print(f"Error: {str(e)}")


# ==========================
# FORMAT JOB PAYLOAD
# ==========================
def format_job_data(job):
    if not hasattr(job, 'dynamic_job_data') or not job.dynamic_job_data:
        raise ValueError("Job is missing dynamic_job_data")
    
    try:
        # Extract job details from dynamic_job_data
        dynamic_data = job.dynamic_job_data
        if not isinstance(dynamic_data, dict):
            raise ValueError("dynamic_job_data is not a valid dictionary")
            
        create_job = dynamic_data.get('Create Job', {})
        address_info = dynamic_data.get('Address Information', {})
        desc_info = dynamic_data.get('Description Information', {})
        if isinstance(desc_info, dict):
            desc_info = desc_info.get('description', {})
    except Exception as e:
        print(f"Error processing job data: {str(e)}")
        raise
    
    # Get salary values safely
    salary_min = safe_int(create_job.get('salary_min', '0'))
    salary_max = safe_int(create_job.get('salary_max', '0'))
    
    # Get experience values safely
    exp_min = safe_int(create_job.get('exp_min', '0'))
    exp_max = safe_int(create_job.get('exp_max', '0'))
    
    # Format location
    locations = []
    if 'city' in address_info and address_info['city']:
        locations.append({"city": address_info['city'].get('name', '')})
    if 'state' in address_info and address_info['state']:
        locations.append({"state": address_info['state'].get('name', '')})
    if 'country' in address_info and address_info['country']:
        locations.append({"country": address_info['country'].get('name', '')})
    
    # Format education
    education = []
    if 'educations' in create_job and create_job['educations']:
        education.append({
            "courseType": "ug courses",
            "qualification": create_job['educations'],
            "specialization": "Any"
        })
    
    # Format description by combining job description and requirements
    description = ""
    if 'job_description' in desc_info:
        description += desc_info['job_description'] + "\n\n"
    if 'requirements' in desc_info:
        description += desc_info['requirements'] + "\n\n"
    if 'benefits' in desc_info:
        description += "Benefits:\n" + desc_info['benefits']
    
    # Format key skills
    key_skills = create_job.get('speciality', [])
    if isinstance(key_skills, str):
        key_skills = [s.strip() for s in key_skills.split(',') if s.strip()]
    
    return {
        "title": create_job.get('title', ''),
        "jobType": "hot",
        "description": description.strip(),
        "minSalary": salary_min,
        "maxSalary": salary_max,
        "salaryCurrency": create_job.get('currency', 'INR'),
        "industry": create_job.get('department', {}).get('name', 'Other'),
        "diversity": ["female"],
        "employmentType": create_job.get('type', 'Full Time, Permanent'),
        "orgName": create_job.get('company_name', ''),
        "website": "",  # Add website if available in your data
        "minWorkExperience": exp_min,
        "maxWorkExperience": exp_max,
        "keySkills": key_skills,
        "locations": locations,
        "educationQualifications": education,
        "showSalary": True,
        "notifyEmail": create_job.get('company_email', 'noreply@example.com'),
        "questions": get_default_questions(job.assesment.form if hasattr(job, 'assesment') and hasattr(job.assesment, 'form') else None),
        "referenceCode": str(create_job.get('id', '')),
        "functionalArea": create_job.get('functional_area', ''),
        "roleCode": create_job.get('role_code', '')
    }


# ==========================
# SAFE INTEGER
# ==========================
def safe_int(value):
    try:
        return int(value)
    except:
        return 0


# ==========================
# DESCRIPTION BUILDER
# ==========================
# def format_description(job_data):
#     # This function is no longer needed as we're building description directly in format_job_data
#     # Keeping it for backward compatibility
#     return job_data.get('description', '')


# ==========================
# LOCATION FORMATTER
# ==========================
def format_locations(job_data):
    # This function is no longer needed as we're building locations directly in format_job_data
    # Keeping it for backward compatibility
    return job_data.get('locations', [{"city": "Remote"}])


# ==========================
# EDUCATION FORMATTER
# ==========================
def format_education(job_data):
    # This function is no longer needed as we're building education directly in format_job_data
    # Keeping it for backward compatibility
    return job_data.get('educationQualifications', [{
        "courseType": "ug courses",
        "qualification": "Any Graduate",
        "specialization": "Any"
    }])


# ==========================
# QUESTION BUILDER
# ==========================
def get_default_questions(assessment_form):
    if not assessment_form:
        return fallback_questions()

    try:
        # If assessment_form is already a list, use it directly
        if isinstance(assessment_form, list):
            questions = assessment_form
        # If it's a string, parse it as JSON
        elif isinstance(assessment_form, str):
            questions = json.loads(assessment_form)
        # If it's an Assessment object, get the form field
        elif hasattr(assessment_form, 'form'):
            form_data = assessment_form.form
            questions = json.loads(form_data) if isinstance(form_data, str) else form_data
        else:
            return fallback_questions()
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print(f"Error parsing assessment form: {str(e)}")
        return fallback_questions()

    result = []
    mapping = {
        'MULTIPLE_CHOICE_SINGLE': 'Radio Button',
        'MULTIPLE_CHOICE_MULTI': 'Checkbox',
        'OPEN_ENDED': 'Text Box',
        'DROPDOWN': 'List Menu',
        'CHECKBOX': 'Check Box',
        'RADIO': 'Radio Button',
        'TEXT': 'Text Box'
    }

    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            continue

        qtype = mapping.get(q.get("type"), "Text Box")
        options = q.get("options", [])

        option_list = None
        if options and qtype in ["Radio Button", "Checkbox", "List Menu", "Check Box"]:
            option_list = [
                {
                    "optionId": str(i),
                    "value": opt.get("text", opt.get("value", "")),
                    "preferred": opt.get("preferred", opt.get("points", 0) > 0)
                }
                for i, opt in enumerate(options, start=1)
            ]

        result.append({
            "questionId": idx,
            "questionText": q.get("question", ""),
            "answerType": qtype,
            "answerOptions": option_list,
            "mandatory": q.get("required", True),
            "metadata": q.get("metadata", {})
        })

    return result or fallback_questions()


def fallback_questions():
    return [
        {
            "questionId": 1,
            "questionText": "Please select your gender",
            "answerType": "Radio Button",
            "answerOptions": [
                {"optionId": "1", "value": "Male", "preferred": True},
                {"optionId": "2", "value": "Female", "preferred": False},
                {"optionId": "3", "value": "Not Declared", "preferred": False},
            ],
            "mandatory": True
        }
    ]


# ==========================
# API CALL
# ==========================
def post_to_zwayam(job_data, api_key):
    url = "https://api.zwayam.com/amplify/v2/jobs/strict"
    headers = {
        "api_key": api_key,
        "Content-Type": "application/json"
    }

    print("Sending job to Zwayam...")
    print("Payload:", json.dumps(job_data, indent=2))

    response = requests.post(url, headers=headers, data=json.dumps(job_data), timeout=30)

    print("Status:", response.status_code)
    print("Response:", response.text)

    return response