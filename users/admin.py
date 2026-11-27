from django.contrib import admin

from users.models import Profile, User, InstitutionSettings

admin.site.register(Profile)
admin.site.register(User)
admin.site.register(InstitutionSettings)
