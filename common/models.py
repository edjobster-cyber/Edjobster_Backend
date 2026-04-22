from django.db import models
from django.contrib.postgres.fields import ArrayField

from common.file_utils import CompanyFileStorage, company_banner_path

class CompanyTags(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=1000, null=True, blank=True, default=None)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)[:20]

    class Meta:
        verbose_name = 'Company Tag'
        verbose_name_plural = 'Company Tags'

    @staticmethod
    def getById(id):
        if CompanyTags.objects.filter(id=id).exists():
            return CompanyTags.objects.get(id=id)
        return None

    @staticmethod
    def getAll():
        return CompanyTags.objects.all()



class Country(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)[:20]

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    @staticmethod
    def getById(countryId):
        if Country.objects.filter(id=countryId).exists():
            return Country.objects.get(id=countryId)
        return None

    @staticmethod
    def getAll():
        return Country.objects.all()


class State(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    country = models.ForeignKey(
        Country, default=1, verbose_name='Country', on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)[:20]

    class Meta:
        verbose_name = 'State'
        verbose_name_plural = 'States'

    @staticmethod
    def getById(stateId):
        if State.objects.filter(id=stateId).exists():
            return State.objects.get(id=stateId)
        return None

    @staticmethod
    def getAll():
        return State.objects.all()

    @staticmethod
    def getByCountry(id):
        country = Country.getById(id)
        if country:
            return State.objects.filter(country=country)
        return []
    
    @staticmethod
    def search(query):
        return State.objects.filter(name=query)


class City(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    state = models.ForeignKey(
        State, default=1, verbose_name='State', on_delete=models.CASCADE)
    pincodes = ArrayField(models.CharField(
        max_length=6, blank=True), default=list)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id) + ":" + str(self.name)[:20]

    class Meta:
        verbose_name = 'City'
        verbose_name_plural = 'Cities'

    @staticmethod
    def getById(cityId):
        if City.objects.filter(id=cityId).exists():
            return City.objects.get(id=cityId)
        return None

    @staticmethod
    def getAll():
        return City.objects.all()

    @staticmethod
    def getBycountryId(countryId):
        if City.objects.filter(id=countryId).exists():
            return City.objects.get(id=countryId)
        return None

    @staticmethod
    def getBystateId(stateId):
        if City.objects.filter(id=stateId).exists():
            return City.objects.get(id=stateId)
        return None

    @staticmethod
    def getByState(id):
        state = State.getById(id)
        if state:
            return City.objects.filter(state=state)
        return []
    
    @staticmethod
    def search(query):
        return City.objects.filter(name=query)


class NoteType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    icon = models.ImageField(
        upload_to='media/data/icons', default=None, null=True, blank=True)
    # icon = models.ImageField(
    #     upload_to='companies/icons',
    #     storage=CompanyFileStorage(),
    #     default=None,
    #     null=True,
    #     blank=True
    # )
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)[:20]

    class Meta:
        verbose_name = 'NoteType'
        verbose_name_plural = 'NoteTypes'

    @staticmethod
    def getById(id):
        if NoteType.objects.filter(id=id).exists():
            return NoteType.objects.get(id=id)
        return None

    @staticmethod
    def getAll():
        return NoteType.objects.all()
