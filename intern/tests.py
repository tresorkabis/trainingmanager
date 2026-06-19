from datetime import date

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.test import TestCase, Client

from intern.models import Categorie, Entreprise, Stagiaire, EtudeStagiaire, AutreFormation
from intern.forms import StagiaireForm
from users.models import User, Profile


class CategorieModelTests(TestCase):
    def setUp(self):
        self.categorie = Categorie.objects.create(titre="sans emploi")

    def test_categorie_creation(self):
        self.assertEqual(self.categorie.titre, "sans emploi")
        self.assertTrue(self.categorie.active)
        self.assertIsNotNone(self.categorie.created_at)
        self.assertIsNotNone(self.categorie.updated_at)

    def test_categorie_str(self):
        self.assertEqual(str(self.categorie), "sans emploi")

    def test_categorie_default_active(self):
        categorie = Categorie.objects.create(titre="test")
        self.assertTrue(categorie.active)

    def test_categorie_unique_titre_constraint(self):
        """Deux catégories avec le même titre sont autorisées au niveau DB (pas de contrainte UNIQUE)."""
        cat2 = Categorie.objects.create(titre="sans emploi")
        self.assertIsNotNone(cat2.pk)
        self.assertNotEqual(cat2.pk, self.categorie.pk)


class EntrepriseModelTests(TestCase):
    def setUp(self):
        self.entreprise = Entreprise.objects.create(
            nom="SNEL",
            adresse="Kinshasa",
            telephone="+243800000000",
            email="contact@snel.cd",
        )

    def test_entreprise_creation(self):
        self.assertEqual(self.entreprise.nom, "SNEL")
        self.assertEqual(self.entreprise.adresse, "Kinshasa")
        self.assertEqual(self.entreprise.telephone, "+243800000000")
        self.assertEqual(self.entreprise.email, "contact@snel.cd")

    def test_entreprise_str(self):
        self.assertEqual(str(self.entreprise), "SNEL")

    def test_entreprise_blank_fields(self):
        entreprise = Entreprise.objects.create(nom="Test")
        self.assertIsNone(entreprise.adresse)
        self.assertIsNone(entreprise.telephone)
        self.assertIsNone(entreprise.email)


class StagiaireModelTests(TestCase):
    def setUp(self):
        self.categorie_sans_emploi = Categorie.objects.create(titre="sans emploi")
        self.categorie_dans_emploi = Categorie.objects.create(titre="dans l'emploi")
        self.entreprise = Entreprise.objects.create(nom="SNEL")

    def test_stagiaire_creation_minimal(self):
        stagiaire = Stagiaire.objects.create(
            nom="Dupont",
            postnom="Jean",
            prenom="Pierre",
            adresse="123 Rue",
            sexe="M",
            telephone="+243800000001",
            email="jean.dupont@example.com",
            categorie=self.categorie_sans_emploi,
        )
        self.assertEqual(stagiaire.nom, "Dupont")
        self.assertEqual(stagiaire.get_full_name(), "Dupont Jean Pierre")
        self.assertTrue(stagiaire.active)

    def test_stagiaire_full_creation(self):
        stagiaire = Stagiaire.objects.create(
            nom="Kabise",
            postnom="Tresor",
            prenom="",
            adresse="Avenue XYZ",
            sexe="M",
            telephone="+243800000002",
            email="tresor.kabise@example.com",
            date_naissance=date(1990, 1, 1),
            lieu_naissance="Kinshasa",
            nationalite="Congolaise",
            type_piece="CE",
            numero_piece="CE123456",
            nom_pere="Pere",
            nom_mere="Mere",
            niveau_etude="BAC+5",
            categorie=self.categorie_sans_emploi,
        )
        self.assertEqual(stagiaire.type_piece, "CE")
        self.assertEqual(stagiaire.numero_piece, "CE123456")

    def test_stagiaire_with_entreprise(self):
        stagiaire = Stagiaire.objects.create(
            nom="emploi",
            postnom="Test",
            prenom="",
            adresse="Adresse",
            sexe="M",
            telephone="+243800000003",
            email="emploi.test@example.com",
            categorie=self.categorie_dans_emploi,
            entreprise=self.entreprise,
            fonction="Ingénieur",
            anciennete_emploi=5,
            anciennete_entreprise=3,
        )
        self.assertEqual(stagiaire.entreprise.nom, "SNEL")
        self.assertEqual(stagiaire.fonction, "Ingénieur")
        self.assertEqual(stagiaire.anciennete_emploi, 5)

    def test_stagiaire_unique_email(self):
        Stagiaire.objects.create(
            nom="A",
            postnom="B",
            prenom="C",
            adresse="Adr",
            sexe="M",
            telephone="+243800000010",
            email="unique@example.com",
            categorie=self.categorie_sans_emploi,
        )
        with self.assertRaises(Exception):
            Stagiaire.objects.create(
                nom="X",
                postnom="Y",
                prenom="Z",
                adresse="Adr2",
                sexe="F",
                telephone="+243800000011",
                email="unique@example.com",
                categorie=self.categorie_sans_emploi,
            )

    def test_stagiaire_str(self):
        stagiaire = Stagiaire.objects.create(
            nom="Test",
            postnom="User",
            prenom="A",
            adresse="Adr",
            sexe="M",
            telephone="+243800000020",
            email="test.user@example.com",
            categorie=self.categorie_sans_emploi,
        )
        self.assertIn("Test", str(stagiaire))

    def test_stagiaire_get_full_name(self):
        stagiaire = Stagiaire(
            nom="Nom", postnom="Post", prenom="Pre"
        )
        self.assertEqual(stagiaire.get_full_name(), "Nom Post Pre")

    def test_stagiaire_get_full_name_no_prenom(self):
        stagiaire = Stagiaire(
            nom="Nom", postnom="Post", prenom=""
        )
        self.assertEqual(stagiaire.get_full_name(), "Nom Post")


