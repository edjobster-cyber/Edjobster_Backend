from rest_framework import serializers
from .models import (AddonPlan, Contacts, Location, Department, Designation, Degree, Pipeline, PipelineStage, 
    EmailCategory, EmailTemplate, EmailFields, Webform, Testimonials, TemplateVariables, Plan, 
    Payment, Subscription, EmailCredential, Module, UnsubscribeLink, OrganizationalEmail, 
    ShortLink, QRModel, LinkdingCompanyid, CandidateEvaluationCriteria, JobBoardList, JobBoard,
    CreditWallet, Feature, PlanFeatureCredit, CreditHistory, BilingHistory)
from account.serializer import AccountSerializer

class TemplateVariablesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateVariables
        fields = ['id', 'name', 'value']

class LocationSerializer(serializers.ModelSerializer):
    city_id = serializers.IntegerField(source='city.id')
    city_name = serializers.CharField(source='city.name')
    state_id = serializers.IntegerField(source='state.id')
    state_name = serializers.CharField(source='state.name')
    country_id = serializers.IntegerField(source='country.id')
    country_name = serializers.CharField(source='country.name')

    class Meta:
        model = Location
        fields = ['id',  'name', 'address', 'pincode', 'loc_lat', 'loc_lon', 'city_id', 'city_name', 'state_id', 'state_name',
                  'country_id', 'country_name', 'phone', 'email']


class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = ['id', 'name','company']

class DesignationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Designation
        fields = ['id', 'name', 'company']


class DegreeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Degree
        fields = ['id', 'name', 'company']

class PipelineStageSerializer(serializers.ModelSerializer):    
    class Meta:
        model = PipelineStage
        fields = "__all__"

    def get_pipeline(self, obj):
        if obj.pipeline:
            return PipelineSerializer(obj.pipeline).data
        return None 

class TestimonialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonials
        fields = "__all__"

    def get_testimonials(self, obj):
        if obj.testimonials:
            return TestimonialsSerializer(obj.testimonials).data
        return None 

class PipelineSerializer(serializers.ModelSerializer):
    stages = PipelineStageSerializer(many=True, read_only=True)
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'company','stages']
        depth = 2
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        stages = []
        for i in range(1, 8):
            stages.append(PipelineStageSerializer(getattr(instance, f"stage{i}")).data)
        representation['stages'] = stages
        return representation

class PipelineStagListSerializer(serializers.ModelSerializer):
    # pipeline = serializers.SerializerMethodField()
    
    class Meta:
        model = PipelineStage
        fields = ['id', 'name', 'status']
        depth = 2 

    def get_pipeline(self, obj):
        if obj.pipeline:
            return PipelineSerializer(obj.pipeline).data
        return None 

class EmailFieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailFields
        fields = ['name', 'value']

class EmailCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailCategory
        fields = ['id', 'name', 'company']



class EmailTemplateSerializer(serializers.ModelSerializer):

    category_id = serializers.IntegerField(source='category.id')
    category_name = serializers.CharField(source='category.name')

    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'company', 'from_email', 'reply_to', 'subject', 'message', 'type', 'category_id', 'category_name', 'add_signature', 'unsubscribe_link', 'attachment', 'attachment_category', 'attachment_subcategory', 'footer', 'created' , 'updated']

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = "__all__"

class WebformListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Webform
        fields = ['id','name', 'created', 'updated']

                                                                  
class WebformDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = Webform
        fields = ['id', 'name', 'form', 'created', 'updated']

class ContactsDataSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    class Meta:
        model = Contacts
        fields = ['id', 'name', 'email', 'mobile', 'company_name']

    def get_company_name(self, obj):
        if obj.company:
            return obj.company.name
        return None 
class BillingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'
    
