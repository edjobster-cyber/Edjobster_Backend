"""
Resume Data Mapper

This module provides functions to map parsed resume data to the application's module format.
"""
from datetime import datetime
from common.models import Country, State, City
from .models import SubjectSpecialization

def get_location_ids(country_name, state_name, city_name):
    """
    Get location IDs for country, state, and city if they exist.
    
    Args:
        country_name (str): Name of the country
        state_name (str): Name of the state
        city_name (str): Name of the city
        
    Returns:
        tuple: (country_id, state_id, city_id) as strings
    """
    country = Country.objects.filter(name=country_name.strip()).first() if country_name else None
    state = None
    city = None
    
    if country and state_name:
        state = State.objects.filter(
            name=state_name.strip(),
            country=country
        ).first()
        
        if state and city_name:
            city = City.objects.filter(
                name=city_name.strip(),
                state=state
            ).first()
    
    return (
        str(country.id) if country else '',
        str(state.id) if state else '',
        str(city.id) if city else ''
    )

def map_personal_details(resume_data):
    """Map personal details from resume data."""
    personal_details = {}
    
    # Basic name fields
    name = resume_data.get('Name', {})
    personal_details.update({
        'first_name': name.get('FirstName', ''),
        'last_name': name.get('LastName', ''),
        'gender': resume_data.get('Gender', '').capitalize(),
        'marital_status': resume_data.get('MaritalStatus', '').capitalize(),
        'date_of_birth': resume_data.get('DateOfBirth', '')
    })
    
    # Contact information
    if resume_data.get('Email') and len(resume_data['Email']) > 0:
        personal_details['email'] = resume_data['Email'][0].get('EmailAddress', '')
    
    if resume_data.get('PhoneNumber') and len(resume_data['PhoneNumber']) > 0:
        personal_details['phone'] = resume_data['PhoneNumber'][0].get('FormattedNumber', '')
        if len(resume_data['PhoneNumber']) > 1:
            personal_details['alternate_phone'] = resume_data['PhoneNumber'][1].get('FormattedNumber', '')
    
    # Address handling
    _process_address_data(resume_data, personal_details)
    
    # Calculate age if date of birth is available
    _calculate_age(personal_details)
    
    return personal_details

def _process_address_data(resume_data, personal_details):
    """Process address data from resume."""
    if not resume_data.get('Address'):
        return
        
    address_data = resume_data['Address']
    
    if isinstance(address_data, list) and address_data:
        _process_legacy_address_format(address_data[0], personal_details)
    else:
        _process_modern_address_format(address_data, personal_details)

def _process_legacy_address_format(address, personal_details):
    """Process legacy address format (list with single address object)."""
    personal_details['street'] = address.get('Street', '')
    
    country_name = address.get('Country', '')
    state_name = address.get('State', '')
    city_name = address.get('City', '')
    
    country_id, state_id, city_id = get_location_ids(country_name, state_name, city_name)
    
    personal_details.update({
        'country': {'id': country_id, 'name': str(country_name)},
        'state': {'id': state_id, 'name': str(state_name)},
        'city': {'id': city_id, 'name': str(city_name)},
        'pincode': str(address.get('ZipCode', ''))
    })

def _process_modern_address_format(address, personal_details):
    """Process modern address format (direct object)."""
    personal_details['street'] = address.get('street', '')
    
    # Handle city, state, country as either objects or strings
    city = address.get('city', {}) if isinstance(address.get('city'), dict) else {'name': address.get('city', '')}
    state = address.get('state', {}) if isinstance(address.get('state'), dict) else {'name': address.get('state', '')}
    country = address.get('country', {}) if isinstance(address.get('country'), dict) else {'name': address.get('country', '')}
    
    # Get location IDs
    country_id, state_id, city_id = get_location_ids(
        country.get('name', ''),
        state.get('name', ''),
        city.get('name', '')
    )
    
    # Update with IDs from database or original IDs
    personal_details.update({
        'country': {
            'id': country_id or country.get('id', ''),
            'name': str(country.get('name', ''))
        },
        'state': {
            'id': state_id or state.get('id', ''),
            'name': str(state.get('name', ''))
        },
        'city': {
            'id': city_id or city.get('id', ''),
            'name': str(city.get('name', ''))
        },
        'pincode': str(address.get('pincode', address.get('zipcode', '')))
    })

def _calculate_age(personal_details):
    """Calculate age from date of birth if available."""
    if not personal_details.get('date_of_birth'):
        return
    
    try:
        birth_date = datetime.strptime(personal_details['date_of_birth'], '%Y-%m-%d')
        age = datetime.now().year - birth_date.year
        if (datetime.now().month, datetime.now().day) < (birth_date.month, birth_date.day):
            age -= 1
        personal_details['age'] = str(age)
    except (ValueError, TypeError):
        pass

