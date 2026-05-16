from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from intern.models import Categorie, EtudeStagiaire, Stagiaire, Entreprise # Import Entreprise
from training.models import Filiere, Formation, Service
from progress.models import Action, DetailAction # Import Action and DetailAction

class StagiaireListView(ListView):
    context_object_name = "stagiaire_list"
    queryset = Stagiaire.objects.all()
    paginate_by = 5
    template_name = "intern/stagiaires.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['link'] = "stagiaires"
        return ctx

class StagiaireDetailView(DetailView):
    model = Stagiaire
    template_name = "intern/stagiaire.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stagiaires'] = Stagiaire.objects.all()
        ctx['categories'] = Categorie.objects.all()
        # ctx['services'] = Service.objects.all() # Removed
        # ctx['filieres'] = Filiere.objects.select_related('service').all() # Removed
        ctx['entreprises'] = Entreprise.objects.all() # Add enterprises to context
        
        # Fetch DetailAction objects for the current stagiaire
        current_stagiaire = self.get_object()
        ctx['actions_suivies'] = DetailAction.objects.filter(stagiaire=current_stagiaire).select_related('action__formation').order_by('action__date_debut')

        ctx['titre'] = "Voir"
        return ctx


class StagiaireCreateView(View):
    def get(self, request):
        ctx = {
            "categories": Categorie.objects.all(),
            # "services": Service.objects.all(), # Removed
            # "filieres": Filiere.objects.select_related('service').all(), # Removed
            "entreprises": Entreprise.objects.all(), # Add enterprises to context
            "titre" : "Saisie d'un stagiaire",
            "mode" : "new"
        }
        return render(request, 'intern/stagiaire.html', ctx)
    
    def post(self, request):
        nom = request.POST['nom']
        postnom = request.POST['postnom']
        prenom = request.POST['prenom']
        adresse = request.POST['adresse']
        sexe = request.POST['sexe']
        telephone = request.POST['telephone']
        email = request.POST.get('email') or None
        date_naissance = request.POST.get('date_naissance') or None
        lieu_naissance = request.POST.get('lieu_naissance') or None
        nationalite = request.POST.get('nationalite') or None
        type_piece = request.POST.get('type_piece') or None # New field
        numero_piece = request.POST.get('numero_piece') or None
        nom_pere = request.POST.get('nom_pere') or None
        nom_mere = request.POST.get('nom_mere') or None
        niveau_etude = request.POST.get('niveau_etude') or None
        id_categorie = request.POST['categorie']
        # id_service = request.POST.get('service') or None # Removed
        # id_filiere = request.POST.get('filiere') or None # Removed
        photo = request.FILES.get('photo')

        # Fetch the Categorie object to check its title
        categorie_obj = Categorie.objects.get(id=id_categorie)

        stagiaire = Stagiaire(
            nom = nom,
            postnom = postnom,
            prenom = prenom,
            adresse = adresse,
            sexe = sexe,
            telephone = telephone,
            email = email,
            date_naissance = date_naissance,
            lieu_naissance = lieu_naissance,
            nationalite = nationalite,
            type_piece = type_piece, # Assign new field
            numero_piece = numero_piece,
            nom_pere = nom_pere,
            nom_mere = nom_mere,
            niveau_etude = niveau_etude,
            photo = photo,
            categorie_id = id_categorie,
            # service_id = id_service, # Removed
            # filiere_id = id_filiere, # Removed
        )

        # Conditionally handle new fields if category is "dans l'emploi"
        if categorie_obj.titre == "dans l'emploi":
            entreprise_id = request.POST.get('entreprise')
            stagiaire.entreprise_id = entreprise_id if entreprise_id else None
            stagiaire.fonction = request.POST.get('fonction') or None
            anciennete_emploi = request.POST.get('anciennete_emploi')
            stagiaire.anciennete_emploi = int(anciennete_emploi) if anciennete_emploi else None
            anciennete_entreprise = request.POST.get('anciennete_entreprise')
            stagiaire.anciennete_entreprise = int(anciennete_entreprise) if anciennete_entreprise else None
        else:
            # Ensure these fields are cleared if category changes from "dans l'emploi"
            stagiaire.entreprise = None
            stagiaire.fonction = None
            stagiaire.anciennete_emploi = None
            stagiaire.anciennete_entreprise = None


        stagiaire.save()

        etude_intitules = request.POST.getlist('etude_intitule[]')
        etude_etablissements = request.POST.getlist('etude_etablissement[]')
        etude_niveaux = request.POST.getlist('etude_niveau[]')
        etude_annee_debuts = request.POST.getlist('etude_annee_debut[]')
        etude_annee_fins = request.POST.getlist('etude_annee_fin[]')
        etude_diplomes = request.POST.getlist('etude_diplome[]')
        etude_descriptions = request.POST.getlist('etude_description[]')

        for index, intitule in enumerate(etude_intitules):
            intitule = (intitule or '').strip()
            if not intitule:
                continue

            annee_debut = etude_annee_debuts[index].strip() if index < len(etude_annee_debuts) else ''
            annee_fin = etude_annee_fins[index].strip() if index < len(etude_annee_fins) else ''

            EtudeStagiaire.objects.create(
                stagiaire=stagiaire,
                intitule=intitule,
                etablissement=etude_etablissements[index].strip() if index < len(etude_etablissements) else None,
                niveau=etude_niveaux[index].strip() if index < len(etude_niveaux) else None,
                annee_debut=int(annee_debut) if annee_debut else None,
                annee_fin=int(annee_fin) if annee_fin else None,
                diplome_obtenu=etude_diplomes[index].strip() if index < len(etude_diplomes) else None,
                description=etude_descriptions[index].strip() if index < len(etude_descriptions) else None,
            )

        return HttpResponseRedirect("/intern/stagiaires")
