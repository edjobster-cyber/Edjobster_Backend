from rest_framework import serializers
from .models import Country, NoteType, State, City, CompanyTags
from django.conf import settings

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']


class CompanyTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyTags
        fields = ['id', 'name']


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'pincodes']


class NoteTypeSerializer(serializers.ModelSerializer):

    icon = serializers.SerializerMethodField()

    class Meta:
        model = NoteType
        fields = ['id', 'name', 'icon']

    def get_icon(self, obj):
        if obj.icon:
            return settings.NOTE_ICON_FILE_URL+obj.icon.name[17:]
        return None                      