class PaymentSerializer(serializers.ModelSerializer):
    plan_details = serializers.SerializerMethodField()
    addon_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ['id', 'payment_type', 'plan_pricing', 'addon_plan', 'razorpay_order_id', 
                 'razorpay_payment_id', 'razorpay_signature', 'amount', 'created_at',
                 'plan_details', 'addon_details']
    
    def get_plan_details(self, obj):
        if obj.plan_pricing:
            return {
                'id': obj.plan_pricing.plan.id,
                'name': obj.plan_pricing.plan.name,
                'description': obj.plan_pricing.plan.description,
                'billing_cycle': {
                    'id': obj.plan_pricing.billing_cycle.id,
                    'name': obj.plan_pricing.billing_cycle.name,
                    'duration_months': obj.plan_pricing.billing_cycle.duration_in_months
                }
            }
        return None
    
    def get_addon_details(self, obj):
        if obj.addon_plan:
            return {
                'id': obj.addon_plan.id,
                'name': obj.addon_plan.name,
                'description': obj.addon_plan.description,
                'credits': obj.addon_plan.credits,
                'feature': {
                    'id': obj.addon_plan.feature.id,
                    'name': obj.addon_plan.feature.name,
                    'code': obj.addon_plan.feature.code
                }
            }
        return None

class SubscriptionSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    plan = BillingPlanSerializer()
    class Meta:
        model = Subscription
        fields = '__all__'
        
class EmailCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailCredential
        fields = '__all__'

class UnsubscribeLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnsubscribeLink
        fields = '__all__'

class OrganizationalEmailSerializer(serializers.ModelSerializer):  
    class Meta:
        model = OrganizationalEmail
        fields = '__all'

class ShortLinkSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()

    class Meta:
        model = ShortLink
        fields = ['id', 'code', 'long_url', 'job', 'title', 'company', 'created_at']
        read_only_fields = ['code', 'created_at']
    
    def get_title(self, obj):
        if hasattr(obj, 'job') and obj.job and obj.job.dynamic_job_data:
            return obj.job.dynamic_job_data.get('Create Job', {}).get('title')
        return None

    def get_company(self, obj):
        if hasattr(obj, 'job') and obj.job and obj.job.company:
            return obj.job.company.name
        return None
        
class QRModelSerializer(serializers.ModelSerializer):
    qr_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = QRModel
        fields = ['id', 'url', 'job', 'qr_image', 'qr_image_url', 'created_at', 'updated_at']
        read_only_fields = ['qr_image', 'created_at', 'updated_at']
    
    def get_qr_image_url(self, obj):
        if obj.qr_image:
            return self.context['request'].build_absolute_uri(obj.qr_image.url)
        return None