class EtudeStagiaireModelTests(TestCase):
    def setUp(self):
        cat = Categorie.objects.create(titre="sans emploi")
        self.stagiaire = Stagiaire.objects.create(
            nom="Etudiant", postnom="Test", prenom="",
            adresse="Adr", sexe="M", telephone="+243800000030",
            email="etudiant.test@example.com", categorie=cat,
        )

    def test_etude_creation(self):
        etude = EtudeStagiaire.objects.create(
            stagiaire=self.stagiaire,
            intitule="Licence en Informatique",
            etablissement="UNIKIN",
            niveau="L3",
            annee_debut=2018,
            annee_fin=2022,
            diplome_obtenu="Licence",
        )
        self.assertEqual(etude.intitule, "Licence en Informatique")
        self.assertEqual(etude.diplome_obtenu, "Licence")

    def test_etude_str(self):
        etude = EtudeStagiaire.objects.create(
            stagiaire=self.stagiaire,
            intitule="Master",
        )
        self.assertIn("Etudiant", str(etude))

    def test_etude_related_name(self):
        EtudeStagiaire.objects.create(stagiaire=self.stagiaire, intitule="E1")
        EtudeStagiaire.objects.create(stagiaire=self.stagiaire, intitule="E2")
        self.assertEqual(self.stagiaire.etudes.count(), 2)


class AutreFormationModelTests(TestCase):
    def setUp(self):
        cat = Categorie.objects.create(titre="sans emploi")
        self.stagiaire = Stagiaire.objects.create(
            nom="Formation", postnom="Autre", prenom="",
            adresse="Adr", sexe="F", telephone="+243800000040",
            email="formation.autre@example.com", categorie=cat,
        )

    def test_autre_formation_creation(self):
        af = AutreFormation.objects.create(
            stagiaire=self.stagiaire,
            intitule="Formation Python",
            etablissement="Coursera",
            annee_fin=2023,
        )
        self.assertEqual(af.intitule, "Formation Python")
        self.assertEqual(af.annee_fin, 2023)

    def test_autre_formation_str(self):
        af = AutreFormation.objects.create(
            stagiaire=self.stagiaire,
            intitule="Django",
        )
        self.assertIn("Formation", str(af))

    def test_autre_formation_related_name(self):
        AutreFormation.objects.create(stagiaire=self.stagiaire, intitule="F1")
        AutreFormation.objects.create(stagiaire=self.stagiaire, intitule="F2")
        self.assertEqual(self.stagiaire.autres_formations.count(), 2)


