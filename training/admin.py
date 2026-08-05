from django.contrib import admin

from training.models import Filiere, Formation, Service

admin.site.register(Service)
admin.site.register(Filiere)


@admin.register(Formation) # Registered Formation
class FormationAdmin(admin.ModelAdmin): # Renamed from MetierAdmin
    list_display = ('nom', 'filiere', 'duree', 'duree_heures', 'cout', 'frais_participation', 'frais_jury', 'frais_materiels', 'active')
    list_filter = ('active', 'filiere')
    search_fields = ('nom', 'filiere__nom')