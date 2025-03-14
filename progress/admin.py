from django.contrib import admin

from progress.models import  Formateur,TypeAction,Action,DetailAction

admin.site.register(Formateur)
admin.site.register(TypeAction)
admin.site.register(Action)
admin.site.register(DetailAction)
