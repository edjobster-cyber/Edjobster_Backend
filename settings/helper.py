from collections import namedtuple
import email
import re
from unicodedata import category
from account.models import Account, Company, TokenEmailVerification, TokenResetPassword
from candidates.models import Candidate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import authenticate
from common.encoder import decode
from common.utils import isValidUuid, getDomainFromEmail
from common.models import Country, State, City
import json

from job.decorators import check_subscription_and_credits, deduct_credit_decorator
from settings.decorators import check_feature_availability
from .models import Contacts, CreditWallet, Degree, Department, Designation, EmailCategory, EmailFields, EmailTemplate, FeatureUsage, Location, Pipeline, PipelineStage, PlanFeatureCredit, Webform, TemplateVariables, Plan, Subscription, EmailCredential, Module, OrganizationalEmail, UnsubscribeLink, UnsubscribeEmailToken
from .serializer import ContactsDataSerializer, DegreeSerializer, PipelineStagListSerializer, DepartmentSerializer, DesignationSerializer, EmailCategorySerializer, EmailFieldSerializer, EmailTemplateSerializer, LocationSerializer, PipelineSerializer, PipelineStageSerializer, WebformDataSerializer, WebformListSerializer, TemplateVariablesSerializer, BillingPlanSerializer, SubscriptionSerializer, EmailCredentialsSerializer, ModuleSerializer, OrganizationalEmailSerializer, UnsubscribeLinkSerializer
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from job.models import Job

def getCompanyByUser(user):
    return Company.getByUser(user.use)

#INSTITUTE SETTINGS
def getLocations(request):
    
    user = request.user

    if user.is_superuser:
        locations = Location.objects.all()
    else:
        locations = Location.objects.filter(company__id=user.company_id)

    serializer = LocationSerializer(locations, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }
    
def getLocationsCareer(pk=None):
    
    if pk:   
        location = Location.objects.get(pk=pk)
        serializer = LocationSerializer(location)
    else:
        # Fetch all locations
        locations = Location.objects.all()
        serializer = LocationSerializer(locations, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }

def saveLocation(request):

    data = request.data
    name = data.get('name', None)
    address = data.get('address', None)
    city = data.get('city', None)
    pincode = data.get('pincode', None)
    loc_lat = data.get('loc_lat', None)
    loc_lon = data.get('loc_lon', None)

    company = Company.getByUser(request.user)

    if not company or not name or not address or not city or not pincode:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    city = City.getById(city)    

    id = data.get('id', None)
    if id:
        location = Location.getById(id, company)
        if not location:
            return {
                'code': 400,
                'msg': 'location not found'
            }
    else:
        location = Location()
        location.company = company

    location.name = name
    location.address = address
    location.city = city
    location.state = city.state
    location.country = city.state.country
    location.pincode = pincode
    location.loc_lat = loc_lat
    location.loc_lon = loc_lon

    location.save()

    return getLocations(request)

def deleteLocation(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        location = Location.getById(id, company)
        if not location:
            return {
                'code': 400,
                'msg': 'Location not found'
            }

        location.delete()
        return {
            'code': 200,
            'msg': 'Location deleted succesfully!',
            'data': getLocations(request)['data']
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }

def getDepartments(request):

    user = request.user
    company_id = request.GET.get('company_id')
    role = '' 

    if user.is_authenticated:
        role = 'superuser' if user.is_superuser else 'admin' if user.role == Account.ADMIN else 'user'
        if user.is_superuser:
            departments = Department.objects.all()
        else:
            departments = Department.objects.filter(Q(company__id=user.company_id) | Q(company__isnull=True))
    else:
        departments = Department.objects.filter(Q(company__id=company_id) | Q(company__isnull=True))
        
    serializer = DepartmentSerializer(departments, many=True)

    return {
        'code': 200,
        'data': serializer.data,
        'role': role
    }    

def saveDepartment(request):

    company = Company.getByUser(request.user)    
    data = request.data    
    name = data.get('name', None)   

    if not name:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    id = data.get('id', None)

    if id:
        department = Department.getById(id, company)
        if not department:
            return {
                'code': 400,
                'msg': 'Department not found'
            }
        if department.name != name and Department.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Department with name '+name+' already exists.'
            } 
    else:
        if Department.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Department with name '+name+' already exists.'
            } 

        department = Department()   
        department.company = company
    
    department.name = name
    department.save()

    return getDepartments(request)

def deleteDepartment(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        department = Department.getById(id, company)
        if not department:
            return {
                'code': 400,
                'msg': 'Department not found'
            }

        department.delete()
        return {
            'code': 200,
            'msg': 'Department deleted succesfully!',
            'data': getDepartments(request)['data']
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }    

def getDegrees(request):
    
    user = request.user
    role = ''
    
    if user.is_authenticated:
        role = 'superuser' if user.is_superuser else 'admin' if user.role == Account.ADMIN else 'user'

    if user.is_superuser:
        degrees = Degree.objects.all()
    else:
        degrees = Degree.objects.filter(Q(company__id=user.company_id) | Q(company__isnull=True))

    serializer = DegreeSerializer(degrees, many=True)

    return {
        'code': 200,
        'data': serializer.data,
        'role': role
    }    

def saveDegree(request):

    company = Company.getByUser(request.user)    
    
    data = request.data    
    name = data.get('name', None)   

    if not name:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    id = data.get('id', None)

    if id:
        degree = Degree.getById(id, company)
        if not degree:
            return {
                'code': 400,
                'msg': 'Degree not found'
            }
        if degree.name != name and Degree.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Degree with name '+name+' already exists.'
            } 
    else:
        if Degree.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Degree with name '+name+' already exists.'
            } 

        degree = Degree()    
        degree.company = company

    
    degree.name = name
    degree.save()

    return getDegrees(request)

