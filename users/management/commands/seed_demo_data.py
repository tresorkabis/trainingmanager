from datetime import date

from django.core.management import BaseCommand
from django.db import transaction

from intern.models import Categorie, EtudeStagiaire, Stagiaire, Entreprise, AutreFormation # Import AutreFormation
from progress.models import Action, DetailAction, Formateur, TypeAction
from training.models import Filiere, Formation, Module, Service
from users.models import Profile, User
from users.utils import createprofile


class Command(BaseCommand):
    help = "Peuple la base avec des donnees de demonstration coherentes."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Nettoyage des donnees existantes..."))
        # Supprimer les données existantes pour éviter les doublons et les conflits
        DetailAction.objects.all().delete()
        Action.objects.all().delete()
        Formateur.objects.all().delete()
        TypeAction.objects.all().delete()
        AutreFormation.objects.all().delete()
        EtudeStagiaire.objects.all().delete()
        Stagiaire.objects.all().delete()
        Entreprise.objects.all().delete()
        Module.objects.all().delete()
        Formation.objects.all().delete()
        Filiere.objects.all().delete()
        Service.objects.all().delete()
        User.objects.all().delete()
        Profile.objects.all().delete()
        Categorie.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Donnees nettoyees."))


        createprofile()
        manager_profile = Profile.objects.filter(name="Manager").first()
        chef_filiere_profile = Profile.objects.filter(name="Chef de filière").first()
        chef_service_profile = Profile.objects.filter(name="Chef de service").first()
        user_profile = Profile.objects.filter(name="User").first() # Assurez-vous que le profil "User" existe

        # Changement de demo.manager en manager
        manager_user, created = User.objects.get_or_create(
            username="manager", # Nom d'utilisateur changé ici
            defaults={
                "email": "manager@training.local", # Email mis à jour
                "first_name": "Demo",
                "last_name": "Manager",
                "profile": manager_profile,
            },
        )
        if created or not manager_user.check_password("demo"): # Mot de passe changé à "demo"
            manager_user.set_password("demo")
            manager_user.profile = manager_profile # Ensure profile is set even if user existed
            manager_user.save()

        # --- Ajout de la création du superutilisateur admin ---
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@training.local",
                "is_staff": True,
                "is_superuser": True,
                "profile": manager_profile, # Assigner un profil si nécessaire
            },
        )
        if created or not admin_user.check_password("demo"): # Mot de passe changé à "demo"
            admin_user.set_password("demo")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.profile = manager_profile # Assigner un profil si nécessaire
            admin_user.save()
        # --- Fin de l'ajout ---

        categories = {}
        # Updated categories as per user's request
        for titre in ["dans l'emploi", "sans emploi", "non défini"]:
            categorie, _ = Categorie.objects.get_or_create(titre=titre)
            categories[titre] = categorie

        services = {}
        for nom in ["Formation Continue", "Technique Industrielle", "Informatique", "Gestion Administrative"]:
            service, _ = Service.objects.get_or_create(nom=nom)
            services[nom] = service

        filieres = {}
        filiere_specs = [
            ("Electricite industrielle", "Technique Industrielle"),
            ("Maintenance des equipements", "Technique Industrielle"),
            ("Bureautique", "Informatique"),
            ("Gestion administrative", "Gestion Administrative"),
        ]
        for nom, service_nom in filiere_specs:
            filiere, _ = Filiere.objects.get_or_create(
                nom=nom,
                defaults={"service": services[service_nom]},
            )
            if filiere.service_id != services[service_nom].id:
                filiere.service = services[service_nom]
                filiere.save(update_fields=["service"])
            filieres[nom] = filiere

        # --- Ajout des utilisateurs Chef de filière et Chef de service ---
        chef_filiere_user, created = User.objects.get_or_create(
            username="chef.filiere",
            defaults={
                "email": "chef.filiere@training.local",
                "first_name": "Chef",
                "last_name": "Filiere",
                "profile": chef_filiere_profile,
                "filiere": filieres["Electricite industrielle"], # Assigner une filière
            },
        )
        if created or not chef_filiere_user.check_password("demo"): # Mot de passe changé à "demo"
            chef_filiere_user.set_password("demo")
            chef_filiere_user.profile = chef_filiere_profile
            chef_filiere_user.filiere = filieres["Electricite industrielle"]
            chef_filiere_user.save()

        chef_service_user, created = User.objects.get_or_create(
            username="chef.service",
            defaults={
                "email": "chef.service@training.local",
                "first_name": "Chef",
                "last_name": "Service",
                "profile": chef_service_profile,
                "service": services["Technique Industrielle"], # Assigner un service
            },
        )
        if created or not chef_service_user.check_password("demo"): # Mot de passe changé à "demo"
            chef_service_user.set_password("demo")
            chef_service_user.profile = chef_service_profile
            chef_service_user.service = services["Technique Industrielle"]
            chef_service_user.save()
        # --- Fin de l'ajout des utilisateurs Chef ---

        # Ajout d'un utilisateur standard
        standard_user, created = User.objects.get_or_create(
            username="user.standard",
            defaults={
                "email": "user.standard@training.local",
                "first_name": "Utilisateur",
                "last_name": "Standard",
                "profile": user_profile,
            },
        )
        if created or not standard_user.check_password("demo"):
            standard_user.set_password("demo")
            standard_user.profile = user_profile
            standard_user.save()

        # --- Début de la section Formateurs (déplacée plus haut) ---
        formateurs = {} # Initialiser le dictionnaire formateurs ici
        formateur_specs_data = [
            ("FM001", "Kabasele", "Mwamba", "Jean", "Kinshasa / Kintambo", "0817000001", "kabasele.demo@training.local", "Electricité"),
            ("FM002", "Ngoy", "Kabeya", "Marie", "Kinshasa / Limete", "0817000002", "ngoy.demo@training.local", "Informatique"),
            ("FM003", "Lwamba", "Kalala", "Pierre", "Lubumbashi / Kamalondo", "0971000003", "lwamba.demo@training.local", "Mécanique"),
            ("FM004", "Mufwankolo", "Nzuzi", "Sophie", "Kinshasa / Ngaliema", "0817000004", "mufwankolo.demo@training.local", "Gestion"),
            ("FM005", "Kazadi", "Mutombo", "Paul", "Kinshasa / Limete", "0817000005", "kazadi.demo@training.local", "Automatisme"),
        ]
        for matricule, nom, postnom, prenom, adresse, telephone, email, specialite in formateur_specs_data:
            formateur, _ = Formateur.objects.get_or_create(
                matricule=matricule,
                defaults={
                    "nom": nom,
                    "postnom": postnom,
                    "prenom": prenom, # Nouveau champ
                    "adresse": adresse,
                    "telephone": telephone,
                    "email": email,
                    "specialite": specialite, # Nouveau champ
                },
            )
            changed = False
            for field, value in {
                "nom": nom,
                "postnom": postnom,
                "prenom": prenom, # Nouveau champ
                "adresse": adresse,
                "telephone": telephone,
                "email": email,
                "specialite": specialite, # Nouveau champ
            }.items():
                if getattr(formateur, field) != value:
                    setattr(formateur, field, value)
                    changed = True
            if changed:
                formateur.save()
            formateurs[matricule] = formateur # Peupler le dictionnaire formateurs
        
        formateurs_list = list(formateurs.values()) # Créer la liste des objets Formateur
        if not formateurs_list:
            self.stdout.write(self.style.WARNING("Aucun formateur trouvé après création. Création de formateurs par défaut."))
            # Fallback si, pour une raison quelconque, formateurs_list est vide
            # Cela ne devrait pas arriver si les formateurs sont créés juste au-dessus
            formateur1, _ = Formateur.objects.get_or_create(matricule="FM001", defaults={"nom": "Kabasele", "postnom": "Mwamba", "prenom": "Jean", "adresse": "Kinshasa / Kintambo", "telephone": "0817000001", "email": "kabasele.demo@training.local", "specialite": "Electricité"})
            formateur2, _ = Formateur.objects.get_or_create(matricule="FM002", defaults={"nom": "Ngoy", "postnom": "Kabeya", "prenom": "Marie", "adresse": "Kinshasa / Limete", "telephone": "0817000002", "email": "ngoy.demo@training.local", "specialite": "Informatique"})
            formateurs_list = [formateur1, formateur2]
        # --- Fin de la section Formateurs ---

        formateur_index = 0 # Réinitialiser l'index pour l'assignation des modules

        formations = {}
        formation_specs = [
            {"nom": "Electricite batiment", "duree": 6, "filiere_nom": "Electricite industrielle", "frais_materiels": 120.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 1500.00, "modules": [("Fondamentaux électriques", "Notions de base et sécurité", 40), ("Installations domestiques", "Circuits et équipements du bâtiment", 80)]},
            {"nom": "Automatisme industriel", "duree": 8, "filiere_nom": "Electricite industrielle", "frais_materiels": 180.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 2000.00, "modules": [("API et capteurs", "Automates programmables et instrumentation", 60), ("Supervision", "Interfaces et contrôle industriel", 50)]},
            {"nom": "Maintenance preventive", "duree": 5, "filiere_nom": "Maintenance des equipements", "frais_materiels": 95.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 1200.00, "modules": [("Diagnostic", "Méthodes de contrôle et inspection", 35), ("Planification", "Organisation des maintenances périodiques", 25)]},
            {"nom": "Pack Office professionnel", "duree": 3, "filiere_nom": "Bureautique", "frais_materiels": 60.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 800.00, "modules": [("Word avancé", "Mise en forme et publipostage", 20), ("Excel métier", "Tableaux, formules et graphiques", 30)]},
            {"nom": "Secretaire de direction", "duree": 6, "filiere_nom": "Gestion administrative", "frais_materiels": 110.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 1300.00, "modules": [("Communication professionnelle", "Rédaction et accueil", 35), ("Organisation administrative", "Classement, agenda et suivi", 45)]},
        ]
        for spec in formation_specs:
            nom = spec["nom"]
            duree = spec["duree"]
            filiere_nom = spec["filiere_nom"]
            frais_materiels = spec["frais_materiels"]
            frais_participation = spec["frais_participation"]
            frais_jury = spec["frais_jury"]
            cout = spec["cout"]
            # duree_heures sera calculée à partir des modules

            formation, _ = Formation.objects.get_or_create(
                nom=nom,
                defaults={
                    "duree": duree,
                    "duree_heures": 0, # Initialiser à 0, sera mis à jour après les modules
                    "filiere": filieres[filiere_nom],
                    "cout": cout,
                    "frais_participation": frais_participation,
                    "frais_jury": frais_jury,
                    "frais_materiels": frais_materiels,
                    "active": True, # Explicitly set active
                },
            )
            changed = False
            if formation.filiere_id != filieres[filiere_nom].id:
                formation.filiere = filieres[filiere_nom]
                changed = True
            if formation.duree != duree:
                formation.duree = duree
                changed = True
            # if formation.duree_heures != duree_heures: # Cette ligne est supprimée car duree_heures est calculée
            #     formation.duree_heures = duree_heures
            #     changed = True
            if formation.cout != cout:
                formation.cout = cout
                changed = True
            if formation.frais_participation != frais_participation:
                formation.frais_participation = frais_participation
                changed = True
            if formation.frais_jury != frais_jury:
                formation.frais_jury = frais_jury
                changed = True
            if formation.frais_materiels != frais_materiels:
                formation.frais_materiels = frais_materiels
                changed = True
            if not formation.active: # Ensure it's active
                formation.active = True
                changed = True
            if changed:
                formation.save()
            
            Module.objects.filter(formation=formation).delete()
            
            total_duree_heures_for_formation = 0 # Initialiser le total pour cette formation
            for ordre, module_spec in enumerate(spec.get("modules", []), start=1):
                titre, description, duree_module_heures = module_spec # Renommé pour éviter conflit
                
                formateur_to_assign = formateurs_list[formateur_index % len(formateurs_list)]
                
                Module.objects.create(
                    formation=formation,
                    titre=titre,
                    description=description,
                    duree_heures=duree_module_heures,
                    formateur=formateur_to_assign,
                    ordre=ordre,
                )
                total_duree_heures_for_formation += duree_module_heures # Ajouter la durée du module
                formateur_index += 1 # Passer au formateur suivant pour le prochain module
            
            # Mettre à jour la durée en heures de la formation après la création de tous les modules
            if formation.duree_heures != total_duree_heures_for_formation:
                formation.duree_heures = total_duree_heures_for_formation
                formation.save(update_fields=['duree_heures'])

            formations[nom] = formation

        # Create demo Entreprise instances
        entreprises = {}
        entreprise_specs = [
            {"nom": "Global Tech Solutions", "adresse": "123 Rue de l'Innovation, Kinshasa", "telephone": "0811234567", "email": "contact@globaltech.com"},
            {"nom": "Alpha Consulting", "adresse": "45 Av. du Progrès, Lubumbashi", "telephone": "0978765432", "email": "info@alphaconsult.com"},
        ]
        for spec in entreprise_specs:
            entreprise, _ = Entreprise.objects.get_or_create(
                nom=spec["nom"],
                defaults={
                    "adresse": spec["adresse"],
                    "telephone": spec["telephone"],
                    "email": spec["email"],
                }
            )
            entreprises[spec["nom"]] = entreprise


        stagiaire_specs = [
            {
                "nom": "Mukendi",
                "postnom": "Kasongo",
                "prenom": "Aline",
                "sexe": "F",
                "telephone": "0991000001",
                "email": "aline.mukendi.demo@training.local",
                "categorie": "dans l'emploi", # Updated category
                "niveau_etude": "Diplome d'Etat",
                "adresse": "Kinshasa / Lemba",
                "nationalite": "Congolaise",
                "type_piece": "CE", # New field
                "numero_piece": "DEM-ST-001",
                "date_naissance": date(2001, 4, 12),
                "lieu_naissance": "Kinshasa",
                "nom_pere": "Jean Mukendi",
                "nom_mere": "Claire Kasongo",
                "etudes": [
                    {
                        "intitule": "Electricite generale",
                        "etablissement": "Institut Technique de Kinshasa",
                        "niveau": "Diplome d'Etat",
                        "annee_debut": 2017,
                        "annee_fin": 2020,
                        "diplome_obtenu": "Diplome d'Etat",
                    }
                ],
                "autres_formations": [ # Added other formations
                    {
                        "intitule": "Formation en Cybersécurité",
                        "etablissement": "Global Tech Academy",
                        "annee_fin": 2023,
                    }
                ],
                # New fields for "dans l'emploi"
                "entreprise_nom": "Global Tech Solutions",
                "fonction": "Technicien Électricien",
                "anciennete_emploi": 3,
                "anciennete_entreprise": 3,
                "photo": "stagiaires/photo5.jpg", # Placeholder photo
                "filiere_nom": "Electricite industrielle", # Ajout de la filière
            },
            {
                "nom": "Tshibangu",
                "postnom": "Mbuyi",
                "prenom": "Patrick",
                "sexe": "M",
                "telephone": "0991000002",
                "email": "patrick.tshibangu.demo@training.local",
                "categorie": "sans emploi", # Updated category
                "niveau_etude": "Graduat",
                "adresse": "Kinshasa / Ngaliema",
                "nationalite": "Congolaise",
                "type_piece": "PS", # New field
                "numero_piece": "DEM-ST-002",
                "date_naissance": date(1999, 9, 5),
                "lieu_naissance": "Matadi",
                "nom_pere": "Pierre Tshibangu",
                "nom_mere": "Jeanne Mbuyi",
                "etudes": [
                    {
                        "intitule": "Informatique de gestion",
                        "etablissement": "ISC Kinshasa",
                        "niveau": "Graduat",
                        "annee_debut": 2018,
                        "annee_fin": 2021,
                        "diplome_obtenu": "Graduat",
                    },
                    {
                        "intitule": "Comptabilite generale",
                        "etablissement": "Centre Polyvalent",
                        "niveau": "Certification",
                        "annee_debut": 2022,
                        "annee_fin": 2022,
                        "diplome_obtenu": "Attestation",
                    },
                ],
                "photo": "stagiaires/photo6.jpg", # Placeholder photo
                "filiere_nom": "Bureautique", # Ajout de la filière
            },
            {
                "nom": "Ilunga",
                "postnom": "Banza",
                "prenom": "Merveille",
                "sexe": "F",
                "telephone": "0991000003",
                "email": "merveille.ilunga.demo@training.local",
                "categorie": "non défini", # Updated category
                "niveau_etude": "Licence",
                "adresse": "Kinshasa / Gombe",
                "nationalite": "Congolaise",
                "type_piece": "PC", # New field
                "numero_piece": "DEM-ST-003",
                "date_naissance": date(1998, 1, 20),
                "lieu_naissance": "Lubumbashi",
                "nom_pere": "Andre Ilunga",
                "nom_mere": "Solange Banza",
                "etudes": [
                    {
                        "intitule": "Sciences commerciales",
                        "etablissement": "Universite de Kinshasa",
                        "niveau": "Licence",
                        "annee_debut": 2017,
                        "annee_fin": 2022,
                        "diplome_obtenu": "Licence",
                    }
                ],
                "photo": "stagiaires/photo7.jpg", # Placeholder photo
                "filiere_nom": "Gestion administrative", # Ajout de la filière
            },
            {
                "nom": "Kabongo",
                "postnom": "Mwepu",
                "prenom": "David",
                "sexe": "M",
                "telephone": "0991000004",
                "email": "david.kabongo.demo@training.local",
                "categorie": "dans l'emploi",
                "niveau_etude": "Graduat",
                "adresse": "Kinshasa / Limete",
                "nationalite": "Congolaise",
                "type_piece": "CE", # New field
                "numero_piece": "DEM-ST-004",
                "date_naissance": date(1995, 7, 1),
                "lieu_naissance": "Kolwezi",
                "nom_pere": "Pierre Kabongo",
                "nom_mere": "Marie Mwepu",
                "etudes": [
                    {
                        "intitule": "Maintenance Industrielle",
                        "etablissement": "Institut Supérieur Technique",
                        "niveau": "Graduat",
                        "annee_debut": 2015,
                        "annee_fin": 2018,
                        "diplome_obtenu": "Graduat",
                    }
                ],
                "entreprise_nom": "Alpha Consulting",
                "fonction": "Technicien Électricien",
                "anciennete_emploi": 6,
                "anciennete_entreprise": 4,
                "photo": "stagiaires/photo1.jpg",
                "filiere_nom": "Maintenance des equipements", # Ajout de la filière
            },
            {
                "nom": "Nzuzi",
                "postnom": "Lunda",
                "prenom": "Grace",
                "sexe": "F",
                "telephone": "0991000005",
                "email": "grace.nzuzi.demo@training.local",
                "categorie": "sans emploi",
                "niveau_etude": "Diplome d'Etat",
                "adresse": "Kinshasa / Ngaliema",
                "nationalite": "Congolaise",
                "type_piece": "PS", # New field
                "numero_piece": "DEM-ST-005",
                "date_naissance": date(2000, 11, 25),
                "lieu_naissance": "Boma",
                "nom_pere": "Paul Nzuzi",
                "nom_mere": "Sophie Lunda",
                "etudes": [
                    {
                        "intitule": "Secrétariat Bureautique",
                        "etablissement": "Institut Technique Commercial",
                        "niveau": "Diplome d'Etat",
                        "annee_debut": 2016,
                        "annee_fin": 2019,
                        "diplome_obtenu": "Diplome d'Etat",
                    }
                ],
                "photo": "stagiaires/photo2.jpg",
                "filiere_nom": "Gestion administrative", # Ajout de la filière
            },
            {
                "nom": "Mbuyi",
                "postnom": "Kalala",
                "prenom": "Christian",
                "sexe": "M",
                "telephone": "0991000006",
                "email": "christian.mbuyi.demo@training.local",
                "categorie": "non défini",
                "niveau_etude": "Licence",
                "adresse": "Kinshasa / Kasa-Vubu",
                "nationalite": "Congolaise",
                "type_piece": "PC", # New field
                "numero_piece": "DEM-ST-006",
                "date_naissance": date(1997, 3, 8),
                "lieu_naissance": "Mbuji-Mayi",
                "nom_pere": "Jean Mbuyi",
                "nom_mere": "Marthe Kalala",
                "etudes": [
                    {
                        "intitule": "Gestion des Ressources Humaines",
                        "etablissement": "Université Pédagogique Nationale",
                        "niveau": "Licence",
                        "annee_debut": 2016,
                        "annee_fin": 2021,
                        "diplome_obtenu": "Licence",
                    }
                ],
                "photo": "stagiaires/photo3.jpg",
                "filiere_nom": "Gestion administrative", # Ajout de la filière
            },
            {
                "nom": "Lufuma",
                "postnom": "Nkumu",
                "prenom": "Esther",
                "sexe": "F",
                "telephone": "0991000007",
                "email": "esther.lufuma.demo@training.local",
                "categorie": "dans l'emploi",
                "niveau_etude": "Graduat",
                "adresse": "Kinshasa / Bandal",
                "nationalite": "Congolaise",
                "type_piece": "PS", # New field
                "numero_piece": "DEM-ST-007",
                "date_naissance": date(1999, 1, 15),
                "lieu_naissance": "Kisangani",
                "nom_pere": "Joseph Lufuma",
                "nom_mere": "Christine Nkumu",
                "etudes": [
                    {
                        "intitule": "Informatique Appliquée",
                        "etablissement": "Institut Supérieur de Commerce",
                        "niveau": "Graduat",
                        "annee_debut": 2017,
                        "annee_fin": 2020,
                        "diplome_obtenu": "Graduat",
                    }
                ],
                "entreprise_nom": "Global Tech Solutions",
                "fonction": "Assistante administrative",
                "anciennete_emploi": 2,
                "anciennete_entreprise": 2,
                "photo": "stagiaires/photo4.jpg",
                "filiere_nom": "Bureautique", # Ajout de la filière
            },
        ]

        stagiaires = {}
        for spec in stagiaire_specs:
            defaults = {
                "nom": spec["nom"],
                "postnom": spec["postnom"],
                "prenom": spec["prenom"],
                "adresse": spec["adresse"],
                "sexe": spec["sexe"],
                "telephone": spec["telephone"],
                "categorie": categories[spec["categorie"]],
                "date_naissance": spec["date_naissance"],
                "lieu_naissance": spec["lieu_naissance"],
                "nationalite": spec["nationalite"],
                "type_piece": spec["type_piece"], # New field
                "numero_piece": spec["numero_piece"],
                "nom_pere": spec["nom_pere"],
                "nom_mere": spec["nom_mere"],
                "niveau_etude": spec["niveau_etude"],
                "photo": spec["photo"], # New field
                "filiere": filieres[spec["filiere_nom"]], # Assigner la filière
            }

            # Add new fields to defaults if category is "dans l'emploi"
            if spec["categorie"] == "dans l'emploi":
                defaults["entreprise"] = entreprises[spec["entreprise_nom"]]
                defaults["fonction"] = spec["fonction"]
                defaults["anciennete_emploi"] = spec["anciennete_emploi"]
                defaults["anciennete_entreprise"] = spec["anciennete_entreprise"]
            else:
                # Ensure these fields are explicitly None if not "dans l'emploi"
                defaults["entreprise"] = None
                defaults["fonction"] = None
                defaults["anciennete_emploi"] = None
                defaults["anciennete_entreprise"] = None


            stagiaire, _ = Stagiaire.objects.get_or_create(
                email=spec["email"],
                defaults=defaults,
            )
            
            # Update logic for existing stagiaires
            changed = False
            for field, value in defaults.items():
                if field == "filiere": # Gérer la mise à jour de la filière
                    if getattr(stagiaire, field) != value:
                        setattr(stagiaire, field, value)
                        changed = True
                elif getattr(stagiaire, field) != value:
                    setattr(stagiaire, field, value)
                    changed = True
            if changed:
                stagiaire.save()


            EtudeStagiaire.objects.filter(stagiaire=stagiaire).delete()
            for etude in spec["etudes"]:
                EtudeStagiaire.objects.create(stagiaire=stagiaire, **etude)
            
            AutreFormation.objects.filter(stagiaire=stagiaire).delete()
            if "autres_formations" in spec:
                for autre_formation in spec["autres_formations"]:
                    AutreFormation.objects.create(stagiaire=stagiaire, **autre_formation)


            stagiaires[spec["email"]] = stagiaire


        type_actions = {}
        for code, libelle in [("PLAN", "Planification"), ("EXEC", "Execution"), ("EVAL", "Evaluation")]:
            type_action, _ = TypeAction.objects.get_or_create(code=code, defaults={"libelle": libelle})
            if type_action.libelle != libelle:
                type_action.libelle = libelle
                type_action.save(update_fields=["libelle"])
            type_actions[code] = type_action

        actions = {}
        action_specs = [
            {"description": "Session Electricite - Cohorte A", "date_debut": date(2026, 5, 20), "date_fin": date(2026, 11, 20), "formation_nom": "Electricite batiment", "formateur_matricules": ["FM001"]},
            {"description": "Pack Office - Vague Mai", "date_debut": date(2026, 5, 18), "date_fin": date(2026, 8, 18), "formation_nom": "Pack Office professionnel", "formateur_matricules": ["FM002"]},
            {"description": "Maintenance Preventive - Juin", "date_debut": date(2026, 6, 1), "date_fin": date(2026, 9, 1), "formation_nom": "Maintenance preventive", "formateur_matricules": ["FM001", "FM002"]}, # Corrected here
            {"description": "Secretaire de Direction - Sept", "date_debut": date(2026, 9, 1), "date_fin": date(2027, 3, 1), "formation_nom": "Secretaire de direction", "formateur_matricules": ["FM002"]},
            {"description": "Automatisme Avance - Juillet", "date_debut": date(2026, 7, 10), "date_fin": date(2026, 10, 10), "formation_nom": "Automatisme industriel", "formateur_matricules": ["FM001", "FM002"]},
        ]
        for spec in action_specs:
            formation_for_action = formations[spec["formation_nom"]] # Get the Formation object
            
            self.stdout.write(self.style.NOTICE(f"Processing Action: {spec['description']} for Formation: {formation_for_action.nom}"))

            action, created = Action.objects.get_or_create( # Use get_or_create for action
                description=spec["description"],
                defaults={
                    "date_debut": spec["date_debut"],
                    "date_fin": spec["date_fin"],
                    "formation": formation_for_action,
                },
            )
            
            # Update logic for existing actions (similar to formations and stagiaires)
            changed = False
            if action.date_debut != spec["date_debut"]:
                action.date_debut = spec["date_debut"]
                changed = True
            if action.date_fin != spec["date_fin"]:
                action.date_fin = spec["date_fin"]
                changed = True
            if action.formation_id != formation_for_action.id:
                action.formation = formation_for_action
                changed = True
            if changed:
                action.save()

            # --- MODIFIED LOGIC: Assign ALL formateurs from modules of the associated formation ---
            # Get formateurs assigned to modules of this specific formation
            formateurs_from_modules = Formateur.objects.filter(
                modules_dispenses__formation=formation_for_action
            ).distinct()
            
            # Convert to a list of Formateur objects
            assigned_formateurs_for_action = list(formateurs_from_modules)

            self.stdout.write(self.style.NOTICE(f"  Assigning Formateurs from modules for '{formation_for_action.nom}': {[str(f) for f in assigned_formateurs_for_action]}"))
            
            action.formateurs.set(assigned_formateurs_for_action)
            # --- END MODIFIED LOGIC ---

            actions[spec["description"]] = action

        detail_specs = [
            {"stagiaire_email": "aline.mukendi.demo@training.local", "action_description": "Session Electricite - Cohorte A", "statut": "Inscrit", "date_inscription": date(2026, 5, 1)},
            {"stagiaire_email": "patrick.tshibangu.demo@training.local", "action_description": "Pack Office - Vague Mai", "statut": "Terminé", "date_inscription": date(2026, 4, 25)},
            {"stagiaire_email": "merveille.ilunga.demo@training.local", "action_description": "Pack Office - Vague Mai", "statut": "En cours", "date_inscription": date(2026, 5, 10)},
            {"stagiaire_email": "david.kabongo.demo@training.local", "action_description": "Session Electricite - Cohorte A", "statut": "Inscrit", "date_inscription": date(2026, 5, 5)},
            {"stagiaire_email": "grace.nzuzi.demo@training.local", "action_description": "Pack Office - Vague Mai", "statut": "Abandon", "date_inscription": date(2026, 5, 2)},
            {"stagiaire_email": "christian.mbuyi.demo@training.local", "action_description": "Secretaire de Direction - Sept", "statut": "Inscrit", "date_inscription": date(2026, 8, 15)},
            {"stagiaire_email": "esther.lufuma.demo@training.local", "action_description": "Maintenance Preventive - Juin", "statut": "En cours", "date_inscription": date(2026, 5, 28)},
            {"stagiaire_email": "aline.mukendi.demo@training.local", "action_description": "Automatisme Avance - Juillet", "statut": "Inscrit", "date_inscription": date(2026, 6, 20)},
        ]
        for spec in detail_specs:
            DetailAction.objects.get_or_create(
                stagiaire=stagiaires[spec["stagiaire_email"]],
                action=actions[spec["action_description"]],
                defaults={
                    "statut": spec["statut"],
                    "date_inscription": spec["date_inscription"],
                }
            )

        self.stdout.write(self.style.SUCCESS("Donnees de demonstration generees avec succes."))
        self.stdout.write("Comptes de test:")
        self.stdout.write("  - Admin: admin / demo")
        self.stdout.write("  - Manager: manager / demo")
        self.stdout.write("  - Chef de filière: chef.filiere / demo")
        self.stdout.write("  - Chef de service: chef.service / demo")
        self.stdout.write("  - Utilisateur standard: user.standard / demo")