class StagiaireFormTests(TestCase):
    def setUp(self):
        self.cat_sans_emploi = Categorie.objects.create(titre="sans emploi")
        self.cat_dans_emploi = Categorie.objects.create(titre="dans l'emploi")

    def test_form_valid_minimal(self):
        form = StagiaireForm(data={
            'nom': 'Test',
            'postnom': 'User',
            'prenom': 'A',
            'adresse': 'Adr',
            'sexe': 'M',
            'telephone': '+243800000050',
            'email': 'form.test@example.com',
            'categorie': self.cat_sans_emploi.pk,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_with_entreprise(self):
        form = StagiaireForm(data={
            'nom': 'Emploi',
            'postnom': 'Test',
            'prenom': 'A',
            'adresse': 'Adr',
            'sexe': 'F',
            'telephone': '+243800000060',
            'email': 'emploi.form@example.com',
            'categorie': self.cat_dans_emploi.pk,
            'entreprise': 'SNEL',
            'fonction': 'Ingénieur',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_empty_nom(self):
        form = StagiaireForm(data={
            'nom': '',
            'postnom': 'User',
            'prenom': '',
            'adresse': 'Adr',
            'sexe': 'M',
            'telephone': '+243800000070',
            'email': 'invalid@example.com',
            'categorie': self.cat_sans_emploi.pk,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('nom', form.errors)

    def test_form_invalid_email_duplicate(self):
        Stagiaire.objects.create(
            nom="Existing", postnom="User", prenom="",
            adresse="Adr", sexe="M", telephone="+243800000080",
            email="duplicate@example.com", categorie=self.cat_sans_emploi,
        )
        form = StagiaireForm(data={
            'nom': 'New',
            'postnom': 'User',
            'prenom': '',
            'adresse': 'Adr',
            'sexe': 'F',
            'telephone': '+243800000081',
            'email': 'duplicate@example.com',
            'categorie': self.cat_sans_emploi.pk,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class CategorieViewTests(TestCase):
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
        self.categorie = Categorie.objects.create(titre="sans emploi")

    def test_categorie_list_login_required(self):
        response = self.client.get(reverse("categories"))
        self.assertNotEqual(response.status_code, 200)

    def test_categorie_list_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("categories"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sans emploi")

    def test_categorie_create_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("categorie_create"), {
            "titre": "nouvelle catégorie",
            "active": True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Categorie.objects.filter(titre="nouvelle catégorie").exists())

    def test_categorie_create_duplicate_titre(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("categorie_create"), {
            "titre": "sans emploi",
            "active": True,
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "existe déjà", status_code=400)

    def test_categorie_detail_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("categorie", kwargs={"pk": self.categorie.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sans emploi")

    def test_categorie_update_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("categorie_update", kwargs={"pk": self.categorie.pk}),
            {"titre": "employé", "active": True},
        )
        self.assertEqual(response.status_code, 302)
        self.categorie.refresh_from_db()
        self.assertEqual(self.categorie.titre, "employé")

    def test_categorie_delete_as_manager(self):
        self.client.force_login(self.user)
        cat = Categorie.objects.create(titre="temp")
        response = self.client.post(reverse("categorie_delete", kwargs={"pk": cat.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Categorie.objects.filter(pk=cat.pk).exists())


class StagiaireViewTests(TestCase):
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
        self.categorie = Categorie.objects.create(titre="sans emploi")
        self.stagiaire = Stagiaire.objects.create(
            nom="Test", postnom="View", prenom="",
            adresse="Adr", sexe="M", telephone="+243800000090",
            email="stagiaire.view@example.com", categorie=self.categorie,
        )

    def test_stagiaire_list_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("stagiaires"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test")

    def test_stagiaire_detail_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("stagiaire", kwargs={"pk": self.stagiaire.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test")

    def test_stagiaire_create_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("stagiaire_create"), {
            "nom": "Nouveau",
            "postnom": "Stagiaire",
            "prenom": "A",
            "adresse": "Kinshasa",
            "sexe": "M",
            "telephone": "+243800000100",
            "email": "nouveau.stagiaire@example.com",
            "categorie": self.categorie.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Stagiaire.objects.filter(email="nouveau.stagiaire@example.com").exists())

    def test_stagiaire_create_invalid_form(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("stagiaire_create"), {
            "nom": "",
            "postnom": "",
            "prenom": "",
            "adresse": "",
            "sexe": "",
            "telephone": "",
            "email": "",
            "categorie": "",
        })
        self.assertEqual(response.status_code, 400)

    def test_stagiaire_update_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("stagiaire_update", kwargs={"pk": self.stagiaire.pk}),
            {
                "nom": "Modifié",
                "postnom": "Stagiaire",
                "prenom": "A",
                "adresse": "Kinshasa",
                "sexe": "M",
                "telephone": "+243800000100",
                "email": "modifie.stagiaire@example.com",
                "categorie": self.categorie.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.stagiaire.refresh_from_db()
        self.assertEqual(self.stagiaire.nom, "Modifié")

    def test_stagiaire_delete_as_manager(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("stagiaire_delete", kwargs={"pk": self.stagiaire.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Stagiaire.objects.filter(pk=self.stagiaire.pk).exists())

    def test_stagiaire_list_permission_denied_for_non_manager(self):
        user_no_perms = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="testpass123",
        )
        self.client.force_login(user_no_perms)
        # Regular users without Manager profile should get permission denied or empty list
        response = self.client.get(reverse("stagiaires"))
        # The view calls enforce_manage_permission which raises PermissionDenied
        self.assertEqual(response.status_code, 403)