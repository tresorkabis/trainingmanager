from datetime import date

from django.core.management import BaseCommand
from django.db import transaction

from intern.models import Categorie, EtudeStagiaire, Stagiaire, Entreprise, AutreFormation # Import AutreFormation
from progress.models import Action, DetailAction, Formateur, TypeAction
from training.models import Filiere, Formation, Service
from users.models import Profile, User
from users.utils import createprofile


class Command(BaseCommand):
    help = "Peuple la base avec des donnees de demonstration coherentes."

    @transaction.atomic
    def handle(self, *args, **options):
        createprofile()
        manager_profile = Profile.objects.filter(name="Manager").first()

        demo_user, created = User.objects.get_or_create(
            username="demo.manager",
            defaults={
                "email": "demo.manager@training.local",
                "first_name": "Demo",
                "last_name": "Manager",
                "profile": manager_profile,
            },
        )
        if created or not demo_user.check_password("demo1234"):
            demo_user.set_password("demo1234")
            demo_user.profile = manager_profile # Ensure profile is set even if user existed
            demo_user.save()

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

        formations = {}
        formation_specs = [
            {"nom": "Electricite batiment", "duree": 6, "filiere_nom": "Electricite industrielle", "fraismateriels": 120.0, "cout": 1500.00},
            {"nom": "Automatisme industriel", "duree": 8, "filiere_nom": "Electricite industrielle", "fraismateriels": 180.0, "cout": 2000.00},
            {"nom": "Maintenance preventive", "duree": 5, "filiere_nom": "Maintenance des equipements", "fraismateriels": 95.0, "cout": 1200.00},
            {"nom": "Pack Office professionnel", "duree": 3, "filiere_nom": "Bureautique", "fraismateriels": 60.0, "cout": 800.00},
            {"nom": "Secretaire de direction", "duree": 6, "filiere_nom": "Gestion administrative", "fraismateriels": 110.0, "cout": 1300.00},
        ]
        for spec in formation_specs:
            nom = spec["nom"]
            duree = spec["duree"]
            filiere_nom = spec["filiere_nom"]
            fraismateriels = spec["fraismateriels"]
            cout = spec["cout"]
            duree_heures = duree * 20 * 7 # Assuming 20 working days/month, 7 hours/day

            formation, _ = Formation.objects.get_or_create(
                nom=nom,
                defaults={
                    "duree": duree,
                    "duree_heures": duree_heures,
                    "filiere": filieres[filiere_nom],
                    "cout": cout,
                    "fraismateriels": fraismateriels,
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
            if formation.duree_heures != duree_heures:
                formation.duree_heures = duree_heures
                changed = True
            if formation.cout != cout:
                formation.cout = cout
                changed = True
            if formation.fraismateriels != fraismateriels:
                formation.fraismateriels = fraismateriels
                changed = True
            if not formation.active: # Ensure it's active
                formation.active = True
                changed = True
            if changed:
                formation.save()
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
                "fonction": "Technicien de maintenance",
                "anciennete_emploi": 6,
                "anciennete_entreprise": 4,
                "photo": "stagiaires/photo1.jpg",
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
                if getattr(stagiaire, field) != value:
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

        formateurs = {}
        for matricule, nom, postnom, adresse, telephone, email in [
            ("FM001", "Kabasele", "Mwamba", "Kinshasa / Kintambo", "0817000001", "kabasele.demo@training.local"),
            ("FM002", "Ngoy", "Kabeya", "Kinshasa / Limete", "0817000002", "ngoy.demo@training.local"),
        ]:
            formateur, _ = Formateur.objects.get_or_create(
                matricule=matricule,
                defaults={
                    "nom": nom,
                    "postnom": postnom,
                    "adresse": adresse,
                    "telephone": telephone,
                    "email": email,
                },
            )
            changed = False
            for field, value in {
                "nom": nom,
                "postnom": postnom,
                "adresse": adresse,
                "telephone": telephone,
                "email": email,
            }.items():
                if getattr(formateur, field) != value:
                    setattr(formateur, field, value)
                    changed = True
            if changed:
                formateur.save()
            formateurs[matricule] = formateur

        actions = {}
        for description, debut, fin, formation_nom in [
            ("Session Electricite - Cohorte A", date(2026, 5, 20), date(2026, 11, 20), "Electricite batiment"),
            ("Pack Office - Vague Mai", date(2026, 5, 18), date(2026, 8, 18), "Pack Office professionnel"),
        ]:
            action, _ = Action.objects.get_or_create(
                description=description,
                defaults={
                    "date_debut": debut,
                    "date_fin": fin,
                    "formation": formations[formation_nom],
                },
            )
            changed = False
            if action.date_debut != debut:
                action.date_debut = debut
                changed = True
            if action.date_fin != fin:
                action.date_fin = fin
                changed = True
            if action.formation_id != formations[formation_nom].id:
                action.formation = formations[formation_nom]
                changed = True
            if changed:
                action.save()
            actions[description] = action

        detail_specs = [
            ("aline.mukendi.demo@training.local", "Session Electricite - Cohorte A"),
            ("patrick.tshibangu.demo@training.local", "Pack Office - Vague Mai"),
            ("merveille.ilunga.demo@training.local", "Pack Office - Vague Mai"),
        ]
        for stagiaire_email, action_description in detail_specs:
            DetailAction.objects.get_or_create(
                stagiaire=stagiaires[stagiaire_email],
                action=actions[action_description],
            )

        self.stdout.write(self.style.SUCCESS("Donnees de demonstration generees avec succes."))
        self.stdout.write("Compte demo : demo.manager / demo1234")