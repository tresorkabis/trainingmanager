from datetime import date
import random # Pour générer des montants aléatoires
# import uuid # N'est plus nécessaire car la référence est générée par la méthode save du modèle

from django.core.management import BaseCommand
from django.db import transaction

from intern.models import Categorie, EtudeStagiaire, Stagiaire, Entreprise, AutreFormation
from progress.models import Action, DetailAction, Formateur, TypeAction, Paiement # Import Paiement
from training.models import Filiere, Formation, Module, Service
from users.models import Profile, User
from users.utils import createprofile


class Command(BaseCommand):
    help = "Peuple la base avec des donnees de demonstration coherentes."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Nettoyage des donnees existantes..."))
        # Supprimer les données existantes pour éviter les doublons et les conflits
        Paiement.objects.all().delete() # Ajout du nettoyage des paiements
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
        user_profile = Profile.objects.filter(name="User").first()
        formateur_profile = Profile.objects.filter(name="Formateur").first() # Récupérer le profil Formateur

        manager_user, created = User.objects.get_or_create(
            username="manager",
            defaults={
                "email": "manager@training.local",
                "first_name": "Demo",
                "last_name": "Manager",
                "profile": manager_profile,
            },
        )
        if created or not manager_user.check_password("demo"):
            manager_user.set_password("demo")
            manager_user.profile = manager_profile
            manager_user.save()

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@training.local",
                "is_staff": True,
                "is_superuser": True,
                "profile": manager_profile,
            },
        )
        if created or not admin_user.check_password("demo"):
            admin_user.set_password("demo")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.profile = manager_profile
            admin_user.save()

        categories = {}
        for titre in ["dans l'emploi", "sans emploi", "non défini"]:
            categorie, _ = Categorie.objects.get_or_create(titre=titre)
            categories[titre] = categorie

        services = {}
        for nom in ["Informatique", "Comptabilité et Administration", "Petites et moyennes entreprises"]:
            service, _ = Service.objects.get_or_create(nom=nom)
            services[nom] = service

        filieres = {}
        filiere_specs = [
            ("Bureautique", "Informatique"),
            ("Développement des plates-formes informatiques", "Informatique"),
            ("Administration système et réseaux", "Informatique"),
            ("Finances et Comptabilité", "Comptabilité et Administration"),
            ("Administration et Gestion", "Comptabilité et Administration"),
            ("Relations Publiques et Communication", "Comptabilité et Administration"),
            ("Logistique et Douane", "Petites et moyennes entreprises"),
            ("Gestion de projets", "Petites et moyennes entreprises"),
            ("Petites et Moyennes Entreprises (PME)", "Petites et moyennes entreprises"),
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

        chef_filiere_user, created = User.objects.get_or_create(
            username="chef.filiere",
            defaults={
                "email": "chef.filiere@training.local",
                "first_name": "Chef",
                "last_name": "Filiere",
                "profile": chef_filiere_profile,
                "filiere": filieres["Développement des plates-formes informatiques"],
            },
        )
        if created or not chef_filiere_user.check_password("demo"):
            chef_filiere_user.set_password("demo")
            chef_filiere_user.profile = chef_filiere_profile
            chef_filiere_user.filiere = filieres["Développement des plates-formes informatiques"]
            chef_filiere_user.save()

        chef_service_user, created = User.objects.get_or_create(
            username="chef.service",
            defaults={
                "email": "chef.service@training.local",
                "first_name": "Chef",
                "last_name": "Service",
                "profile": chef_service_profile,
                "service": services["Informatique"],
            },
        )
        if created or not chef_service_user.check_password("demo"):
            chef_service_user.set_password("demo")
            chef_service_user.profile = chef_service_profile
            chef_service_user.service = services["Informatique"]
            chef_service_user.save()

        # Nouvel utilisateur Formateur
        formateur_user, created = User.objects.get_or_create(
            username="formateur",
            defaults={
                "email": "formateur@training.local",
                "first_name": "Demo",
                "last_name": "Formateur",
                "profile": formateur_profile, # Assigner le profil Formateur
                "filiere": filieres["Développement des plates-formes informatiques"], # Correction ici: utiliser une filière existante
            },
        )
        if created or not formateur_user.check_password("demo"):
            formateur_user.set_password("demo")
            formateur_user.profile = formateur_profile
            formateur_user.filiere = filieres["Développement des plates-formes informatiques"] # Correction ici
            formateur_user.save()

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

        formateurs = {}
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
                    "prenom": prenom,
                    "adresse": adresse,
                    "telephone": telephone,
                    "email": email,
                    "specialite": specialite,
                },
            )
            changed = False
            for field, value in {
                "nom": nom,
                "postnom": postnom,
                "prenom": prenom,
                "adresse": adresse,
                "telephone": telephone,
                "email": email,
                "specialite": specialite,
            }.items():
                if getattr(formateur, field) != value:
                    setattr(formateur, field, value)
                    changed = True
            if changed:
                formateur.save()
            formateurs[matricule] = formateur
        
        formateurs_list = list(formateurs.values())
        if not formateurs_list:
            self.stdout.write(self.style.WARNING("Aucun formateur trouvé après création. Création de formateurs par défaut."))
            formateur1, _ = Formateur.objects.get_or_create(matricule="FM001", defaults={"nom": "Kabasele", "postnom": "Mwamba", "prenom": "Jean", "adresse": "Kinshasa / Kintambo", "telephone": "0817000001", "email": "kabasele.demo@training.local", "specialite": "Electricité"})
            formateur2, _ = Formateur.objects.get_or_create(matricule="FM002", defaults={"nom": "Ngoy", "postnom": "Kabeya", "prenom": "Marie", "adresse": "Kinshasa / Limete", "telephone": "0817000002", "email": "ngoy.demo@training.local", "specialite": "Informatique"})
            formateurs_list = [formateur1, formateur2]

        formateur_index = 0
        metiers = {}
        metier_specs = [
            {"nom": "Electricite batiment", "duree": 6, "type_formation": "qualifiante", "filiere_nom": "Développement des plates-formes informatiques", "frais_materiels": 120.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 1500.00, "modules": [("Fondamentaux électriques", "Notions de base et sécurité", 40), ("Installations domestiques", "Circuits et équipements du bâtiment", 80)]},
            {"nom": "Automatisme industriel", "duree": 8, "type_formation": "qualifiante", "filiere_nom": "Administration système et réseaux", "frais_materiels": 180.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 2000.00, "modules": [("API et capteurs", "Automates programmables et instrumentation", 60), ("Supervision", "Interfaces et contrôle industriel", 50)]},
            {"nom": "Maintenance preventive", "duree": 5, "type_formation": "continue", "filiere_nom": "Administration système et réseaux", "frais_materiels": 95.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 1200.00, "modules": [("Diagnostic", "Méthodes de contrôle et inspection", 35), ("Planification", "Organisation des maintenances périodiques", 25)]},
            {"nom": "Pack Office professionnel", "duree": 3, "type_formation": "continue", "filiere_nom": "Bureautique", "frais_materiels": 60.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 800.00, "modules": [("Word avancé", "Mise en forme et publipostage", 20), ("Excel métier", "Tableaux, formules et graphiques", 30)]},
            {"nom": "Secretaire de direction", "duree": 6, "type_formation": "continue", "filiere_nom": "Administration et Gestion", "frais_materiels": 110.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 1300.00, "modules": [("Communication professionnelle", "Rédaction et accueil", 35), ("Organisation administrative", "Classement, agenda et suivi", 45)]},
            {"nom": "Gestion de Projets PME", "duree": 4, "type_formation": "qualifiante", "filiere_nom": "Gestion de projets", "frais_materiels": 75.0, "frais_participation": 0.0, "frais_jury": 0.0, "cout": 950.00, "modules": [("Fondamentaux de la gestion de projet", "Initiation aux méthodes agiles", 30), ("Outils de planification", "MS Project et Trello", 40)]},
        ]
        for spec in metier_specs:
            nom = spec["nom"]
            duree = spec["duree"]
            type_formation = spec.get("type_formation", "qualifiante")
            filiere_nom = spec["filiere_nom"]
            frais_materiels = spec["frais_materiels"]
            frais_participation = spec["frais_participation"]
            frais_jury = spec["frais_jury"]
            cout = spec["cout"]

            metier, _ = Formation.objects.get_or_create(
                nom=nom,
                defaults={
                    "duree": duree,
                    "duree_heures": 0,
                    "type_formation": type_formation,
                    "filiere": filieres[filiere_nom],
                    "cout": cout,
                    "frais_participation": frais_participation,
                    "frais_jury": frais_jury,
                    "frais_materiels": frais_materiels,
                    "active": True,
                },
            )
            changed = False
            if metier.filiere_id != filieres[filiere_nom].id:
                metier.filiere = filieres[filiere_nom]
                changed = True
            if metier.duree != duree:
                metier.duree = duree
                changed = True
            if metier.cout != cout:
                metier.cout = cout
                changed = True
            if metier.frais_participation != frais_participation:
                metier.frais_participation = frais_participation
                changed = True
            if metier.frais_jury != frais_jury:
                metier.frais_jury = frais_jury
                changed = True
            if metier.frais_materiels != frais_materiels:
                metier.frais_materiels = frais_materiels
                changed = True
            if hasattr(metier, 'type_formation') and metier.type_formation != type_formation:
                metier.type_formation = type_formation
                changed = True
            if not metier.active:
                metier.active = True
                changed = True
            if changed:
                metier.save()
            
            Module.objects.filter(metier=metier).delete()
            
            total_duree_heures_for_metier = 0
            for ordre, module_spec in enumerate(spec.get("modules", []), start=1):
                titre, description, duree_module_heures = module_spec
                
                formateur_to_assign = formateurs_list[formateur_index % len(formateurs_list)]
                
                module_obj = Module.objects.create( # Créer le module d'abord
                    metier=metier,
                    titre=titre,
                    description=description,
                    duree_heures=duree_module_heures,
                    # formateur=formateur_to_assign, # Ne pas passer ici
                    ordre=ordre,
                )
                module_obj.formateurs.add(formateur_to_assign) # Ajouter le formateur au ManyToManyField

                total_duree_heures_for_metier += duree_module_heures
                formateur_index += 1
            
            if metier.duree_heures != total_duree_heures_for_metier:
                metier.duree_heures = total_duree_heures_for_metier
                metier.save(update_fields=['duree_heures'])

            metiers[nom] = metier

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
                "categorie": "dans l'emploi",
                "niveau_etude": "Diplome d'Etat",
                "adresse": "Kinshasa / Lemba",
                "nationalite": "Congolaise",
                "type_piece": "CE",
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
                "autres_formations": [
                    {
                        "intitule": "Formation en Cybersécurité",
                        "etablissement": "Global Tech Academy",
                        "annee_fin": 2023,
                    }
                ],
                "entreprise_nom": "Global Tech Solutions",
                "fonction": "Technicien Électricien",
                "anciennete_emploi": 3,
                "anciennete_entreprise": 3,
                "photo": "stagiaires/photo5.jpg",
                "filiere_nom": "Développement des plates-formes informatiques",
            },
            {
                "nom": "Tshibangu",
                "postnom": "Mbuyi",
                "prenom": "Patrick",
                "sexe": "M",
                "telephone": "0991000002",
                "email": "patrick.tshibangu.demo@training.local",
                "categorie": "sans emploi",
                "niveau_etude": "Graduat",
                "adresse": "Kinshasa / Ngaliema",
                "nationalite": "Congolaise",
                "type_piece": "PS",
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
                "photo": "stagiaires/photo6.jpg",
                "filiere_nom": "Bureautique",
            },
            {
                "nom": "Ilunga",
                "postnom": "Banza",
                "prenom": "Merveille",
                "sexe": "F",
                "telephone": "0991000003",
                "email": "merveille.ilunga.demo@training.local",
                "categorie": "non défini",
                "niveau_etude": "Licence",
                "adresse": "Kinshasa / Gombe",
                "nationalite": "Congolaise",
                "type_piece": "PC",
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
                "photo": "stagiaires/photo7.jpg",
                "filiere_nom": "Administration et Gestion",
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
                "type_piece": "CE",
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
                "filiere_nom": "Administration système et réseaux",
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
                "type_piece": "PS",
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
                "filiere_nom": "Administration et Gestion",
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
                "type_piece": "PC",
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
                "filiere_nom": "Administration et Gestion",
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
                "type_piece": "PS",
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
                "filiere_nom": "Bureautique",
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
                "type_piece": spec["type_piece"],
                "numero_piece": spec["numero_piece"],
                "nom_pere": spec["nom_pere"],
                "nom_mere": spec["nom_mere"],
                "niveau_etude": spec["niveau_etude"],
                "photo": spec["photo"],
                "filiere": filieres[spec["filiere_nom"]],
            }

            if spec["categorie"] == "dans l'emploi":
                defaults["entreprise"] = entreprises[spec["entreprise_nom"]]
                defaults["fonction"] = spec["fonction"]
                defaults["anciennete_emploi"] = spec["anciennete_emploi"]
                defaults["anciennete_entreprise"] = spec["anciennete_entreprise"]
            else:
                defaults["entreprise"] = None
                defaults["fonction"] = None
                defaults["anciennete_emploi"] = None
                defaults["anciennete_entreprise"] = None


            stagiaire, _ = Stagiaire.objects.get_or_create(
                email=spec["email"],
                defaults=defaults,
            )
            
            changed = False
            for field, value in defaults.items():
                if field == "filiere":
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
        for code, libelle in [("INT", "Interné"), ("EXT", "Externé")]:
            type_action, _ = TypeAction.objects.get_or_create(code=code, defaults={"libelle": libelle})
            if type_action.libelle != libelle:
                type_action.libelle = libelle
                type_action.save(update_fields=["libelle"])
            type_actions[code] = type_action

        actions = {}
        action_specs = [
            {"description": "Session Electricite - Cohorte A", "date_debut": date(2026, 5, 20), "date_fin": date(2026, 11, 20), "metier_nom": "Electricite batiment", "formateur_matricules": ["FM001"], "type_action_code": "INT"},
            {"description": "Pack Office - Vague Mai", "date_debut": date(2026, 5, 18), "date_fin": date(2026, 8, 18), "metier_nom": "Pack Office professionnel", "formateur_matricules": ["FM002"], "type_action_code": "EXT"},
            {"description": "Maintenance Preventive - Juin", "date_debut": date(2026, 6, 1), "date_fin": date(2026, 9, 1), "metier_nom": "Maintenance preventive", "formateur_matricules": ["FM001", "FM002"], "type_action_code": "INT"},
            {"description": "Secretaire de Direction - Sept", "date_debut": date(2026, 9, 1), "date_fin": date(2027, 3, 1), "metier_nom": "Secretaire de direction", "formateur_matricules": ["FM002"], "type_action_code": "EXT"},
            {"description": "Automatisme Avance - Juillet", "date_debut": date(2026, 7, 10), "date_fin": date(2026, 10, 10), "metier_nom": "Automatisme industriel", "formateur_matricules": ["FM001", "FM002"], "type_action_code": "INT"},
            {"description": "Gestion de Projets PME - Oct", "date_debut": date(2026, 10, 1), "date_fin": date(2027, 2, 1), "metier_nom": "Gestion de Projets PME", "formateur_matricules": ["FM004"], "type_action_code": "EXT"},
        ]
        for spec in action_specs:
            metier_for_action = metiers[spec["metier_nom"]]
            
            self.stdout.write(self.style.NOTICE(f"Processing Action: {spec['description']} for Metier: {metier_for_action.nom}"))

            action, created = Action.objects.get_or_create(
                description=spec["description"],
                defaults={
                    "date_debut": spec["date_debut"],
                    "date_fin": spec["date_fin"],
                    "metier": metier_for_action,
                    "type_action": type_actions[spec["type_action_code"]],
                },
            )
            
            changed = False
            if action.date_debut != spec["date_debut"]:
                action.date_debut = spec["date_debut"]
                changed = True
            if action.date_fin != spec["date_fin"]:
                action.date_fin = spec["date_fin"]
                changed = True
            if action.metier_id != metier_for_action.id:
                action.metier = metier_for_action
                changed = True
            if action.type_action_id != type_actions[spec["type_action_code"]].id:
                action.type_action = type_actions[spec["type_action_code"]]
                changed = True
            if changed:
                action.save()

            formateurs_from_modules = Formateur.objects.filter(
                modules_dispenses__metier=metier_for_action
            ).distinct()
            
            assigned_formateurs_for_action = list(formateurs_from_modules)

            self.stdout.write(self.style.NOTICE(f"  Assigning Formateurs from modules for '{metier_for_action.nom}': {[str(f) for f in assigned_formateurs_for_action]}"))
            
            action.formateurs.set(assigned_formateurs_for_action)

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
            {"stagiaire_email": "aline.mukendi.demo@training.local", "action_description": "Gestion de Projets PME - Oct", "statut": "Inscrit", "date_inscription": date(2026, 9, 15)},
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

        # --- Ajout des paiements de démonstration ---
        self.stdout.write(self.style.SUCCESS("Generation des paiements de demonstration..."))
        paiement_specs = [
            {"stagiaire_email": "aline.mukendi.demo@training.local", "action_description": "Session Electricite - Cohorte A", "montant": 500.00, "date_paiement": date(2026, 5, 15), "motif": "Acompte formation", "mode_paiement": "ESPECES"},
            {"stagiaire_email": "aline.mukendi.demo@training.local", "action_description": "Session Electricite - Cohorte A", "montant": 1000.00, "date_paiement": date(2026, 6, 10), "motif": "Solde formation", "mode_paiement": "VIREMENT"},
            {"stagiaire_email": "patrick.tshibangu.demo@training.local", "action_description": "Pack Office - Vague Mai", "montant": 800.00, "date_paiement": date(2026, 5, 10), "motif": "Paiement complet", "mode_paiement": "MOBILE_MONEY"},
            {"stagiaire_email": "merveille.ilunga.demo@training.local", "action_description": "Pack Office - Vague Mai", "montant": 400.00, "date_paiement": date(2026, 5, 12), "motif": "Acompte", "mode_paiement": "ESPECES"},
            {"stagiaire_email": "david.kabongo.demo@training.local", "action_description": "Session Electricite - Cohorte A", "montant": 750.00, "date_paiement": date(2026, 5, 20), "motif": "Paiement partiel", "mode_paiement": "VIREMENT"},
            {"stagiaire_email": "esther.lufuma.demo@training.local", "action_description": "Maintenance Preventive - Juin", "montant": 600.00, "date_paiement": date(2026, 6, 5), "motif": "Acompte", "mode_paiement": "ESPECES"},
            {"stagiaire_email": "christian.mbuyi.demo@training.local", "action_description": "Secretaire de Direction - Sept", "montant": 1300.00, "date_paiement": date(2026, 8, 20), "motif": "Paiement complet", "mode_paiement": "MOBILE_MONEY"},
        ]

        for spec in paiement_specs:
            stagiaire_obj = stagiaires[spec["stagiaire_email"]]
            action_obj = actions.get(spec["action_description"]) # Utiliser .get() car l'action peut être None

            Paiement.objects.get_or_create(
                stagiaire=stagiaire_obj,
                action=action_obj,
                montant=spec["montant"],
                date_paiement=spec["date_paiement"],
                motif=spec["motif"],
                mode_paiement=spec["mode_paiement"],
                # La référence est générée automatiquement par le modèle
            )
        self.stdout.write(self.style.SUCCESS("Paiements de demonstration generes."))
        # --- Fin de l'ajout des paiements ---


        self.stdout.write(self.style.SUCCESS("Donnees de demonstration generees avec succes."))
        self.stdout.write("Comptes de test:")
        self.stdout.write("  - Admin: admin / demo")
        self.stdout.write("  - Manager: manager / demo")
        self.stdout.write("  - Chef de filière: chef.filiere / demo")
        self.stdout.write("  - Chef de service: chef.service / demo")
        self.stdout.write("  - Utilisateur standard: user.standard / demo")