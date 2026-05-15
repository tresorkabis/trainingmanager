from datetime import date

from django.core.management import BaseCommand
from django.db import transaction

from intern.models import Categorie, EtudeStagiaire, Stagiaire
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

        demo_user, user_created = User.objects.get_or_create(
            username="demo.manager",
            defaults={
                "email": "demo.manager@training.local",
                "first_name": "Demo",
                "last_name": "Manager",
                "profile": manager_profile,
            },
        )
        if user_created or not demo_user.check_password("demo1234"):
            demo_user.set_password("demo1234")
            demo_user.profile = manager_profile
            demo_user.save()

        categories = {}
        for titre in ["Technique", "Administration", "Informatique", "Maintenance"]:
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
            ("Electricite batiment", 6, "Electricite industrielle", 120.0),
            ("Automatisme industriel", 8, "Electricite industrielle", 180.0),
            ("Maintenance preventive", 5, "Maintenance des equipements", 95.0),
            ("Pack Office professionnel", 3, "Bureautique", 60.0),
            ("Secretaire de direction", 6, "Gestion administrative", 110.0),
        ]
        for nom, duree, filiere_nom, frais in formation_specs:
            formation, _ = Formation.objects.get_or_create(
                nom=nom,
                defaults={
                    "duree": duree,
                    "filiere": filieres[filiere_nom],
                    "fraismateriels": frais,
                },
            )
            changed = False
            if formation.filiere_id != filieres[filiere_nom].id:
                formation.filiere = filieres[filiere_nom]
                changed = True
            if formation.duree != duree:
                formation.duree = duree
                changed = True
            if formation.fraismateriels != frais:
                formation.fraismateriels = frais
                changed = True
            if changed:
                formation.save()
            formations[nom] = formation

        stagiaire_specs = [
            {
                "nom": "Mukendi",
                "postnom": "Kasongo",
                "prenom": "Aline",
                "sexe": "F",
                "telephone": "0991000001",
                "email": "aline.mukendi.demo@training.local",
                "categorie": "Technique",
                "service": "Technique Industrielle",
                "filiere": "Electricite industrielle",
                "formation": "Electricite batiment",
                "niveau_etude": "Diplome d'Etat",
                "adresse": "Kinshasa / Lemba",
                "nationalite": "Congolaise",
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
                        "description": "Orientation technique avec base en installation electrique.",
                    }
                ],
            },
            {
                "nom": "Tshibangu",
                "postnom": "Mbuyi",
                "prenom": "Patrick",
                "sexe": "M",
                "telephone": "0991000002",
                "email": "patrick.tshibangu.demo@training.local",
                "categorie": "Informatique",
                "service": "Informatique",
                "filiere": "Bureautique",
                "formation": "Pack Office professionnel",
                "niveau_etude": "Graduat",
                "adresse": "Kinshasa / Ngaliema",
                "nationalite": "Congolaise",
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
                        "description": "Formation initiale en bureautique et gestion numerique.",
                    },
                    {
                        "intitule": "Comptabilite generale",
                        "etablissement": "Centre Polyvalent",
                        "niveau": "Certification",
                        "annee_debut": 2022,
                        "annee_fin": 2022,
                        "diplome_obtenu": "Attestation",
                        "description": "Module court complete pour les outils administratifs.",
                    },
                ],
            },
            {
                "nom": "Ilunga",
                "postnom": "Banza",
                "prenom": "Merveille",
                "sexe": "F",
                "telephone": "0991000003",
                "email": "merveille.ilunga.demo@training.local",
                "categorie": "Administration",
                "service": "Gestion Administrative",
                "filiere": "Gestion administrative",
                "formation": "Secretaire de direction",
                "niveau_etude": "Licence",
                "adresse": "Kinshasa / Gombe",
                "nationalite": "Congolaise",
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
                        "description": "Profil oriente gestion, accueil et organisation administrative.",
                    }
                ],
            },
        ]

        stagiaires = {}
        for spec in stagiaire_specs:
            stagiaire, _ = Stagiaire.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "nom": spec["nom"],
                    "postnom": spec["postnom"],
                    "prenom": spec["prenom"],
                    "adresse": spec["adresse"],
                    "sexe": spec["sexe"],
                    "telephone": spec["telephone"],
                    "categorie": categories[spec["categorie"]],
                    "service": services[spec["service"]],
                    "filiere": filieres[spec["filiere"]],
                    "formation": formations[spec["formation"]],
                    "date_naissance": spec["date_naissance"],
                    "lieu_naissance": spec["lieu_naissance"],
                    "nationalite": spec["nationalite"],
                    "numero_piece": spec["numero_piece"],
                    "nom_pere": spec["nom_pere"],
                    "nom_mere": spec["nom_mere"],
                    "niveau_etude": spec["niveau_etude"],
                },
            )
            changed = False
            for field, value in {
                "nom": spec["nom"],
                "postnom": spec["postnom"],
                "prenom": spec["prenom"],
                "adresse": spec["adresse"],
                "sexe": spec["sexe"],
                "telephone": spec["telephone"],
                "categorie": categories[spec["categorie"]],
                "service": services[spec["service"]],
                "filiere": filieres[spec["filiere"]],
                "formation": formations[spec["formation"]],
                "date_naissance": spec["date_naissance"],
                "lieu_naissance": spec["lieu_naissance"],
                "nationalite": spec["nationalite"],
                "numero_piece": spec["numero_piece"],
                "nom_pere": spec["nom_pere"],
                "nom_mere": spec["nom_mere"],
                "niveau_etude": spec["niveau_etude"],
            }.items():
                if getattr(stagiaire, field) != value:
                    setattr(stagiaire, field, value)
                    changed = True
            if changed:
                stagiaire.save()

            EtudeStagiaire.objects.filter(stagiaire=stagiaire).delete()
            for etude in spec["etudes"]:
                EtudeStagiaire.objects.create(stagiaire=stagiaire, **etude)
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
