from rest_framework import serializers
from .models import Account, Company, CareerSiteCompanyDetail,CaptureLead
from settings.models import Department, Designation
from django.conf import settings
from django.contrib.auth.hashers import make_password
import logging

class AccountSerializer(serializers.ModelSerializer):

    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    def get_department(self, obj):
        if hasattr(obj, 'department') and obj.department:
            try:
                department = Department.getByDid(obj.department.id)
            except AttributeError:
                department = Department.getByDid(obj.department)
            if department:
                return department.name
        return None

    def get_designation(self, obj):    
        if hasattr(obj, 'designation'):
            designation = Designation.getByDid(obj.designation)
            if designation:
                return designation.name
        return None

    class Meta:
        model = Account
        fields = ['account_id', 'photo', 'first_name', 'last_name', 'role', 'company_id', 'mobile', 'email',
                  'is_active', 'verified', 'department', 'designation', 'is_trial', 'trial_start', 'trial_end']


    def get_photo(self, obj):
        # if 'photo' in obj:
        #     return obj['photo']
            # return settings.PHOTO_FILE_URL+obj['photo']['name'][19:]
        return None  


class CandidateSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'password', 'role', 'username','verified']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': False}  # We'll handle this in create method
        }

    def create(self, validated_data):
        # Ensure username is set to email if not provided
        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email']
            
        # Hash the password
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance

class CompanySerializer(serializers.ModelSerializer):

    admin_id = serializers.IntegerField(source='admin.id',allow_null=True)
    admin_first_name = serializers.CharField(source='admin.first_name',allow_null=True)
    admin_last_name = serializers.CharField(source='admin.last_name',allow_null=True)
    admin_email = serializers.CharField(source='admin.email',allow_null=True)

    city_id = serializers.IntegerField(source='city.id',allow_null=True)
    city_name = serializers.CharField(source='city.name',allow_null=True)
    state_id = serializers.IntegerField(source='city.state.id',allow_null=True)
    state_name = serializers.CharField(source='city.state.name',allow_null=True)
    country_id = serializers.IntegerField(source='city.state.country.id',allow_null=True)
    country_name = serializers.CharField(source='city.state.country.name',allow_null=True)
    # logo = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'logo', 'name', 'domain', 'website', 'email', 'description', 'admin_id', 'admin_first_name',
                  'admin_last_name', 'admin_email', 'phone', 'address', 'landmark', 'pincode', 'loc_lat', 'loc_lon', 'city_id', 'city_name', 'state_id', 'state_name',
                  'country_id', 'country_name', 'tag',"linkedin","twitter","facebook","instagram","banner",'sector']
    
    # def get_logo(self, obj):
    #     request = self.context.get('request')
    #     if obj.logo:
    #         return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url
    #     return None

class MemberSerializer(serializers.ModelSerializer):
    def validate_mobile(self, value):
        if Account.getByMobile(value):
           raise serializers.ValidationError("Mobile already exists")
        return value

    def validate_role(self, value):
        if value not in [Account.ADMIN, Account.USER]:
           raise serializers.ValidationError("Invalid role")
        return value
    
    def validate_email(self, value):
        if Account.getByEmail(value):
            raise serializers.ValidationError("Email already exists")
        return value
    
    class Meta:
        model = Account
        fields = [
            'first_name', 
            'last_name', 
            'mobile', 
            'email', 
            'role', 
            'username', 
            'department', 
            'designation',
            'addedBy', 
            'verified', 
            'company_id', 
            'photo',
            'password',
        ]

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    
class CareerSiteCompanyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerSiteCompanyDetail
        fields = '__all__'

class CaptureLeadSerializer(serializers.ModelSerializer):
        class Meta:
            model = CaptureLead
            fields = '__all__'