from django.db import models
import uuid

class ContactDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile_number = models.BigIntegerField(unique=True)
    company_name = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    platform = models.CharField(max_length=255, blank=True)
    Jd_create = models.IntegerField(default=1)
    unsubscribe = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ScheduleCall(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255,null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    mobile_number = models.BigIntegerField(unique=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    platform = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    