from django.contrib import admin

from intern.models import Categorie, EtudeStagiaire, Stagiaire, Entreprise


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
        # 'active',  # Removed 'active' from list_display
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
    fieldsets = (
        (None, {
            'fields': (
                ('nom', 'postnom', 'prenom'),
                ('sexe', 'telephone', 'email'),
                ('date_naissance', 'lieu_naissance', 'nationalite'),
                ('numero_piece', 'niveau_etude'),
                'adresse',
                'photo',
                ('categorie', 'service', 'filiere', 'formation'),
            )
        }),
        ('Informations professionnelles (si dans l\'emploi)', {
            'fields': (
                'entreprise',
                'fonction',
                ('anciennete_emploi', 'anciennete_entreprise'),
            ),
            'classes': ('collapse',), # Optional: collapse this section by default
        }),
        ('Statut', {
            'fields': ('active',),
            'classes': ('collapse',),
        }),
    )


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('titre', 'created_at') # Removed 'active'
    search_fields = ('titre',)


@admin.register(EtudeStagiaire)
class EtudeStagiaireAdmin(admin.ModelAdmin):
    list_display = ('stagiaire', 'intitule', 'niveau', 'etablissement') # Removed 'active'
    list_filter = ('niveau',) # Removed 'active'
    search_fields = ('stagiaire__nom', 'stagiaire__postnom', 'intitule', 'etablissement')


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'email', 'active', 'created_at')
    search_fields = ('nom', 'email', 'telephone')
