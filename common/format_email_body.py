import re
from django.conf import settings
from settings.models import Module, Department, Designation

def format_email_body(body, interview=None, candidate=None, job=None, account=None, assessment=None, contact=None):
    model_mapping = {
        'interview': interview, 'candidate': candidate, 'user': account,
        'job': job, 'assessment': assessment, 'contact': contact,
    }
    field_mapping = {
        'interview': 'dynamic_interview_data',
        'candidate': 'webform_candidate_data',
        'job': 'dynamic_job_data',
        'assessment': 'dynamic_assessment_data',
    }
    module_type = {
        'interview': 'interview',
        'candidate': 'candidate',
        'job': 'job_opening',
        'assessment': 'assessment',
    }
    
    company = (
        getattr(job, 'company', None) or getattr(interview, 'company', None) or
        getattr(assessment, 'company', None) or getattr(getattr(candidate, 'job', None), 'company', None) or
        getattr(account, 'company', None)
    )

    values = {}
    for var in re.findall(r"\$\{([a-zA-Z0-9_]+)\}", body):
        parts = var.split('_')
        model_name, field_name = parts[0], '_'.join(parts[1:])
        instance = model_mapping.get(model_name)
        data_field = field_mapping.get(model_name)
        field_value = None

        modules = Module.objects.filter(
            module_type=module_type.get(model_name), company_id=company
        ).values_list('form', flat=True)

        for module in modules:
            for section in module:
                if any(f.get('name') == field_name for f in section.get('fields', [])):
                    section_data = getattr(instance, data_field, {}).get(section['name'], {})
                    if isinstance(section_data.get(field_name), dict):
                        field_value = section_data.get(field_name).get('name')
                    else:
                        field_value = section_data.get(field_name)

        if field_value is None:
            field_value = getattr(instance, field_name, '')
            if field_name=="company" and model_name == "job":
                field_value = instance.company.name

        values[var] = field_value or ''

    return body.format(**values).replace('$', '')

def _convert_to_string(value):
    """Helper function to convert any value to a string representation"""
    if value is None:
        return ''
    elif isinstance(value, (list, tuple)):
        return ', '.join(str(item) for item in value)
    elif isinstance(value, dict):
        return str(value.get('name', value))
    else:
        return str(value)