def deleteDegree(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        degree = Degree.getById(id, company)
        if not degree:
            return {
                'code': 400,
                'msg': 'Degree not found'
            }

        degree.delete()
        return {
            'code': 200,
            'msg': 'Degree deleted succesfully!',
            'data': getDegrees(request)['data']
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }        

def getDesignations(request):

    user = request.user
    role = ''
    
    if user.is_authenticated:
        role = 'superuser' if user.is_superuser else 'admin' if user.role == Account.ADMIN else 'user'

    if user.is_superuser:
        designation = Designation.objects.all()
    else:
        designation = Designation.objects.filter(Q(company__id=user.company_id) | Q(company__isnull=True))

    serializer = DesignationSerializer(designation, many=True)

    return {
        'code': 200,
        'data': serializer.data,
        'role': role
    }    

def saveDesignation(request):

    company = Company.getByUser(request.user)    
    
    data = request.data    
    name = data.get('name', None)   

    if not name:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    id = data.get('id', None)

    if id:
        designation = Designation.getById(id, company)
        if not designation:
            return {
                'code': 400,
                'msg': 'Designation not found'
            }
        if designation.name != name and Designation.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Designation with name '+name+' already exists.'
            } 
    else:
        if Designation.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Designation with name '+name+' already exists.'
            } 

        designation = Designation()    
        designation.company = company
    
    designation.name = name
    designation.save()

    return getDesignations(request)

