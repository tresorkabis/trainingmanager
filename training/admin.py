from django.contrib import admin

from training.models import Filiere, Formation, Service

admin.site.register(Service)
admin.site.register(Filiere)
admin.site.register(Formation)