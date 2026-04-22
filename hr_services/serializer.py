from rest_framework import serializers

from .models import ContactDetails, ScheduleCall


class ContactDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactDetails
        fields = '__all__'


class ScheduleCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleCall
        fields = '__all__'
    