def deleteDecignation(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        designation = Designation.getById(id, company)
        if not designation:
            return {
                'code': 400,
                'msg': 'Designation not found'
            }

        designation.delete()
        return {
            'code': 200,
            'msg': 'Designation deleted succesfully!',
            'data': getDesignations(request)['data']
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }        

#PIPELINES
def getPipelineStages(request):
    pipeline_id = request.GET.get('id')
    user = request.user
    
    # Check for invalid pipeline_id values
    if not pipeline_id or pipeline_id in ['undefined', 'null', 'None', '']:
        pipeline_id = None

    if user.is_superuser:
        if pipeline_id:
            try:
                pipeline = Pipeline.objects.get(id=pipeline_id)
            except (Pipeline.DoesNotExist, ValueError):
                return {
                    'code':400,
                    'msg': 'Pipeline not found'
                }
            if not pipeline:
                return {
                    'code':400,
                    'msg': 'Pipeline not found'
                }
        else:
            data = Pipeline.objects.all()
            serializer = PipelineStagListSerializer(data, many=True)
            return {
                'code': 200,
                'data': serializer.data
            }
    else:
        company = Company.getByUser(request.user)
        if not company:
            return {
                'code': 400,
                'msg': 'Invalid request'
            }
        if pipeline_id:
            pipeline = Pipeline.getById(id=pipeline_id, company=company)
        else:
            pipeline = None
        if not pipeline:
            data= Pipeline.getForCompany(company=company)
            serializer = PipelineStagListSerializer(data, many=True)
            return{
                'code': 200,
                'data': serializer.data
            }
            
    id1 = pipeline.stage1.id
    id2 = pipeline.stage2.id
    id3 = pipeline.stage3.id
    id4 = pipeline.stage4.id
    id5 = pipeline.stage5.id
    id6 = pipeline.stage6.id
    id7 = pipeline.stage7.id

    pipelineStates = PipelineStage.objects.filter(id__in = [id1, id2, id3, id4, id5, id6, id7]).order_by('id')

    serializer = PipelineStagListSerializer(pipelineStates, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }    

def savePipelineStage(request):
    pipeline_id = request.GET.get('id')
    company = Company.getByUser(request.user)    
    
    data = request.data    

    pipeline = Pipeline.getById(id = pipeline_id, company=company)

    if not pipeline:
        return {
            'code': 400,
            'msg': 'Pipeline not Valid'
        }

    id = data.get('id', None)

    update = False

    if id:
        pipelineStage = PipelineStage.getByPipeline(company=company, pipeline=pipeline)
        if not pipelineStage:
            return {
                'code': 400,
                'msg': 'Pipeline Stage not found'
            }
        update = True
    else:
        pipelineStage = PipelineStage()    
        pipelineStage.company = company

        
    
    if data.get('name'):
        pipelineStage.name = data.get('name')

    if data.get('status'):
        pipelineStage.status = data.get('status')
    pipelineStage.pipeline = pipeline

    if not update: 
        pipelineStage.save()

    return getPipelineStages(request)

def deletePipelineStage(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)
    pipeline= PipelineStage()
    if id:
        pipelineStage = PipelineStage.getById(id)
        if not pipelineStage:
            return {
                'code': 400,
                'msg': 'Pipeline Stage not found'
            }

        pipelineStage.delete()
        pipelineStage.save()
        pipeline.save()
        return {
            'code': 200,
            'msg': 'Pipeline Stage deleted succesfully!'
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }        


def getPipelineStageDetails(request):

    stage_id = request.GET.get('id', None)   

    if not stage_id:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    company = Company.getByUser(request.user)    
    stage = PipelineStage.getById(stage_id)
    if not stage:
        return {
            'code': 400,
            'msg': 'Pipeline Status not found'
        }

    serializer = PipelineStageSerializer(stage, many=False)

    return {
        'code': 200,
        'data': serializer.data
    }    

def savePipelineStatus(request):

    company = Company.getByUser(request.user)    
    
    data = request.data    
    stage_id = data.get('stage', None)   
    status = data.get('status', None)   

    if not stage_id or not isinstance(status, list):
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    stage = PipelineStage.getById(stage_id)
    if not stage:
        return {
            'code': 400,
            'msg': 'Pipeline Status not found'
        }
    
    stage.status = status
    stage.save()

    serializer = PipelineStageSerializer(stage, many=False)

    return {
        'code': 200,
        'msg' : 'Pipeline stage updated!',
        'data': serializer.data
    }   


def getPipelines(request):

    company = Company.getByUser(request.user)
    pipelines = Pipeline.getForCompany(company=company)

    serializer = PipelineSerializer(pipelines, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }    

def savePipeline(request):

    # company = request.data.get('company', None)   
    # company = Company.getByUser(company)
    company = Company.getByUser(request.user)    
    
    data = request.data    
    name = data.get('name', None)   
    
    if not name:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    if Pipeline.getByName(name=name, company=company):
        return {
            'code': 400,
            'msg': 'Pipeline with name '+name+' already exists.'
        } 

    pipeline = Pipeline()    
    pipeline.company = company
    pipeline.name = name
    pipeline.save()

    return getPipelines(request)

def deletePipeline(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        pipeline = Pipeline.getById(id, company)
        if not pipeline:
            return {
                'code': 400,
                'msg': 'Pipeline not found'
            }

        pipeline.delete()
        return {
            'code': 200,
            'msg': 'Pipeline deleted succesfully!',
            'data': getPipelines(request)['data']
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }   

def getJobAssociatedPipelineStages(request):
    company = Company.getByUser(request.user)
    pipeline = Pipeline.objects.get(company=company)

    id1 = pipeline.stage1.id
    id2 = pipeline.stage2.id
    id3 = pipeline.stage3.id
    id4 = pipeline.stage4.id
    id5 = pipeline.stage5.id
    id6 = pipeline.stage6.id
    id7 = pipeline.stage7.id

    pipelineStages = PipelineStage.objects.filter(id__in = [id1, id2, id3, id4, id5, id6, id7]).order_by('id')

    serializer = PipelineStagListSerializer(pipelineStages, many=True)
    return{
        'code': 200,
        'data': serializer.data,
    }

#EMAILS

def getEmailFileds(request):

    fields = EmailFields.getAll()

    serializer = EmailFieldSerializer(fields, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }        

def getEmailCategories(request):
    
    user = request.user

    role = 'superuser' if user.is_superuser else 'admin' if user.role == Account.ADMIN else 'user'
    if user.is_superuser:
        emails = EmailCategory.objects.all()
    else:
        emails = EmailCategory.objects.filter(Q(company__id=user.company_id) | Q(company__isnull=True))

    serializer = EmailCategorySerializer(emails, many=True)

    return {
        'code': 200,
        'data': serializer.data,
        'role': role
    }    

def saveEmailCategory(request):

    company = Company.getByUser(request.user)    
    
    data = request.data    
    name = data.get('name', None)   

    if not name:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    id = data.get('id', None)

    if id:
        category = EmailCategory.getById(id, company)
        if not category:
            return {
                'code': 400,
                'msg': 'Email Category not found'
            }
        if category.name != name and EmailCategory.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Email Category with name '+name+' already exists.'
            } 
    else:
        if EmailCategory.getByName(name=name, company=company):
            return {
                'code': 400,
                'msg': 'Email Category with name '+name+' already exists.'
            } 
        category = EmailCategory()   
        category.company = company

    category.name = name
    category.save()

    return getEmailCategories(request)

def deleteEmailCategory(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        category = EmailCategory.getById(id, company)
        if not category:
            return {
                'code': 400,
                'msg': 'Email Category not found'
            }

        category.delete()
        return {
            'code': 200,
            'msg': 'Email Category deleted succesfully!',
            'data': getEmailCategories(request)['data']
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }         

def getEmailTemplates(request):
    
    user = request.user
    
    role = 'superuser' if user.is_superuser else 'admin' if user.role == Account.ADMIN else 'user'
    if user.is_superuser:
        emails = EmailTemplate.objects.all()
    else:
        emails = EmailTemplate.objects.filter(Q(company__id=user.company_id) | Q(company__isnull=True))

    serializer = EmailTemplateSerializer(emails, many=True)

    return {
        'code': 200,
        'data': serializer.data,
        'role': role
    }    

@deduct_credit_decorator("Email_Templates")
@check_subscription_and_credits("Email_Templates")
def saveEmailTemplate(self_or_request,request):

    if request is None:
        request = self_or_request
    else:
        self = self_or_request

    company = Company.getByUser(request.user)

    data = request.data    
    type = data.get('type', None)   
    category = data.get('category_id', None)   
    subject = data.get('subject', None)   
    name = data.get('name', None)   
    message = data.get('message', None)
    from_email = data.get('from_email', None)
    reply_to = data.get('reply_to', None)
    
    
    # Convert string boolean values to actual boolean
    add_signature = data.get('add_signature', False)
    if isinstance(add_signature, str):
        add_signature = add_signature.lower() == 'true'
    
    unsubscribe_link = data.get('unsubscribe_link', False)
    if isinstance(unsubscribe_link, str):
        unsubscribe_link = unsubscribe_link.lower() == 'true'
        
    # Get additional fields
    footer = data.get('footer', None)
    attachment_category = data.get('attachment_category', None)
    attachment_subcategory = data.get('attachment_subcategory', None)

    if not category or not type or not type in EmailTemplate.EMAIL_TYPES or not message or not subject or not name:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    category = EmailCategory.getById(category, company)    
    if not category:
        return {
            'code': 400,
            'msg': 'Category not found!'
        }

    id = data.get('id', None)

    if id:
        email = EmailTemplate.getById(id, company)
        if not email:
            return {
                'code': 400,
                'msg': 'Email not found'
            }
        if email.subject != subject and EmailTemplate.getByName(subject=subject, company=company):
            return {
                'code': 400,
                'msg': 'Email Template with subject '+subject+' already exists.'
            } 
    else:
        if EmailTemplate.getByName(subject=subject, company=company):
            return {
                'code': 400,
                'msg': 'Email Template with subject '+subject+' already exists.'
            } 

        email = EmailTemplate()  
        email.company = company  

    if request.FILES != None:
        print("attachments")
        print(request.FILES)
        if 'attachment' in request.FILES:
            file = request.FILES['attachment']
            if email.attachment:
                email.attachment.delete()
            email.attachment = file    
    
    email.category = category
    email.type = type
    email.subject = subject
    email.name = name
    email.message = message
    email.from_email = from_email
    email.reply_to = reply_to
    email.add_signature = add_signature
    email.unsubscribe_link = unsubscribe_link
    email.footer = footer
    email.attachment_category = attachment_category
    email.attachment_subcategory = attachment_subcategory
    email.save()

    return getEmailTemplates(request)

def UpdateEmailTemplate(request):

    company = Company.getByUser(request.user)

    data = request.data    
    type = data.get('type', None)   
    category = data.get('category_id', None)   
    subject = data.get('subject', None)   
    name = data.get('name', None)   
    message = data.get('message', None)
    from_email = data.get('from_email', None)
    reply_to = data.get('reply_to', None)
    
    
    # Convert string boolean values to actual boolean
    add_signature = data.get('add_signature', False)
    if isinstance(add_signature, str):
        add_signature = add_signature.lower() == 'true'
    
    unsubscribe_link = data.get('unsubscribe_link', False)
    if isinstance(unsubscribe_link, str):
        unsubscribe_link = unsubscribe_link.lower() == 'true'
        
    # Get additional fields
    footer = data.get('footer', None)
    attachment_category = data.get('attachment_category', None)
    attachment_subcategory = data.get('attachment_subcategory', None)

    if not category or not type or not type in EmailTemplate.EMAIL_TYPES or not message or not subject or not name:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    category = EmailCategory.getById(category, company)    
    if not category:
        return {
            'code': 400,
            'msg': 'Category not found!'
        }

    id = data.get('id', None)

    if id:
        email = EmailTemplate.getById(id, company)
        if not email:
            return {
                'code': 400,
                'msg': 'Email not found'
            }
        if email.subject != subject and EmailTemplate.getByName(subject=subject, company=company):
            return {
                'code': 400,
                'msg': 'Email Template with subject '+subject+' already exists.'
            } 
    else:
        if EmailTemplate.getByName(subject=subject, company=company):
            return {
                'code': 400,
                'msg': 'Email Template with subject '+subject+' already exists.'
            } 

        email = EmailTemplate()  
        email.company = company  

    if request.FILES != None:
        print("attachments")
        print(request.FILES)
        if 'attachment' in request.FILES:
            file = request.FILES['attachment']
            if email.attachment:
                email.attachment.delete()
            email.attachment = file    
    
    email.category = category
    email.type = type
    email.subject = subject
    email.name = name
    email.message = message
    email.from_email = from_email
    email.reply_to = reply_to
    email.add_signature = add_signature
    email.unsubscribe_link = unsubscribe_link
    email.footer = footer
    email.attachment_category = attachment_category
    email.attachment_subcategory = attachment_subcategory
    email.save()

    return getEmailTemplates(request)


def deleteEmailTemmplate(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        email = EmailTemplate.getById(id, company)
        if email and email.attachment:
                email.attachment.delete()
        if not email:
            return {
                'code': 400,
                'msg': 'Email Template not found'
            }

        email.delete()
        return {
            'code': 200,
            'msg': 'Email Template deleted succesfully!',
            'data': getEmailTemplates(request)['data']
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }  
    
def getModulesTypes(request):
    module_type = request.GET.get('moduleType', None)  # New line to get module_type
    company = Company.getByUser(request.user)
    module_type_list = module_type.split(",")
    if module_type:  # Check if module_type is provided
        modules = Module.objects.filter(company=company,module_type__in=module_type_list)
    else:
        modules = Module.objects.filter(company=company)  # Get all modules for the company
    serializer = ModuleSerializer(modules, many=True)
    
    return {
        'code': 200,
        'data': serializer.data
    }
          
def getModules(request):
    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)
    if id:
        if request.user.is_superuser:
            module = Module.objects.get(id=id)
        else:
            module = Module.objects.get(id=id, company=company)
            
        if not module:
            return {
                'code': 400,
                'msg': 'Module not found'
            }
        serializer = ModuleSerializer(module)
    else:
        if request.user.is_superuser:
            modules = Module.objects.all()
        else:
            modules = Module.objects.filter(company=company)
        serializer = ModuleSerializer(modules, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }

def count_fields(form):
    count = 0
    if isinstance(form, list):
        for section in form:
            if 'fields' in section:
                count += len(section['fields'])
    return count

def saveModule(request):
    
    # if request is None:
    #     request = self_or_request
    # else:
    #     self = self_or_request

    data = request.data
    id = data.get('id', None)
    company = Company.getByUser(request.user)

    # Get credit limit for Custom_Fields
    subscription = Subscription.objects.filter(company=company, is_active=True).first()
    credit_limit = 0
    if subscription:
        credit = CreditWallet.objects.filter(company=company, feature__code="Custom_Fields").first()
        
        if credit:
            credit_limit = credit.total_credit or 0

    default_counts = {
        'candidate': 46,
        'interview': 16,
        'job_opening': 21,
        'assessment': 0
    }

    if id:
        module = Module.getById(id, company)
        module.name = data.get('name', None)
        # module.module_type = data.get('module_type', None)
        form_data = data.get('form', None)
        if form_data:
            total_fields = count_fields(form_data)
            default_count = default_counts.get(module.module_type, 0)
            custom_fields = max(0, total_fields - default_count)
            if custom_fields > credit_limit:
                return {'msg': f'Exceeded custom fields limit. Allowed: {credit_limit}, Current: {custom_fields}'} ,status.HTTP_400_BAD_REQUEST
        module.form = form_data
        module.save()
        return {'msg': 'Module saved successfully!'}, status.HTTP_200_OK
    if data:
        module_type = data.get('module_type', None)
        form_data = data.get('form', None)
        if form_data and module_type:
            total_fields = count_fields(form_data)
            default_count = default_counts.get(module_type, 0)
            custom_fields = max(0, total_fields - default_count)
            if custom_fields > credit_limit:
                return {'msg': f'Exceeded custom fields limit. Allowed: {credit_limit}, Current: {custom_fields}'}, status.HTTP_400_BAD_REQUEST
        serializer = ModuleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return {'msg': 'Module saved successfully!'} ,status.HTTP_200_OK

def deleteModule(request):
    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)
    if id:
        module = Module.getById(id,company)
        
        if not module:
            return {
                'code': 400,
                'msg': 'Module not found'
            }
        module.delete()
        return {
            'code': 200,
            'msg': 'Module deleted successfully!'
        }
    return {
        'code': 400,
        'msg': 'Invalid request'
    }

def getModuleCompany(request):
    company = Company.getByUser(request.user)
    module_type="candidate"
    if company:
        module = Module.objects.filter(company=company, module_type=module_type).last()
        serializer= ModuleSerializer(module)
        return{
            'code':200,
            'data':serializer.data
        }

def getWebforms(request):

    company = Company.getByUser(request.user)

    id = request.GET.get('id', None)

    if id:
        user = request.user
        try:
            if user.is_superuser:
                form = Webform.objects.get(id=id)
            else:
                form = Webform.objects.get(id=id)
        except (Webform.DoesNotExist, ValueError):
            return {
                'code': 400,
                'msg': 'Form not found'
            }
        serializer = WebformDataSerializer(form)
    else:
        user = request.user
        if user.is_superuser:
            forms = Webform.objects.all().order_by('created')
        else:
            forms = Webform.objects.filter(company__id=user.company_id).order_by('created')
        
        serializer = WebformListSerializer(forms, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }    

@deduct_credit_decorator("Web_Forms")
@check_subscription_and_credits("Web_Forms")
def saveWebForms(self_or_request,request):
    if request is None:
        request = self_or_request
    else:
        self = self_or_request
    company = Company.getByUser(request.user)    
    
    data = request.data    
    name = data.get('name', None)   
    form = data.get('form', None)   

    if not company or not name or not form:
        return {"msg":'Invalid request'},status.HTTP_400_BAD_REQUEST
        

    id = data.get('id', None)

    if id:
        webform = Webform.getById(id, company)
        if not webform:
            return {"msg":'Webform not found'}, status.HTTP_400_BAD_REQUEST
        if webform.name != name:
            if Webform.getByName(name, company):
                return {"msg":'Webform with name '+name+' already exists!'}, status.HTTP_400_BAD_REQUEST
    else:
        if Webform.getByName(name, company):
            return {"msg":'Webform with name '+name+' already exists!'}, status.HTTP_400_BAD_REQUEST

        webform = Webform()  
        # webform.company = company
    company = Company.objects.get(id=company.id)
    webform.company = company
    webform.name = name
    webform.form = form

    webform.save()

    return {"msg":'Webform saved successfully!'},status.HTTP_200_OK

def UpdateWebForms(request):

    company = Company.getByUser(request.user)    
    
    data = request.data    
    name = data.get('name', None)   
    form = data.get('form', None)   

    if not company or not name or not form:
        return {"msg":'Invalid request'},status.HTTP_400_BAD_REQUEST
        

    id = data.get('id', None)

    if id:
        webform = Webform.getById(id, company)
        if not webform:
            return {"msg":'Webform not found'}, status.HTTP_400_BAD_REQUEST
        if webform.name != name:
            if Webform.getByName(name, company):
                return {"msg":'Webform with name '+name+' already exists!'}, status.HTTP_400_BAD_REQUEST
    else:
        if Webform.getByName(name, company):
            return {"msg":'Webform with name '+name+' already exists!'}, status.HTTP_400_BAD_REQUEST

        webform = Webform()  
        # webform.company = company
    company = Company.objects.get(id=company.id)
    webform.company = company
    webform.name = name
    webform.form = form

    webform.save()

    return {"msg":'Webform saved successfully!'},status.HTTP_200_OK

def deleteWebforms(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        form = Webform.getById(id, company)

        if not form:
            return {
                'code': 400,
                'msg': 'Webform not found'
            }

        form.delete()
        return {
            'code': 200,
            'msg': 'Webform deleted succesfully!',
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }            

def getWebformFields(request):

    return {
        'code': 200,
        'data': [
            {
                'name': 'First Name',
                'value': 'first_name',
                'type': 'text'
            },
            {
                'name': 'Middle Name',
                'value': 'middle_name',
                'type': 'text'
            },
            {
                'name': 'Last Name',
                'value': 'last_name',
                'type': 'text'
            },
            {
                'name': 'Phone Number',
                'value': 'phone',
                'type': 'number'
            },
            {
                'name': 'Mobile Number',
                'value': 'mobile',
                'type': 'number'
            },
            {
                'name': 'Email',
                'value': 'email',
                'type': 'email'
            },
            {
                'name': 'Alternate Email',
                'value': 'email_alt',
                'type': 'email'
            },
            {
                'name': 'Marrital Status',
                'value': 'marital_status',
                'type': 'select',
                'options': ['Single', 'Married']
            },
            {
                'name': 'Gender',
                'value': 'gender',
                'type': 'select',
                'options': Candidate.GENDER_LIST
            },
            {
                'name': 'Date of Birth',
                'value': 'date_of_birth',
                'type': 'date'
            },
            {
                'name': 'Last Applied',
                'value': 'last_applied',
                'type': 'datetime'
            },
            {
                'name': 'Street',
                'value': 'street',
                'type': 'text'
            },
            {
                'name': 'Pincode',
                'value': 'pincode',
                'type': 'number'
            },
            {
                'name': 'City',
                'value': 'city',
                'type': 'text'
            },
            {
                'name': 'State',
                'value': 'state',
                'type': 'state'
            },
            {
                'name': 'Country',
                'value': 'country',
                'type': 'country'
            },
            {
                'name': 'Age',
                'value': 'age',
                'type': 'number'
            },
            {
                'name': 'Experience in years',
                'value': 'exp_years',
                'type': 'number'
            },
            {
                'name': 'Experience in months',
                'value': 'exp_months',
                'type': 'number'
            },
            {
                'name': 'Highest Qualification',
                'value': 'qualification',
                'type': 'select',
                'options': Candidate.QUALIFICATION_LIST
            },
            {
                'name': 'Current Job',
                'value': 'cur_job',
                'type': 'text'
            },
            {
                'name': 'Current Job',
                'value': 'cur_job',
                'type': 'text'
            },
            {
                'name': 'Current Employer',
                'value': 'cur_employer',
                'type': 'text'
            },
            {
                'name': 'Certifications',
                'value': 'certifications',
                'type': 'text'
            },
            {
                'name': 'Functional Area',
                'value': 'fun_area',
                'type': 'text'
            },
            {
                'name': 'Subjects',
                'value': 'subjects',
                'type': 'text'
            },
            {
                'name': 'Skills',
                'value': 'skills',
                'type': 'text'
            },
            {
                'name': 'Resume',
                'value': 'resume',
                'type': 'file'
            }
        ]
    }     

def getModulesTypesJob(request):
    module_type = request.GET.get('moduleType', None)  # New line to get module_type
    id = request.GET.get('id', None)  # New line to get module_type
    company = Job.objects.values_list('company', flat=True).get(id=id)

    if module_type:  # Check if module_type is provided
        modules = Module.objects.filter(company=company, module_type=module_type).last()  # Filter by module_type
        serializer = ModuleSerializer(modules)
    else:
        modules = Module.objects.filter(company=company)  # Get all modules for the company
        serializer = ModuleSerializer(modules, many=True)
    
    return {
        'code': 200,
        'data': serializer.data
    }

def getContacts(request):
    company = Company.getByUser(request.user)

    id = request.GET.get('id', None)

    if id:
        contact = Contacts.getById(id, company)
        if not contact:
            return {
                'code': 400,
                'msg': 'Form not found'
            }
        serializer = ContactsDataSerializer(contact)

    else:
        user = request.user
        if user.is_superuser:
            contacts = Contacts.objects.all()
        else:
            contacts = Contacts.objects.filter(company__id=user.company_id)
            
        serializer = ContactsDataSerializer(contacts, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }    

def saveContacts(request):

    company = Company.getByUser(request.user)    
    
    data = request.data 
    id = data.get('id', None)
    name = data.get('name', None)
    mobile = data.get('mobile', None)    
    email = data.get('email', None)

    # For update function
    if id:  
        # See whatever data is coming, else ryuk cries :)
        contact = Contacts.getById(id, company)
        if not contact:
            return{
                'code': 400,
                'msg': 'Contact not found'
            }
        if name: 
            contact.name = name
        if mobile: 
            contact.mobile = mobile
        if email: 
            contact.email = email
    
    # For creating new contact
    else:
        if mobile and Contacts.getByMobile(mobile,company):
            return{
                    'code': 400,
                    'msg': 'Contact already exists with same mobile number'
                }
        if email and Contacts.getByEmailId(email,company):
            return{
                    'code': 400,
                    'msg': 'Contact already exists with same email'
                }
        contact = Contacts()
        contact.company = company
        contact.name = name
        contact.mobile = mobile
        contact.email = email
    
    # Save changes
    contact.save()
    
    return {
        'code': 200,
        'msg': 'Contact saved successfully!'
    }
    

        

def deleteContacts(request):
    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        contact = Contacts.getById(id, company)

        if not contact:
            return {
                'code': 400,
                'msg': 'Contact not found'
            }

        contact.delete()
        return {
            'code': 200,
            'msg': 'Contact deleted succesfully!',
        }

    return {
        'code': 400,
        'msg': 'Invalid request'
    }


def Update(request):

    company = Company.getByUser(request.user)    
    
    data = request.data 
    id = data.get('id', None)
    name = data.get('name', None)
    mobile = data.get('mobile', None)    
    email = data.get('email', None)

    # For update function
    if id:  
        # See whatever data is coming, else ryuk cries :)
        contact = Contacts.getById(id, company)
        if not contact:
            return{
                'code': 400,
                'msg': 'Contact not found'
            }
        if name: 
            contact.name = name
        if mobile: 
            contact.mobile = mobile
        if email: 
            contact.email = email
    
        contact = Contacts()
        contact.company = company
        contact.name = name
        contact.mobile = mobile
        contact.email = email
    
    # Save changes
    contact.save()
    
    return {
        'code': 200,
        'msg': 'Contact updated successfully!'
    }    

def getTemplateVariables(request):
    company = Company.getByUser(request.user)
    template_variables = TemplateVariables.getForCompany(company)
    serializer = TemplateVariablesSerializer(template_variables, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }

def saveTemplateVariables(request):
    company = Company.getByUser(request.user)
    data = request.data

    value = data.get('value', None)
    
    if id:
        template_variable = TemplateVariables.getById(id, company)
        if not template_variable:
            return {
                'code': 400,
                'msg': 'Template variable not found'
            }
        if value:
            template_variable.value = value

    else:
        return {
            'code': 400,
            'msg': 'Template variable not found'
        } 
    
    template_variable.save()
    
    return {
        'code': 200,
        'msg': 'Template variable saved successfully!'
    }
    
from decimal import Decimal
from settings.models import PlanPricing, Subscription

# def getBillingPlans(request):
#     from django.db.models import Prefetch
    
#     # Get all active plans with their pricings and billing cycles
#     plans = Plan.objects.filter(is_active=True).prefetch_related(
#         Prefetch('prices', queryset=PlanPricing.objects.select_related('billing_cycle'))
#     )
    
#     response_data = []
    
#     for plan in plans:
#         plan_data = {
#             'id': plan.id,
#             'name': plan.name,
#             'description': plan.description,
#             'is_active': plan.is_active,
#             'pricings': []
#         }
        
#         # Add all available pricing options for this plan
#         for pricing in plan.prices.all():
#             new_price = pricing.price
#             if pricing.offer:
#                 try:
#                     offer_percentage = Decimal(pricing.offer)
#                     new_price = pricing.price * (1 - offer_percentage / Decimal(100))
#                     new_price = int(new_price) + Decimal('0.99')
#                 except (ValueError, TypeError):
#                     pass  # Use original price if offer is invalid

#             plan_data['pricings'].append({
#                 'id': pricing.id,
#                 'billing_cycle': {
#                     'id': pricing.billing_cycle.id,
#                     'name': pricing.billing_cycle.name,
#                     'duration_months': pricing.billing_cycle.duration_in_months
#                 },
#                 'price': str(new_price),
#                 'original_price': str(pricing.price) if pricing.price else None,
#                 'offer': pricing.offer
#             })
            
#         response_data.append(plan_data)
        
#     return {
#         'code': 200,
#         'data': response_data
#     }
    
def getBillingPlans(request):
    from django.db.models import Prefetch
    
    # Get all active plans with their pricings and features
    plans = Plan.objects.filter(is_active=True).prefetch_related(
        Prefetch('prices', queryset=PlanPricing.objects.select_related('billing_cycle')),
        Prefetch('feature_limits', queryset=PlanFeatureCredit.objects.select_related('feature'))
    )
    
    response_data = []
    
    for plan in plans:
        plan_data = {
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'is_active': plan.is_active,
            'pricings': [],
            # 'features': []
        }
        
        # Add all available pricing options for this plan
        for pricing in plan.prices.all():
            new_price = pricing.price
            if pricing.offer:
                try:
                    offer_percentage = Decimal(pricing.offer)
                    new_price = pricing.price * (1 - offer_percentage / Decimal(100))
                    new_price = int(new_price) + Decimal('0.99')
                except (ValueError, TypeError):
                    pass  # Use original price if offer is invalid

            plan_data['pricings'].append({
                'id': pricing.id,
                'billing_cycle': {
                    'id': pricing.billing_cycle.id,
                    'name': pricing.billing_cycle.name,
                    'duration_months': pricing.billing_cycle.duration_in_months
                },
                'price': str(new_price),
                'original_price': str(pricing.price) if pricing.price else None,
                'offer': pricing.offer
            })
            
        # Add only feature names for this plan
        # plan_data['features'] = [
        #     {
        #         'name': plan_feature.feature.name
        #     } for plan_feature in plan.feature_limits.all()
        # ]
        # plan_data['features'] = [
        #     {
        #         'name': plan_feature.feature.name,
        #         'feature_usages': [
        #             {'name': usage.name}
        #             for usage in plan_feature.feature.featureusage_set.all()
        #         ] if hasattr(plan_feature.feature, 'featureusage_set') else []
        #     } for plan_feature in plan.feature_limits.all()
        # ]
            
        response_data.append(plan_data)
        
    return {
        'code': 200,
        'data': response_data
    }

def getCurrentSubscription(request):
    try:
        subscription = Subscription.objects.select_related(
            'plan_pricing',
            'plan_pricing__plan',
            'plan_pricing__billing_cycle',
            'company'
        ).filter(company=request.user.company_id, is_active=True).first()
        
        plan_pricing = subscription.plan_pricing
        if not plan_pricing:
            return None
            
        # Calculate offer price if applicable
        price = plan_pricing.price or Decimal('0')
        offer_price = None
        offer_percentage = None
        
        if plan_pricing.offer:
            try:
                offer_percentage = Decimal(plan_pricing.offer)
                if offer_percentage > 0 and price:
                    offer_price = price * (1 - offer_percentage / Decimal(100))
                    offer_price = int(offer_price) + Decimal('0.99')
            except (ValueError, TypeError):
                pass
        
        # If no valid offer price, use the regular price
        if offer_price is None and price:
            offer_price = int(price) + Decimal('0.99')
        
        # Prepare the response data
        response_data = {
            'code': 200,
            'data': {
                'id': subscription.id,
                'plan': {
                    'id': plan_pricing.plan.id,
                    'name': plan_pricing.plan.name,
                    'description': plan_pricing.plan.description
                },
                'billing_cycle': {
                    'id': plan_pricing.billing_cycle.id,
                    'name': plan_pricing.billing_cycle.name,
                    'duration_months': plan_pricing.billing_cycle.duration_in_months
                },
                'price': str(price) if price is not None else None,
                'offer_price': str(offer_price) if offer_price is not None else None,
                'offer_percentage': str(offer_percentage) if offer_percentage is not None else None,
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
                'is_active': subscription.is_active,
                'company_id': subscription.company.id if subscription.company else None
            }
        }
        
        return response_data
    except Subscription.DoesNotExist:
        return {'code': 404, 'message': 'No active subscription found'}
    except Exception as e:
        return {'code': 500, 'message': f'Error fetching subscription: {str(e)}'}
    
    
def getDesignationsCareer(request):

    designation = Designation.objects.all()

    serializer = DesignationSerializer(designation, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }    

def getDegreesCareer(request):

    degrees = Degree.objects.all()
    serializer = DegreeSerializer(degrees, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }     
    
def getEmailCredentials(request):
    email_credentials = EmailCredential.objects.all()
    serializer = EmailCredentialsSerializer(email_credentials, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }
    
def getOrganizationalEmails(request):
    company = Company.getByUser(request.user)
    organizational_emails = OrganizationalEmail.objects.filter(company=company)
    
    # Add email filtering if email parameter is provided
    email = request.GET.get('email')
    if email:
        organizational_emails = organizational_emails.filter(email__icontains=email)
    
    serializer = OrganizationalEmailSerializer(organizational_emails, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }

def saveOrganizationalEmail(request):
    company = Company.getByUser(request.user)
    data = request.data
    data["company"] =company.id
    # if organizational_email:
    serializer = OrganizationalEmailSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return serializer.data
    return serializer.errors

def deleteOrganizationalEmail(request,id):
    organizationalEmail=OrganizationalEmail.objects.get(id=id)
    organizationalEmail.delete()
    return status.HTTP_200_OK

def saveUnsubscribeEmailTokenLink(request, token):
    unsubscribe_link = UnsubscribeEmailToken.getByToken(token)
    if unsubscribe_link:
        unsubscribe_link.candidate.unsubscribe_link = True
        unsubscribe_link.candidate.save()
        unsubscribe_link.delete()
        return status.HTTP_200_OK
    return status.HTTP_400_BAD_REQUEST

def getUnsubscribeLinks(request):
    company = Company.getByUser(request.user)
    unsubscribe_links = UnsubscribeLink.objects.get(company=company)
    serializer = UnsubscribeLinkSerializer(unsubscribe_links)
    return serializer.data

@staticmethod
@check_feature_availability("unsubscribe_link")
def saveUnsubscribeLink(self,request):
    
    company = Company.getByUser(request.user)
    unsubscribe_link = UnsubscribeLink.objects.filter(company=company).last()
    data = request.data
    # body = data.get('body', None)
    data["company"] =company.id
    if unsubscribe_link:
        serializer = UnsubscribeLinkSerializer(data=data,instance=unsubscribe_link)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        return serializer.errors
    else:
        # unsubscribe_link = UnsubscribeLink.objects.create(company=company, body=body)
        serializer = UnsubscribeLinkSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        return serializer.errors
   
def getAttachmentCategories(request):
    """
    Get attachment categories and subcategories for email templates
    """
    from .models import EmailTemplate
    
    # Get categories
    categories = [
        {
            'value': choice[0],
            'label': choice[1]
        }
        for choice in EmailTemplate.ATTACHMENT_CATEGORY_CHOICES
    ]
    
    # Get subcategories
    subcategories = [
        {
            'value': choice[0],
            'label': choice[1]
        }
        for choice in EmailTemplate.ATTACHMENT_SUBCATEGORY_CHOICES
    ]
    
    data = {
        'categories': categories,
        'subcategories': subcategories
    }
    
    return {
        'code': 200,
        'data': data
    }
   