from django.core.exceptions import ValidationError
from django.urls import reverse
from django.test import TestCase, Client

from training.models import Service, Filiere, Formation, Module
from progress.models import Formateur
from users.models import User, Profile


class ServiceModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service Informatique")

    def test_service_creation(self):
        self.assertEqual(self.service.nom, "Service Informatique")
        self.assertTrue(self.service.active)

    def test_service_str(self):
        self.assertEqual(str(self.service), "Service Informatique")

    def test_service_default_active(self):
        service = Service.objects.create(nom="Test")
        self.assertTrue(service.active)


class FiliereModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")

    def test_filiere_creation(self):
        filiere = Filiere.objects.create(nom="Développement", service=self.service)
        self.assertEqual(filiere.nom, "Développement")
        self.assertEqual(filiere.service.nom, "Service A")

    def test_filiere_str(self):
        filiere = Filiere.objects.create(nom="Réseau", service=self.service)
        self.assertEqual(str(filiere), "Réseau")

    def test_filiere_without_service(self):
        filiere = Filiere.objects.create(nom="Générale")
        self.assertIsNone(filiere.service)

    def test_filiere_related_name(self):
        Filiere.objects.create(nom="F1", service=self.service)
        Filiere.objects.create(nom="F2", service=self.service)
        self.assertEqual(self.service.filieres.count(), 2)


class FormationModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Informatique", service=self.service)

    def test_formation_creation(self):
        formation = Formation.objects.create(
            nom="Django Avancé",
            duree=30,
            duree_heures=60,
            filiere=self.filiere,
            cout=1500,
            type_formation="qualifiante",
        )
        self.assertEqual(formation.nom, "Django Avancé")
        self.assertEqual(formation.type_formation, "qualifiante")
        self.assertEqual(formation.cout, 1500)

    def test_formation_continue_default(self):
        formation = Formation.objects.create(
            nom="Formation Continue",
            duree=5,
            filiere=self.filiere,
            type_formation="continue",
        )
        self.assertEqual(formation.type_formation, "continue")

    def test_formation_str(self):
        formation = Formation.objects.create(
            nom="Python",
            duree=10,
            filiere=self.filiere,
        )
        self.assertEqual(str(formation), "Python")

    def test_formation_frais_defaults(self):
        formation = Formation.objects.create(
            nom="Test Frais",
            duree=10,
            filiere=self.filiere,
        )
        self.assertEqual(formation.frais_participation, 0)
        self.assertEqual(formation.frais_jury, 0)
        self.assertEqual(formation.frais_materiels, 0)

    def test_formation_related_name(self):
        self.filiere.formations.create(nom="F1", duree=10)
        self.filiere.formations.create(nom="F2", duree=20)
        self.assertEqual(self.filiere.formations.count(), 2)


class ModuleModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Informatique", service=self.service)
        self.formation = Formation.objects.create(
            nom="Django", duree=30, filiere=self.filiere,
        )
        self.formateur = Formateur.objects.create(
            matricule="F001", nom="Kabise", postnom="Tresor",
            adresse="Adr", telephone="+243800000200",
            email="tresor@example.com",
        )

    def test_module_creation(self):
        module = Module.objects.create(
            formation=self.formation,
            titre="Vues Django",
            duree_heures=10,
            ordre=1,
        )
        self.assertEqual(module.titre, "Vues Django")
        self.assertEqual(module.formation.nom, "Django")

    def test_module_str(self):
        module = Module.objects.create(
            formation=self.formation,
            titre="Modèles",
            ordre=2,
        )
        self.assertIn("Django", str(module))
        self.assertIn("Modèles", str(module))

    def test_module_formateurs_m2m(self):
        module = Module.objects.create(
            formation=self.formation,
            titre="APIs",
            ordre=3,
        )
        module.formateurs.add(self.formateur)
        self.assertEqual(module.formateurs.count(), 1)
        self.assertIn(self.formateur, module.formateurs.all())

    def test_module_default_ordering(self):
        m1 = Module.objects.create(formation=self.formation, titre="B", ordre=2)
        m2 = Module.objects.create(formation=self.formation, titre="A", ordre=1)
        modules = Module.objects.all()
        self.assertEqual(modules[0], m2)
        self.assertEqual(modules[1], m1)

    def test_module_related_name(self):
        self.formation.modules.create(titre="M1", ordre=1)
        self.formation.modules.create(titre="M2", ordre=2)
        self.assertEqual(self.formation.modules.count(), 2)


class ServiceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(name="Manager")
        self.user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
        )
        self.user.profile = self.profile
        self.user.save()
        self.service = Service.objects.create(nom="Service A")

    def test_service_list_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("services"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Service A")

    def test_service_create_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("service_create"), {
            "nom": "Nouveau Service",
            "active": True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Service.objects.filter(nom="Nouveau Service").exists())

    def test_service_update_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("service_update", kwargs={"pk": self.service.pk}),
            {"nom": "Service Modifié", "active": True},
        )
        self.assertEqual(response.status_code, 302)
        self.service.refresh_from_db()
        self.assertEqual(self.service.nom, "Service Modifié")

    def test_service_delete_as_admin(self):
        self.client.force_login(self.user)
        s = Service.objects.create(nom="Temp")
        response = self.client.post(reverse("service_delete", kwargs={"pk": s.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Service.objects.filter(pk=s.pk).exists())


class FiliereViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(name="Manager")
        self.user = User.objects.create_user(
            username="admin2",
            email="admin2@example.com",
            password="testpass123",
        )
        self.user.profile = self.profile
        self.user.save()
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Informatique", service=self.service)

    def test_filiere_list_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("filieres"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informatique")

    def test_filiere_create_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("filiere_create"), {
            "nom": "Réseau",
            "service": self.service.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Filiere.objects.filter(nom="Réseau").exists())

    def test_filiere_detail_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("filiere", kwargs={"pk": self.filiere.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informatique")

    def test_filiere_update_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("filiere_update", kwargs={"pk": self.filiere.pk}),
            {"nom": "Développement", "service": self.service.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.filiere.refresh_from_db()
        self.assertEqual(self.filiere.nom, "Développement")

    def test_filiere_delete_as_admin(self):
        self.client.force_login(self.user)
        f = Filiere.objects.create(nom="Temp")
        response = self.client.post(reverse("filiere_delete", kwargs={"pk": f.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Filiere.objects.filter(pk=f.pk).exists())


class FormationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(name="Manager")
        self.user = User.objects.create_user(
            username="admin3",
            email="admin3@example.com",
            password="testpass123",
        )
        self.user.profile = self.profile
        self.user.save()
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Informatique", service=self.service)
        self.formation = Formation.objects.create(
            nom="Django Pro", duree=30, filiere=self.filiere,
        )

    def test_formation_list_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("formations"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Pro")

    def test_formation_create_as_admin(self):
        self.client.force_login(self.user)
        # The view uses both MetierForm and ModuleFormSet - provide empty formset data
        response = self.client.post(reverse("formation_create"), {
            "nom": "Python Avancé",
            "duree": 20,
            "type_formation": "qualifiante",
            "filiere": self.filiere.pk,
            "cout": 1000,
            "frais_participation": 500,
            "frais_jury": 200,
            "frais_materiels": 300,
            # ModuleFormSet management form data (empty formset)
            "modules-TOTAL_FORMS": "0",
            "modules-INITIAL_FORMS": "0",
            "modules-MIN_NUM_FORMS": "0",
            "modules-MAX_NUM_FORMS": "1000",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Formation.objects.filter(nom="Python Avancé").exists())

    def test_formation_detail_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("formation", kwargs={"pk": self.formation.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Pro")

    def test_formation_update_as_admin(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("formation_update", kwargs={"pk": self.formation.pk}),
            {
                "nom": "Django Expert",
                "duree": 40,
                "type_formation": "qualifiante",
                "filiere": self.filiere.pk,
                "cout": 2000,
                "frais_participation": 1000,
                "frais_jury": 500,
                "frais_materiels": 500,
                # ModuleFormSet management form data (empty formset - formation has 0 modules)
                "modules-TOTAL_FORMS": "0",
                "modules-INITIAL_FORMS": "0",
                "modules-MIN_NUM_FORMS": "0",
                "modules-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.formation.refresh_from_db()
        self.assertEqual(self.formation.nom, "Django Expert")

    def test_formation_delete_as_admin(self):
        self.client.force_login(self.user)
        f = Formation.objects.create(nom="Temp", duree=10, filiere=self.filiere)
        response = self.client.post(reverse("formation_delete", kwargs={"pk": f.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Formation.objects.filter(pk=f.pk).exists())

    def test_formation_list_uses_legacy_name(self):
        """L'ancien nom 'metiers' doit rediriger vers la même vue."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("metiers"))
        self.assertEqual(response.status_code, 200)