class CandidateEvaluationCriteriaSerializer(serializers.ModelSerializer):
    """
    Serializer for CandidateEvaluationCriteria model
    """
    company_id = serializers.IntegerField(source='company.id', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = CandidateEvaluationCriteria
        fields = [
            'id', 'company', 'company_id', 'company_name', 'prompt',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_prompt(self, value):
        """
        Validate that the prompt is a valid JSON object
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Prompt must be a JSON object.")
        return value


class LinkdingCompanyidSerializer(serializers.ModelSerializer):
    """
    Serializer for LinkdingCompanyid model
    """
    company_id = serializers.IntegerField(source='company.id', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = LinkdingCompanyid
        fields = [
            'id', 'company', 'company_id', 'company_name', 'linkding_id', 
            'created_at', 'updated_at', 'is_active', 'metadata'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_linkding_id(self, value):
        """
        Validate that linkding_id is unique
        """
        if self.instance and self.instance.linkding_id == value:
            return value
            
        if LinkdingCompanyid.objects.filter(linkding_id=value).exists():
            raise serializers.ValidationError("A company with this Linkding ID already exists.")
        return value

class JobBoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for JobBoardList model
    """
    class Meta:
        model = JobBoardList
        fields = [
            'id', 'title', 'subtitle', 'logo', 'value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class JobBoardSerializer(serializers.ModelSerializer):
    """
    Serializer for JobBoard model
    """
    job_board_lists = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=JobBoardList.objects.all(),
        source='job_board_list'
    )

    class Meta:
        model = JobBoard
        fields = '__all__'

    def create(self, validated_data):
        job_board_lists = validated_data.pop('job_board_list', [])
        job_board = JobBoard.objects.create(**validated_data)
        job_board.job_board_list.set(job_board_lists)
        return job_board

    def update(self, instance, validated_data):
        job_board_lists = validated_data.pop('job_board_list', None)
        if job_board_lists is not None:
            instance.job_board_list.set(job_board_lists)
        return super().update(instance, validated_data)


class CreditWalletSerializer(serializers.ModelSerializer):
    """
    Serializer for CreditWallet model
    """
    available_credit = serializers.SerializerMethodField()
    feature_name = serializers.CharField(source='feature.name', read_only=True)
    feature_code = serializers.CharField(source='feature.code', read_only=True)

    class Meta:
        model = CreditWallet
        fields = [
            'id', 'feature', 'feature_name', 'feature_code', 
            'total_credit', 'used_credit', 'available_credit', 
            'isdayli', 'iscredit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'available_credit', 'isdayli', 'iscredit', 'created_at', 'updated_at']

    def get_available_credit(self, obj):
        return obj.total_credit - obj.used_credit

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = '__all__'

class AddonPlanSerializer(serializers.ModelSerializer):
    feature_name = serializers.CharField(source='feature.name', read_only=True)
    feature_code = serializers.CharField(source='feature.code', read_only=True)
    feature_price = serializers.DecimalField(source='feature.price',max_digits=10,decimal_places=2,read_only=True)
    
    class Meta:
        model = AddonPlan
        fields = ['id', 'feature', 'feature_name', 'feature_code', 'feature_price', 'name', 'description', 
                 'credits', 'price', 'offer_price', 'is_active', 'created_at', 'updated_at']

class PlanFeatureCreditSerializer(serializers.ModelSerializer):
    """
    Serializer for PlanFeatureCredit model
    """
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    feature_name = serializers.CharField(source='feature.name', read_only=True)
    feature_code = serializers.CharField(source='feature.code', read_only=True)
    iscredit = serializers.BooleanField(source='feature.iscredit', read_only=True)
    isdayli = serializers.BooleanField(source='feature.isdayli', read_only=True)
    iswithoutcredit = serializers.BooleanField(source='feature.iswithoutcredit', read_only=True)

    class Meta:
        model = PlanFeatureCredit
        fields = [
            'id', 'plan', 'plan_name', 'feature', 'feature_name', 'feature_code',
            'iscredit', 'isdayli', 'iswithoutcredit', 'credit_limit',"credit_limit", 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CreditHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for CreditHistory model
    """
    feature_name = serializers.CharField(source='feature.name', read_only=True)
    feature_code = serializers.CharField(source='feature.code', read_only=True)
    usage_name = serializers.CharField(source='feature_usage.name', read_only=True)
    usage_code = serializers.CharField(source='feature_usage.code', read_only=True)

    class Meta:
        model = CreditHistory
        fields = [
            'id', 'company', 'credit_wallet', 'feature', 'feature_name', 'feature_code',
            'feature_usage', 'usage_name', 'usage_code', 'credit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class BilingHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for BilingHistory model
    """
    plan_name = serializers.CharField(source='plan_pricing.plan.name', read_only=True)
    feature_name = serializers.CharField(source='feature.name', read_only=True)
    feature_code = serializers.CharField(source='feature.code', read_only=True)
    billing_cycle = serializers.CharField(source='plan_pricing.billing_cycle.name', read_only=True)

    class Meta:
        model = BilingHistory
        fields = [
            'id', 'company', 'plan_pricing', 'plan_name', 'feature', 'feature_name', 
            'feature_code', 'transaction_type', 'price', 'credit', 'billing_cycle',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']