def map_professional_details(resume_data):
    """Map professional details from resume data."""
    professional_details = {
        'exp_years': resume_data.get('YearsOfExperience', ''),
        'highest_qualification': resume_data.get('HighestQualification', ''),
        'current_employer': resume_data.get('CurrentEmployer', ''),
        'currently_working': 'Yes' if resume_data.get('CurrentlyWorking') == 'Yes' else 'No',
        'professional_start_date': resume_data.get('ProfessionalStartDate', ''),
        'professional_end_date': resume_data.get('ProfessionalEndDate', ''),
        'current_job_title': resume_data.get('CurrentJobTitle', ''),
        'current_salary': resume_data.get('CurrentSalary', {}).get('Amount', ''),
        'expected_salary': resume_data.get('ExpectedSalary', {}).get('Amount', ''),
        'salary_currency': resume_data.get('SalaryCurrency', resume_data.get('CurrentSalary', {}).get('Currency', '')),
        'professional_certificate': resume_data.get('ProfessionalCertificate', '')
    }
    
    # Map professional degree
    professional_degree = resume_data.get('ProfessionalDegree', '')
    if 'MBA' in professional_degree:
        professional_degree = 'MBA - ' + professional_degree.replace('MBA', '').strip(' -')
    professional_details['degrees'] = professional_degree
    
    # Map subjects
    _map_subjects(resume_data, professional_details)
    
    # Map skills
    professional_details['skills'] = []
    if 'SegregatedSkill' in resume_data:
        professional_details['skills'] = [
            {'name': skill.get('Skill', '')}
            for skill in resume_data['SegregatedSkill']
            if skill.get('Skill')
        ]
    
    return professional_details

def _map_subjects(resume_data, professional_details):
    """Map subject data from resume to professional details."""
    subject_data = resume_data.get('Subject', '')
    if not subject_data:
        professional_details['subject'] = []
        return
    
    if isinstance(subject_data, list):
        # New format: [{"id": 5, "name": "English"}, ...]
        subjects = []
        for subj in subject_data:
            if not subj:
                continue
                
            name = str(subj.get('name', '')).strip()
            if not name:
                continue
                
            # Try to find existing subject by name
            subject = SubjectSpecialization.objects.filter(name__iexact=name).first()
            subjects.append({
                'id': str(subject.id) if subject else '',
                'name': name
            })
        professional_details['subject'] = subjects
    else:
        # Old format: "English, Political Science"
        professional_details['subject'] = [
            {
                'id': str(SubjectSpecialization.objects.filter(name__iexact=s.strip()).first().id) 
                if SubjectSpecialization.objects.filter(name__iexact=s.strip()).exists() 
                else '',
                'name': s.strip()
            } 
            for s in subject_data.split(',') 
            if s.strip()
        ]

def map_education(resume_data):
    """Map education history from resume data."""
    education = []
    
    if 'Education' in resume_data and isinstance(resume_data['Education'], list):
        for edu in resume_data['Education']:
            if not edu:
                continue
                
            education.append({
                'institution': edu.get('SchoolName', ''),
                'degree': edu.get('Degree', ''),
                'field_of_study': edu.get('FieldOfStudy', ''),
                'start_date': edu.get('StartDate', ''),
                'end_date': edu.get('EndDate', ''),
                'description': edu.get('Description', '')
            })
    
    return education

def map_experience(resume_data):
    """Map work experience from resume data."""
    experience = []
    
    if 'Experience' in resume_data and isinstance(resume_data['Experience'], list):
        for exp in resume_data['Experience']:
            if not exp:
                continue
                
            experience.append({
                'company': exp.get('Company', ''),
                'position': exp.get('Position', ''),
                'start_date': exp.get('StartDate', ''),
                'end_date': exp.get('EndDate', ''),
                'is_current': exp.get('IsCurrent', False),
                'description': exp.get('Description', '')
            })
    
    return experience

def map_resume_to_module(resume_data, module_form):
    """
    Map resume data to module form fields.
    
    Args:
        resume_data: Dictionary containing parsed resume data
        module_form: Module form structure from the database
        
    Returns:
        Dictionary with module names as keys and field mappings as values
    """
    result = {}
    
    # Map personal details
    result['Personal Details'] = map_personal_details(resume_data)
    
    # Map professional details
    result['Professional Details'] = map_professional_details(resume_data)
    
    # Map education
    result['Education'] = map_education(resume_data)
    
    # Map experience
    result['Experience'] = map_experience(resume_data)
    
    return result
