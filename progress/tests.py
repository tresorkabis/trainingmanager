from datetime import date, time

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.urls import reverse
from django.test import TestCase

from progress.models import Action, ActionSchedule, Formateur, ModuleProgress, ModuleSubject, SessionProgress
from progress.services import ActionWorkflowService
from training.models import Filiere, Formation, Module, Service
from intern.models import Categorie, Stagiaire
from users.models import User


class ActionModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Filière A", service=self.service)
        self.formation = Formation.objects.create(
            nom="Formation A",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=1000,
        )

    def test_action_rejects_invalid_date_range(self):
        action = Action(
            description="Action A",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 9),
            formation=self.formation,
        )

        with self.assertRaises(ValidationError):
            action.save()

    def test_action_protects_formation_deletion(self):
        Action.objects.create(
            description="Action A",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 12),
            formation=self.formation,
        )

        with self.assertRaises(ProtectedError):
            self.formation.delete()


class ActionScheduleModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Filière A", service=self.service)
        self.formation = Formation.objects.create(
            nom="Formation A",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=1000,
        )
        self.action = Action.objects.create(
            description="Action A",
            date_debut=date(2026, 6, 8),
            date_fin=date(2026, 6, 14),
            formation=self.formation,
        )

    def test_action_schedule_rejects_invalid_time_range(self):
        schedule = ActionSchedule(
            action=self.action,
            jour_semaine=0,
            heure_debut=time(10, 0),
            heure_fin=time(9, 0),
        )

        with self.assertRaises(ValidationError):
            schedule.save()


class ModuleProgressModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Filière A", service=self.service)
        self.formation_a = Formation.objects.create(
            nom="Formation A",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=1000,
        )
        self.formation_b = Formation.objects.create(
            nom="Formation B",
            duree=12,
            duree_heures=24,
            filiere=self.filiere,
            cout=1200,
        )
        self.module_a = Module.objects.create(
            formation=self.formation_a,
            titre="Module A",
            duree_heures=5,
            ordre=1,
        )
        self.module_b = Module.objects.create(
            formation=self.formation_b,
            titre="Module B",
            duree_heures=5,
            ordre=1,
        )
        self.formateur = Formateur.objects.create(
            matricule="F001",
            nom="Doe",
            postnom="John",
            adresse="Adresse",
            telephone="0000000000",
            email="john.doe@example.com",
        )
        self.action = Action.objects.create(
            description="Action A",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 12),
            formation=self.formation_a,
        )

    def test_module_progress_rejects_module_from_other_formation(self):
        progress = ModuleProgress(
            formateur=self.formateur,
            action=self.action,
            module=self.module_b,
        )

        with self.assertRaises(ValidationError):
            progress.save()

    def test_module_progress_blocks_formateur_deletion(self):
        ModuleProgress.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module_a,
        )

        with self.assertRaises(ProtectedError):
            self.formateur.delete()


class SessionProgressModelTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Filière A", service=self.service)
        self.formation = Formation.objects.create(
            nom="Formation A",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=1000,
        )
        self.module = Module.objects.create(
            formation=self.formation,
            titre="Module A",
            duree_heures=5,
            ordre=1,
        )
        self.formateur = Formateur.objects.create(
            matricule="F002",
            nom="Smith",
            postnom="Anna",
            adresse="Adresse",
            telephone="1111111111",
            email="anna.smith@example.com",
        )
        self.action = Action.objects.create(
            description="Action A",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 12),
            formation=self.formation,
        )
        self.module_progress = ModuleProgress.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module,
        )
        ActionSchedule.objects.create(
            action=self.action,
            jour_semaine=2,
            heure_debut=time(14, 0),
            heure_fin=time(16, 0),
        )

    def test_session_progress_rejects_invalid_time_range(self):
        session = SessionProgress(
            module_progress=self.module_progress,
            planned_date=date(2026, 6, 10),
            planned_start_time=time(15, 0),
            planned_end_time=time(14, 0),
        )

        with self.assertRaises(ValidationError):
            session.save()

    def test_session_progress_rejects_planning_outside_action_schedule(self):
        session = SessionProgress(
            module_progress=self.module_progress,
            planned_date=date(2026, 6, 11),
            planned_start_time=time(8, 0),
            planned_end_time=time(10, 0),
        )

        with self.assertRaises(ValidationError):
            session.save()

    def test_session_progress_rejects_wrong_formateur(self):
        other_formateur = Formateur.objects.create(
            matricule="F003",
            nom="Other",
            postnom="Teacher",
            adresse="Adresse",
            telephone="2222222222",
            email="other.teacher@example.com",
        )

        session = SessionProgress(
            module_progress=self.module_progress,
            planned_date=date(2026, 6, 10),
            planned_start_time=time(8, 0),
            planned_end_time=time(10, 0),
            formateur=other_formateur,
        )

        with self.assertRaises(ValidationError):
            session.save()

    def test_realized_session_requires_real_date(self):
        session = SessionProgress(
            module_progress=self.module_progress,
            planned_date=date(2026, 6, 10),
            planned_start_time=time(8, 0),
            planned_end_time=time(10, 0),
            statut="REALISEE",
        )

        with self.assertRaises(ValidationError):
            session.save()

    def test_session_progress_blocks_module_progress_deletion(self):
        SessionProgress.objects.create(
            module_progress=self.module_progress,
            planned_date=date(2026, 6, 10),
            planned_start_time=time(14, 0),
            planned_end_time=time(16, 0),
            actual_date=date(2026, 6, 10),
            actual_start_time=time(14, 0),
            actual_end_time=time(16, 0),
            statut="REALISEE",
        )

        with self.assertRaises(ProtectedError):
            ModuleProgress.objects.filter(pk=self.module_progress.pk).delete()


class SessionPlanningWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="planner",
            email="planner@example.com",
            password="testpass123",
        )
        self.client.force_login(self.user)

        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Filière A", service=self.service)
        self.formation = Formation.objects.create(
            nom="Formation A",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=1000,
        )
        self.module = Module.objects.create(
            formation=self.formation,
            titre="Module A",
            description="Revoir les bases du module",
            duree_heures=5,
            ordre=1,
        )
        ModuleSubject.objects.create(
            module=self.module,
            titre="Introduction",
            description="Première partie",
            nombre_seances=2,
            ordre=1,
        )
        ModuleSubject.objects.create(
            module=self.module,
            titre="Pratique",
            description="Exercices guidés",
            nombre_seances=1,
            ordre=2,
        )
        self.formateur = Formateur.objects.create(
            matricule="F020",
            nom="Planner",
            postnom="Test",
            adresse="Adresse",
            telephone="6666666666",
            email="planner.test@example.com",
        )
        self.action = Action.objects.create(
            description="Action A",
            date_debut=date(2026, 6, 8),
            date_fin=date(2026, 6, 12),
            formation=self.formation,
        )
        self.module_progress = ModuleProgress.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module,
        )
        ActionSchedule.objects.create(
            action=self.action,
            jour_semaine=0,
            heure_debut=time(8, 0),
            heure_fin=time(10, 0),
        )
        ActionSchedule.objects.create(
            action=self.action,
            jour_semaine=2,
            heure_debut=time(14, 0),
            heure_fin=time(16, 0),
        )
        SessionProgress.objects.create(
            module_progress=self.module_progress,
            planned_date=date(2026, 6, 8),
            planned_start_time=time(8, 0),
            planned_end_time=time(10, 0),
            statut="PLANIFIEE",
        )

    def test_session_create_view_prefills_next_planning_slot(self):
        response = self.client.get(
            reverse("session_progress_create", kwargs={"module_progress_pk": self.module_progress.pk})
        )

        self.assertEqual(response.status_code, 200)
        defaults = response.context["next_session_defaults"]
        self.assertEqual(defaults["planned_date"], date(2026, 6, 10))
        self.assertEqual(defaults["planned_start_time"], time(14, 0))
        self.assertEqual(defaults["planned_end_time"], time(16, 0))
        self.assertEqual(defaults["planned_topics"], "Première partie")

        form = response.context["form"]
        self.assertEqual(form.initial["planned_date"], date(2026, 6, 10))
        self.assertEqual(form.initial["planned_start_time"], time(14, 0))
        self.assertEqual(form.initial["planned_end_time"], time(16, 0))
        self.assertEqual(form.initial["planned_topics"], "Première partie")


class ActionWorkflowServiceTests(TestCase):
    def setUp(self):
        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Filière A", service=self.service)
        self.formation = Formation.objects.create(
            nom="Formation A",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=1000,
        )
        self.module = Module.objects.create(
            formation=self.formation,
            titre="Module A",
            duree_heures=5,
            ordre=1,
        )
        self.formateur = Formateur.objects.create(
            matricule="F010",
            nom="Dupont",
            postnom="Marie",
            adresse="Adresse",
            telephone="3333333333",
            email="marie.dupont@example.com",
        )
        self.module.formateurs.add(self.formateur)
        self.action = Action.objects.create(
            description="Action A",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 12),
            formation=self.formation,
        )

    def test_sync_action_components_creates_module_progressions(self):
        assignments = {self.module.id: [self.formateur.id]}

        result = ActionWorkflowService.sync_action_components(self.action, assignments)

        self.assertEqual(result.created_progressions, 1)
        self.assertEqual(ModuleProgress.objects.filter(action=self.action).count(), 1)
        self.assertEqual(self.action.formateurs.count(), 1)

    def test_validate_module_assignments_rejects_non_eligible_formateur(self):
        other_formateur = Formateur.objects.create(
            matricule="F011",
            nom="Other",
            postnom="One",
            adresse="Adresse",
            telephone="4444444444",
            email="other.one@example.com",
        )

        errors = ActionWorkflowService.validate_module_assignments(
            self.formation,
            {self.module.id: [other_formateur.id]},
        )

        self.assertTrue(errors)


class DetailActionCreateViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
        )
        self.client.force_login(self.user)

        self.service = Service.objects.create(nom="Service A")
        self.filiere = Filiere.objects.create(nom="Filière A", service=self.service)
        self.formation = Formation.objects.create(
            nom="Formation A",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=1000,
        )
        self.action = Action.objects.create(
            description="Action A",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 12),
            formation=self.formation,
        )
        self.categorie = Categorie.objects.create(titre="sans emploi")
        self.stagiaire = Stagiaire.objects.create(
            nom="Kane",
            postnom="Aline",
            prenom="",
            adresse="Adresse",
            sexe="F",
            telephone="5555555555",
            email="aline.kane@example.com",
            categorie=self.categorie,
        )

    def test_detailaction_create_view_creates_inscription_and_redirects_to_next(self):
        response = self.client.post(
            reverse("detailaction_create"),
            {
                "stagiaire": self.stagiaire.pk,
                "action": self.action.pk,
                "next": "/progress/actions/1/#stagiaires",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("#stagiaires"))
        self.assertEqual(self.stagiaire.detailaction_set.count(), 1)

        response_repeat = self.client.post(
            reverse("detailaction_create"),
            {
                "stagiaire": self.stagiaire.pk,
                "action": self.action.pk,
                "next": "/progress/actions/1/#stagiaires",
            },
        )

        self.assertEqual(self.stagiaire.detailaction_set.count(), 1)
        self.assertEqual(response_repeat.status_code, 302)
