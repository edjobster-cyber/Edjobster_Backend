import os
import logging
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from functools import wraps

def calculate_company_storage_usage(view_func):
    """
    Decorator to calculate and include company storage usage in the response.
    
    The decorated view should accept a company_id parameter or have it in the URL.
    The decorator will add a 'storage_info' field to the response with storage details.
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        from account.models import Company  # Moved import here to avoid circular import
        try:
            # Get company_id from URL kwargs or request data
            print("...............1")
            company_id = kwargs.get('company_id') or request.data.get('company_id',"095d7759-75cf-4d90-b7e3-59e51d3a7c52")
            # if not company_id:
            #     return Response(
            #         {'error': 'Company ID is required'},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            
            # Get the company
            try:
                company = Company.objects.get(id=company_id)
                print("...............2")
            except Company.DoesNotExist:
                return Response(
                    {'error': 'Company not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            # if hasattr(instance, 'name') and instance.name:
            #     company_name = slugify(instance.name)
            # elif hasattr(instance, 'user') and hasattr(instance.user, 'company') and instance.user.company_id:
            #     company_name = slugify(instance.user.company.name)
            # Initialize storage info
            company_dir = os.path.join(settings.MEDIA_ROOT, 'media', slugify(company.name))
            storage_info = {
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'file_count': 0,
                'directory': company_dir,
                'has_uploads': False
            }
            print("storage_info",storage_info)
            # Calculate storage if directory exists
            if os.path.exists(company_dir):
                total_size = 0
                file_count = 0
                
                # Calculate total size and file count
                for dirpath, _, filenames in os.walk(company_dir):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.isfile(fp):
                            total_size += os.path.getsize(fp)
                            file_count += 1
                
                # Update storage info
                storage_info.update({
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'file_count': file_count,
                    'has_uploads': file_count > 0
                })
                # from settings.models import Feature,CreditWallet
                
                # First get the feature by code
                # try:
                #     storage_feature = Feature.objects.get(code="file_storage_per_organization")
                # except Feature.DoesNotExist:
                #     return Response(
                #         {'error': 'Storage feature is not configured'},
                #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
                #     )
                
                # Then get the wallet for this company and feature
                # credit_wallet = CreditWallet.objects.get(
                #     company_id=request.user.company_id,
                #     feature=storage_feature
                # )
                # credit_wallet.used_credit = round(total_size / (1024 * 1024), 2)
                # credit_wallet.save()
                # print('credit_wallet',credit_wallet)
            
            # Call the original view function
            response = view_func(self, request, *args, **kwargs)
            
            # Add storage info to the response
            if hasattr(response, 'data') and isinstance(response.data, dict):
                response.data['storage_info'] = storage_info
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Error calculating storage usage: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper

def calculate_company_storage(instance):
    from settings.models import CreditWallet, Feature
    
    # Initialize storage info with default values
    storage_info = {
        'total_size_bytes': 0,
        'total_size_mb': 0,
        'file_count': 0,
        'has_uploads': False
    }

    if not instance or not hasattr(instance, 'name') or not instance.name:
        return storage_info

    company_dir = os.path.join(settings.MEDIA_ROOT, 'media', slugify(instance.name))
    storage_info['directory'] = company_dir

    if os.path.exists(company_dir):
        total_size = 0
        file_count = 0
        
        # Calculate total size and file count
        for dirpath, _, filenames in os.walk(company_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
                    file_count += 1
        
        # Update storage info
        storage_info.update({
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'has_uploads': file_count > 0
        })
        
        # First get the feature by code
        try:
            storage_feature = Feature.objects.get(code="file_storage_per_organization")
        except Feature.DoesNotExist:
            # Log error and skip wallet update
            logger = logging.getLogger(__name__)
            logger.error('Storage feature is not configured')
            return storage_info
        
        # Then get the wallet for this company and feature
        try:
            credit_wallet = CreditWallet.objects.get(
                company_id=instance.id,
                feature=storage_feature
            )
            credit_wallet.used_credit = round(total_size / (1024 * 1024), 2)
            credit_wallet.save()
        except CreditWallet.DoesNotExist:
            # Log error and skip update
            logger = logging.getLogger(__name__)
            logger.error(f'CreditWallet not found for company {instance.id} and feature {storage_feature.id}')
    
    return storage_info
    

def company_file_path(instance, filename, base_path):
    """
    Generate file path for company-specific files
    Format: media/{company_name}/{base_path}/filename
    """
    # Get company name from instance
    calculate_company_storage(instance)
    company_name = 'default'
    if hasattr(instance, 'name') and instance.name:
        print("name test",instance.name)
        company_name = slugify(instance.name)
    elif hasattr(instance, 'user') and hasattr(instance.user, 'company') and instance.user.company_id:
        company_name = slugify(instance.user.company.name)
    

    # Generate safe filename
    # ext = filename.split('.')[-1]
    # filename = f"{slugify('.'.join(filename.split('.')[:-1]))}.{ext}"
    
    return os.path.join('media', company_name, base_path, filename)


class CompanyFileStorage(FileSystemStorage):
    """
    Custom storage that saves files in company-specific directories
    """
    def __init__(self, location=None, base_url=None, file_permissions_mode=None, directory_permissions_mode=None):
        super().__init__(location, base_url, file_permissions_mode, directory_permissions_mode)
    
    def get_available_name(self, name, max_length=None):
        # Remove any existing files with the same name
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name

def user_photo_path(instance, filename):
    from account.models import Company
    instance = get_object_or_404(Company, id=instance.company_id)
    return company_file_path(instance, filename, 'users/photos')

def company_logo_path(instance, filename):
    return company_file_path(instance, filename, 'companies/logos')

def company_banner_path(instance, filename):
    return company_file_path(instance, filename, 'companies/banners')

def job_document_path(instance, filename):
    instance = instance.company
    return company_file_path(instance, filename, 'jobs/documents')

def resume_upload_path(instance, filename):
    # For ManyToManyField 'job', check if instance is saved (has PK)
    if instance.pk and instance.job.exists():
        instance = instance.job.first().company
    else:
        # Fallback to direct company attribute
        instance = getattr(instance, 'company', None)
    return company_file_path(instance, filename, 'candidates/resumes')

def cover_letter_path(instance, filename):
    if instance.pk and instance.job.exists():
        instance = instance.job.first().company
    else:
        instance = getattr(instance, 'company', None)
    return company_file_path(instance, filename, 'candidates/cover_letters')

def certificate_upload_path(instance, filename):
    if instance.pk and instance.job.exists():
        instance = instance.job.first().company
    else:
        instance = getattr(instance, 'company', None)
    return company_file_path(instance, filename, 'candidates/certificates')

def job_board_credentials_path(instance, filename):
    instance = instance.company
    return company_file_path(instance, filename, 'job_boards/credentials')

def email_template_document_path(instance, filename):
    return company_file_path(instance, filename, 'emails/templates/documents')

def qr_code_path(instance, filename):
    instance = instance.job.company
    return company_file_path(instance, filename, 'qr_codes')

def testimonial_profile_photo_path(instance, filename):
    instance = instance.company
    return company_file_path(instance, filename, 'testimonials/profile_photos')