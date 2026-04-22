from django.contrib import admin

from .models import Country, State, City, NoteType, CompanyTags
my_modules = [Country, State, City, NoteType, CompanyTags]

admin.site.register(my_modules)