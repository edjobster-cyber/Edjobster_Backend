from argparse import Action
from celery import shared_task
from .ZwayamJobPost import handle
from .helper import convert_job_to_whatjobs_format
import logging
import json
import requests
from django.conf import settings
from .models import *

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_job_creation(self, job_id, api_key):
    from .models import Job  # Import here to avoid circular import
    """
    Celery task to handle job creation in Zwayam
    """
    try:
        logger.info(f"Processing job creation for job_id: {job_id}")
        result = handle(job_id, api_key)
        logger.info(f"Successfully processed job creation for job_id: {job_id}")
        return {
            'status': 'success',
            'job_id': job_id,
            'result': result
        }
    except Exception as e:
        logger.error(f"Error processing job creation for job_id {job_id}: {str(e)}", exc_info=True)
        # Retry the task with exponential backoff
        raise self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def submit_job_to_whatjobs_task(self, job_id):
    """
    Celery task to submit or update a job on WhatJobs
    
    Args:
        job_id: ID of the job to submit/update
    """
    logger.info(f"Processing job {job_id} for WhatJobs")
    
    try:
        job = Job.objects.get(id=job_id)
        if not job.published:
            logger.info(f"Job {job_id} is not published, skipping WhatJobs")
            return False
            
        logger.info(f"Submitting job {job_id} on WhatJobs")
        
        # Convert job data to WhatJobs format with the specified action
        job_data = job or {}
        if WhatJobsJob.objects.filter(job=job).exists():
            action = 'update'
        else:
            action = 'add'
        payload = convert_job_to_whatjobs_format(job_data, action)
        print("payload",payload)
        
        # Get the WhatJobs API token from settings or environment
        WHATJOBS_TOKEN = getattr(settings, 'WHATJOBS_TOKEN', 'f6ba39e778969990346e90f63ebb01a2')
        WHATJOBS_URL = getattr(settings, 'WHATJOBS_URL', 'https://api.whatjobs.com/api/v1/jobs/submit/json')
        
        # Convert payload to JSON string for form data
        payload_json = json.dumps(payload)
        logger.info(f"payload_json {payload_json} to WhatJobs")

        # Prepare form data
        files = {
            'data': (None, payload_json, 'application/json')
        }
        

        # Make the API request with form data (matching curl format)
        response = requests.request(
            method='POST',
            url=WHATJOBS_URL,
            headers={
                'x-feed-token': WHATJOBS_TOKEN,
            },
            data={
                "data": json.dumps(payload)
            }
        )
        
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json()
        
        # Save WhatJobs job details to database
        logger.info(f"WhatJobs submission successful for job {job_id}. Response: {result}")
        response = result.get("response", [])
        job = Job.objects.get(id=job_id)
        if action == 'add':
            whatjobs_job = WhatJobsJob.objects.create(
                job=job,
                whatjobs_id= response[0].get('jobID', ''),
                jobUrl= response[0].get('jobUrl', ''),
                message = response[0].get('message', '')
            )
        else:
            whatjobs_job = WhatJobsJob.objects.get(job=job)
            whatjobs_job.whatjobs_id = response[0].get('jobID', '')
            whatjobs_job.jobUrl = response[0].get('jobUrl', '')
            whatjobs_job.message = response[0].get('message', '')
            whatjobs_job.save()
        
        return {
            'status': 'success',
            'job_id': job_id,
            'whatjobs_id': response[0].get('jobID', ''),
            'whatjobs_url': response[0].get('jobUrl', ''),
            'response': result
        }
        
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found for WhatJobs submission")
        return False
    except requests.RequestException as e:
        error_msg = f"Error submitting job {job_id} to WhatJobs: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - Response: {e.response.text}"
        logger.error(error_msg)
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
    except Exception as e:
        logger.error(f"Unexpected error submitting job {job_id} to WhatJobs: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
