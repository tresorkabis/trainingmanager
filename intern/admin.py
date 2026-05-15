from django.contrib import admin

from intern.models import Categorie, EtudeStagiaire, Stagiaire


class EtudeStagiaireInline(admin.TabularInline):
    model = EtudeStagiaire
    extra = 1


@admin.register(Stagiaire)
class StagiaireAdmin(admin.ModelAdmin):
    list_display = (
        'nom',
        'postnom',
        'prenom',
        'service',
        'filiere',
        'formation',
        'telephone',
        'email',
        'nationalite',
        'categorie',
        'active',
    )
    list_filter = ('active', 'sexe', 'categorie', 'service', 'filiere', 'formation', 'nationalite')
    search_fields = (
        'nom',
        'postnom',
        'prenom',
        'telephone',
        'email',
        'numero_piece',
    )
    inlines = [EtudeStagiaireInline]


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('titre', 'active', 'created_at')
    search_fields = ('titre',)


@admin.register(EtudeStagiaire)
class EtudeStagiaireAdmin(admin.ModelAdmin):
    list_display = ('stagiaire', 'intitule', 'niveau', 'etablissement', 'active')
    list_filter = ('active', 'niveau')
    search_fields = ('stagiaire__nom', 'stagiaire__postnom', 'intitule', 'etablissement')
