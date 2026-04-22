import logging
import os
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import CandidateResume
from .resume_parser import parse_resume

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CandidateResume)
def extract_resume_data(sender, instance, created, **kwargs):
    """
    Signal handler to extract data from resume when a CandidateResume is created or updated.
    Uses the new resume_parser module for processing.
    """
    # Only process if this is a new record or the resume file has changed
    if not instance.resume:
        return
        
    # For updates, check if resume file has changed
    if not created:
        try:
            old_instance = CandidateResume.objects.get(pk=instance.pk)
            if old_instance.resume == instance.resume:
                return  # Resume file hasn't changed
        except CandidateResume.DoesNotExist:
            pass

    try:
        # Open the resume file and parse it
        with instance.resume.open('rb') as f:
            parsed_data = parse_resume(f)
            
        if parsed_data:
            # Save the extracted data
            instance.extracted_data = parsed_data
            # Use update_fields to prevent recursion
            CandidateResume.objects.filter(pk=instance.pk).update(extracted_data=parsed_data)
            logger.info(f"Successfully parsed resume {instance.resume.name}")
        else:
            logger.warning(f"Failed to parse resume {instance.resume.name}")
            
    except Exception as e:
        logger.error(f"Error processing resume {getattr(instance.resume, 'name', 'unknown')}: {str(e)}", 
                    exc_info=True)
