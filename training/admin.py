from django.contrib import admin

from training.models import Filiere, Metier, Service # Changé Formation à Metier

admin.site.register(Service)
admin.site.register(Filiere)


@admin.register(Metier) # Changé Formation à Metier
class MetierAdmin(admin.ModelAdmin): # Changé FormationAdmin à MetierAdmin
    list_display = ('nom', 'filiere', 'duree', 'duree_heures', 'cout', 'frais_participation', 'frais_jury', 'frais_materiels', 'active')
    list_filter = ('active', 'filiere')
    search_fields = ('nom', 'filiere__nom')