def format_email_body_bulke_mailSend(body, interview=None, candidate=None, job=None, account=None, assessment=None, contact=None, placeholders=None):
    model_mapping = {
        'interview': interview, 'candidate': candidate, 'user': account,
        'job': job, 'assessment': assessment, 'contact': contact,
    }
    field_mapping = {
        'interview': 'dynamic_interview_data',
        'candidate': 'webform_candidate_data',
        'job': 'dynamic_job_data',
        'assessment': 'dynamic_assessment_data',
    }
    module_type = {
        'interview': 'interview',
        'candidate': 'candidate',
        'job': 'job_opening',
        'assessment': 'assessment',
    }

    company = (
        getattr(job, 'company', None) or getattr(interview, 'company', None) or
        getattr(assessment, 'company', None) or getattr(getattr(candidate, 'job', None), 'company', None) or
        getattr(account, 'company', None)
    )
    values = {}

    # Pre-populate values from placeholders if provided as a dict
    if isinstance(placeholders, dict):
        values.update(placeholders)

    # Pre-map interview fields from dynamic_interview_data JSON.
    # Structure: {"schedule": {"date":..., "time":...}, "basic_info": {"interview_title":..., ...}, "interviewers": {"interviewers": [...]}}
    if interview is not None:
        interview_list = list(interview) if hasattr(interview, '__iter__') else [interview]
        if interview_list:
            iv = interview_list[0]
            dyn = getattr(iv, 'dynamic_interview_data', {}) or {}
            
            schedule = dyn.get('schedule', {}) if isinstance(dyn, dict) else {}
            basic_info = dyn.get('basic_info', {}) if isinstance(dyn, dict) else {}
            interviewers_section = dyn.get('interviewers', {}) if isinstance(dyn, dict) else {}

            if 'interview_title' not in values:
                values['interview_title'] = str(basic_info.get('interview_title', iv.title or ''))
            if 'interview_date' not in values:
                values['interview_date'] = str(schedule.get('date', iv.date or ''))
            if 'interview_time_start' not in values:
                values['interview_time_start'] = str(schedule.get('time', iv.time_start or ''))
            if 'interview_time_end' not in values:
                values['interview_time_end'] = str(schedule.get('time_end', iv.time_end or ''))
            if 'interview_duration' not in values:
                values['interview_duration'] = str(schedule.get('duration', ''))
            if 'interview_type' not in values:
                values['interview_type'] = str(basic_info.get('interview_type', ''))
            if 'interview_round' not in values:
                values['interview_round'] = str(basic_info.get('interview_round', ''))
            if 'interview_link' not in values:
                values['interview_link'] = str(basic_info.get('interview_link', iv.meeting_link or ''))
            if 'interview_meeting_link' not in values:
                values['interview_meeting_link'] = str(iv.meeting_link or basic_info.get('interview_link', ''))
            if 'interview_mode' not in values:
                values['interview_mode'] = str(basic_info.get('mode_of_interview', ''))
            if 'interview_status' not in values:
                values['interview_status'] = str(iv.status or '')

            # Location: stored as {"id": 1, "name": "..."} in basic_info
            if 'interview_location' not in values:
                loc_data = basic_info.get('interview_location', {})
                if isinstance(loc_data, dict):
                    values['interview_location'] = str(loc_data.get('name', ''))
                elif iv.location:
                    values['interview_location'] = str(iv.location.name or iv.location.address or '')
                else:
                    values['interview_location'] = ''

            # Interviewers: stored as {"interviewers": [{"id":..., "name":...}]}
            if 'interview_interviewers' not in values:
                iw_list = interviewers_section.get('interviewers', [])
                if isinstance(iw_list, list):
                    interviewer_names = [i.get('name', '') for i in iw_list if isinstance(i, dict)]
                    values['interview_interviewers'] = ', '.join(interviewer_names)
                else:
                    values['interview_interviewers'] = ''


    for var in re.findall(r"\$\{([a-zA-Z0-9_]+)\}", body):
        if var in values:
            continue

        data_field_value = []
        parts = var.split('_')
        model_name = parts[0]
        
        # Determine field name from parts
        if model_name == "job" and len(parts) > 2 and parts[1] == "opening":
            field_name = '_'.join(parts[2:])
        elif len(parts) > 1:
            field_name = '_'.join(parts[1:])
        else:
            field_name = ""

        instance = model_mapping.get(model_name)
        data_field = field_mapping.get(model_name)
        field_value = None

        modules = Module.objects.filter(
            module_type=module_type.get(model_name), company_id=company
        ).values_list('form', flat=True)

        for module in modules:
            for section in module:
                formatted = ""
                if any(f.get('name') == field_name for f in section.get('fields', [])):
                    # Handle QuerySet (like job, interview, assessment)
                    if hasattr(instance, '__iter__'):
                        for data in instance:
                            section_data = getattr(data, data_field, {}).get(section['name'], {})
                            val = section_data.get(field_name)
                            if isinstance(val, dict):
                                data_field_value.append(val.get('name', ''))
                            elif isinstance(val, list):
                                data_field_value.append(', '.join(map(str, val)))
                            elif val is not None:
                                data_field_value.append(str(val))
                        field_value = ', '.join(data_field_value)
                    else:
                        section_data = getattr(instance, data_field, {}).get(section['name'], {})
                        val = section_data.get(field_name)
                        if isinstance(val, dict):
                            field_value = val.get('name')
                        elif isinstance(val, list):
                            field_value = ', '.join(map(str, val))
                        else:
                            field_value = val
                
                # Special handling for Education/Experience
                elif field_name == "education" and section["name"] == "Education":
                    target_instance = instance[0] if hasattr(instance, '__iter__') and len(instance) > 0 else instance
                    section_data = getattr(target_instance, data_field, {}).get(section['name'], [])
                    for idx, edu in enumerate(section_data, 1):
                        degree = edu.get("education_degree", "")
                        spec = f" in {edu.get('education_specialization', '')}" if edu.get('education_specialization') else ''
                        school = edu.get('school_name', "")
                        start = edu.get('start_date', "")
                        end = edu.get('end_date', "")

                        formatted += f"""<div style="margin-bottom: 1em;">
                            <strong>{idx}. {degree}{spec}</strong><br>
                            <span>{school}</span><br>
                            <span><strong>Duration:</strong> {start} - {end}</span><br>
                        </div>"""
                    field_value = formatted

                elif field_name == "experience" and section["name"] == "Experience":
                    target_instance = instance[0] if hasattr(instance, '__iter__') and len(instance) > 0 else instance
                    section_data = getattr(target_instance, data_field, {}).get(section['name'], [])
                    for idx, exp in enumerate(section_data, 1):
                        designation = exp.get("designation", "")
                        name_of_company = exp.get("name_of_company", "")
                        start = exp.get("from_date", "")
                        end = exp.get("to_date", "")
                        responsibilities = exp.get("job_responsibilities", "")

                        formatted += f"""
                        <div style="margin-bottom: 1em;">
                            <strong>{idx}. {designation}</strong><br>
                            <span>{name_of_company}</span><br>
                            <span><strong>Duration:</strong> {start} - {end}</span><br>
                            {"<span>" + responsibilities + "</span>" if responsibilities else ""}
                        </div>
                        """
                    field_value = formatted

        if field_value is None and field_name:
            if hasattr(instance, '__iter__'):
                attr_values = []
                for data in instance:
                    json_data = getattr(data, data_field, {}) if data_field else {}
                    val_found = False
                    if isinstance(json_data, dict):
                        if field_name in json_data:
                            val = json_data.get(field_name)
                            if isinstance(val, dict): attr_values.append(val.get('name', ''))
                            elif isinstance(val, list): attr_values.append(', '.join(map(str, val)))
                            elif val is not None: attr_values.append(str(val))
                            val_found = True
                        else:
                            for section_name, section_data in json_data.items():
                                if isinstance(section_data, dict) and field_name in section_data:
                                    val = section_data.get(field_name)
                                    if isinstance(val, dict): attr_values.append(val.get('name', ''))
                                    elif isinstance(val, list): attr_values.append(', '.join(map(str, val)))
                                    elif val is not None: attr_values.append(str(val))
                                    val_found = True
                                    break
                    if not val_found:
                        val = getattr(data, field_name, None)
                        if val is not None:
                            if hasattr(val, 'all') and callable(getattr(val, 'all', None)):
                                val_list = [str(v.name) if hasattr(v, 'name') else str(v) for v in val.all()]
                                attr_values.append(', '.join(val_list))
                            elif field_name == "company" and model_name == "job" and hasattr(val, 'name'):
                                attr_values.append(val.name)
                            else:
                                attr_values.append(str(val))
                if attr_values:
                    field_value = ', '.join(attr_values)
                else:
                    field_value = ''
            else:
                json_data = getattr(instance, data_field, {}) if data_field else {}
                val_found = False
                if isinstance(json_data, dict):
                    if field_name in json_data:
                        val = json_data.get(field_name)
                        if isinstance(val, dict): field_value = val.get('name', '')
                        elif isinstance(val, list): field_value = ', '.join(map(str, val))
                        else: field_value = str(val) if val is not None else ''
                        val_found = True
                    else:
                        for section_name, section_data in json_data.items():
                            if isinstance(section_data, dict) and field_name in section_data:
                                val = section_data.get(field_name)
                                if isinstance(val, dict): field_value = val.get('name', '')
                                elif isinstance(val, list): field_value = ', '.join(map(str, val))
                                else: field_value = str(val) if val is not None else ''
                                val_found = True
                                break
                if not val_found:
                    field_value = getattr(instance, field_name, '')
                    if getattr(field_value, '__call__', None) and not hasattr(field_value, 'all'):
                        try:
                            field_value = field_value()
                        except Exception:
                            field_value = ''
                    elif hasattr(field_value, 'all') and callable(getattr(field_value, 'all', None)):
                        val_list = [str(v.name) if hasattr(v, 'name') else str(v) for v in field_value.all()]
                        field_value = ', '.join(val_list)
                            
                    if field_name == "role" and model_name == "user":
                        if field_value == "A": field_value = "Admin"
                        elif field_value == "U": field_value = "User"
                    if field_name == "designation" and model_name == "user" and field_value:
                        try:
                            designation = Designation.objects.get(id=field_value)
                            field_value = designation.name
                        except Exception: pass
                    if field_name == "department" and model_name == "user" and field_value:
                        try:
                            department = Department.objects.get(id=field_value)
                            field_value = department.name
                        except Exception: pass
                    if field_name == "company" and model_name == "job" and hasattr(field_value, 'name'):
                        field_value = field_value.name

        values[var] = field_value or ''

    for key, val in values.items():
        body = body.replace(f'${{{key}}}', str(val))
        
    return body

def format_unsubscribe_link(unsubscribe_link, token):
    link = f'{settings.API_URL}/common/unsubscribe-email-template/{token}'
    data = {
    "Unsubscribe_Link": f"<a href='{link}'>Unsubscribe</a>",
    "From_Address": "noreply@edjobster.com",
    "Organization_Information": "Edjobster Inc, Mumbai, India"
}
    values={}
    for var in re.findall(r"\$\{([a-zA-Z0-9_]+)\}", unsubscribe_link):
        # data_field_value = []
        # list_field_value = []
        parts = var.split('_')
        # model_name, field_name = parts[0], '_'.join(parts[1:])
        values[var]=data[var]

    for key, val in values.items():
        unsubscribe_link = unsubscribe_link.replace(f'${{{key}}}', str(val))
        
    return unsubscribe_link
