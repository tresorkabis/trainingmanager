from datetime import date, time

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.urls import reverse
from django.test import TestCase

from progress.models import Action, ActionSchedule, Formateur, ModuleProgress, ModuleSubject, SessionProgress, Paiement
from progress.services import ActionWorkflowService
from training.models import Filiere, Formation, Module, Service
from intern.models import Categorie, Stagiaire
from users.models import User, Profile


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

    def test_updating_planned_session_to_realized_moves_action_to_in_progress(self):
        second_module = Module.objects.create(
            formation=self.formation_a,
            titre="Module A2",
            duree_heures=5,
            ordre=2,
        )
        progression = ModuleProgress.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module_a,
        )
        ModuleProgress.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=second_module,
        )

        session = SessionProgress.objects.create(
            module_progress=progression,
            planned_date=date(2026, 6, 10),
            planned_start_time=time(8, 0),
            planned_end_time=time(13, 0),
        )
        self.action.refresh_from_db()
        self.assertEqual(self.action.statut, "PLANIFIEE")

        session.actual_date = date(2026, 6, 10)
        session.actual_start_time = time(8, 0)
        session.actual_end_time = time(13, 0)
        session.statut = "REALISEE"
        session.save()

        progression.refresh_from_db()
        self.action.refresh_from_db()
        self.assertEqual(progression.statut_module, "TE")
        self.assertEqual(self.action.statut, "EN_COURS")

    def test_realized_session_without_actual_times_starts_module(self):
        progression = ModuleProgress.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module_a,
        )

        SessionProgress.objects.create(
            module_progress=progression,
            planned_date=date(2026, 6, 10),
            planned_start_time=time(8, 0),
            planned_end_time=time(13, 0),
            actual_date=date(2026, 6, 10),
            statut="REALISEE",
        )

        progression.refresh_from_db()
        self.action.refresh_from_db()
        self.assertEqual(progression.statut_module, "EC")
        self.assertEqual(self.action.statut, "EN_COURS")


class ModuleProgressCreateViewTests(TestCase):
    def setUp(self):
        profile = Profile.objects.create(name="Manager")
        user = User.objects.create_user(
            username="progress_manager",
            email="progress_manager@example.com",
            password="testpass123",
            profile=profile,
        )
        self.client.force_login(user)

        service = Service.objects.create(nom="Service Progression")
        filiere = Filiere.objects.create(nom="Filière Progression", service=service)
        formation = Formation.objects.create(
            nom="Formation Progression",
            duree=10,
            duree_heures=20,
            filiere=filiere,
        )
        self.action = Action.objects.create(
            description="Session de progression",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 12),
            formation=formation,
        )
        self.module = Module.objects.create(
            formation=formation,
            titre="Module de progression",
            duree_heures=5,
        )
        self.formateur = Formateur.objects.create(
            matricule="FP001",
            nom="Formateur",
            postnom="Autorisé",
            adresse="Adresse",
            telephone="0000000100",
            email="formateur.progression@example.com",
        )
        self.module.formateurs.add(self.formateur)
        self.progression = ModuleProgress.objects.create(
            action=self.action,
            module=self.module,
            formateur=self.formateur,
        )

    def test_create_assistant_uses_assigned_formateur_and_updates_progression(self):
        url = reverse("module_progress_create")
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "module-progress-wizard-data")
        self.assertContains(get_response, "Choisir le module et son formateur")

        post_response = self.client.post(url, {
            "action": self.action.pk,
            "module": self.module.pk,
            "formateur": self.formateur.pk,
            "statut_module": "NC",
            "date_debut_reelle": "",
            "date_fin_reelle": "",
            "note": "15",
            "commentaires": "Saisie de progression",
        })

        self.assertRedirects(post_response, reverse("module_progressions"), fetch_redirect_response=False)
        self.assertEqual(ModuleProgress.objects.count(), 1)
        self.progression.refresh_from_db()
        self.assertEqual(self.progression.note, 15)
        self.assertEqual(self.progression.commentaires, "Saisie de progression")

    def test_create_assistant_rejects_formateur_not_assigned_to_module(self):
        unauthorized_formateur = Formateur.objects.create(
            matricule="FP002",
            nom="Formateur",
            postnom="Non autorisé",
            adresse="Adresse",
            telephone="0000000101",
            email="formateur.nonautorise@example.com",
        )

        response = self.client.post(reverse("module_progress_create"), {
            "action": self.action.pk,
            "module": self.module.pk,
            "formateur": unauthorized_formateur.pk,
            "statut_module": "NC",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ModuleProgress.objects.count(), 1)
        self.assertIn("formateur", response.context["form"].errors)

    def test_module_progress_list_filters_by_action(self):
        other_action = Action.objects.create(
            description="Autre session",
            date_debut=date(2026, 7, 10),
            date_fin=date(2026, 7, 12),
            formation=self.action.formation,
        )
        other_progression = ModuleProgress.objects.create(
            action=other_action,
            module=self.module,
            formateur=self.formateur,
        )

        response = self.client.get(
            reverse("module_progressions"),
            {"action": self.action.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [progress.pk for progress in response.context["module_progressions"]],
            [self.progression.pk],
        )
        self.assertContains(response, "Toutes les actions")


class ActionDetailSessionDateTests(TestCase):
    def setUp(self):
        profile = Profile.objects.create(name="Manager")
        user = User.objects.create_user(
            username="action_detail_manager",
            email="action_detail_manager@example.com",
            password="testpass123",
            profile=profile,
        )
        self.client.force_login(user)

        service = Service.objects.create(nom="Service Action Detail")
        filiere = Filiere.objects.create(nom="Filière Action Detail", service=service)
        formation = Formation.objects.create(
            nom="Formation Action Detail",
            duree=10,
            duree_heures=20,
            filiere=filiere,
        )
        module = Module.objects.create(
            formation=formation,
            titre="Module Dates",
            duree_heures=4,
        )
        subject = ModuleSubject.objects.create(module=module, titre="Introduction", ordre=1)
        formateur = Formateur.objects.create(
            matricule="AD001",
            nom="Formatrice",
            postnom="Test",
            adresse="Adresse",
            telephone="0000000200",
            email="formatrice.action.detail@example.com",
        )
        action = Action.objects.create(
            description="Action avec dates",
            date_debut=date(2026, 6, 1),
            date_fin=date(2026, 6, 30),
            formation=formation,
        )
        progression = ModuleProgress.objects.create(
            formateur=formateur,
            action=action,
            module=module,
        )
        self.progression = progression
        SessionProgress.objects.create(
            module_progress=progression,
            planned_date=date(2026, 6, 10),
            planned_start_time=time(9, 0),
            planned_end_time=time(11, 0),
            planned_topics=subject.titre,
            actual_date=date(2026, 6, 11),
            actual_start_time=time(10, 0),
            actual_end_time=time(12, 0),
            topics_covered=subject.titre,
            statut="REALISEE",
        )
        self.action = action

    def test_action_modules_tab_shows_planned_and_actual_dates(self):
        response = self.client.get(reverse("action", kwargs={"pk": self.action.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "module-schedule-chart")
        self.assertEqual(response.context["evolution_chart"]["categories"], ["10/06/2026", "11/06/2026"])

    def test_module_progress_detail_button_opens_subject_chart(self):
        action_response = self.client.get(reverse("action", kwargs={"pk": self.action.pk}))
        detail_response = self.client.get(
            reverse("module_progress_detail", kwargs={"pk": self.progression.pk})
        )

        self.assertContains(action_response, "Voir la progression")
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "progression-subject-chart")
        self.assertEqual(
            detail_response.context["progression_chart_data"]["planned"],
            [{"x": "2026-06-10", "y": 0}],
        )
        self.assertEqual(
            detail_response.context["progression_chart_data"]["actual"],
            [{"x": "2026-06-11", "y": 0}],
        )


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
        self.profile = Profile.objects.create(name="Manager")
        self.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
            profile=self.profile,
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


class PaiementListViewTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(name="Caisse")
        self.user = User.objects.create_user(
            username="caisse_test",
            email="caisse_test@example.com",
            password="testpass123",
            profile=self.profile,
        )
        self.client.force_login(self.user)

        self.service = Service.objects.create(nom="Service P")
        self.filiere = Filiere.objects.create(nom="Filière P", service=self.service)
        self.formation = Formation.objects.create(
            nom="Formation P",
            duree=10,
            duree_heures=20,
            filiere=self.filiere,
            cout=100,
        )
        self.action = Action.objects.create(
            description="Action P",
            date_debut=date(2026, 6, 10),
            date_fin=date(2026, 6, 12),
            formation=self.formation,
        )
        self.categorie = Categorie.objects.create(titre="sans emploi")
        self.stagiaire = Stagiaire.objects.create(
            nom="Test",
            postnom="Paiement",
            prenom="",
            adresse="Adresse",
            sexe="M",
            telephone="1234567890",
            email="test.paiement@example.com",
            categorie=self.categorie,
        )
        # Create a payment with surplus (exceeds formation cost to test |abs filter)
        Paiement.objects.create(
            stagiaire=self.stagiaire,
            action=self.action,
            montant=150,
            date_paiement=date.today(),
            mode_paiement="ESPECES",
        )

    def test_paiement_list_view_renders_successfully_including_negative_balances(self):
        from progress.templatetags.tm_tags import tm_abs_filter
        self.assertEqual(tm_abs_filter(-50), 50.0)
        self.assertEqual(tm_abs_filter(50), 50.0)
        self.assertEqual(tm_abs_filter("invalid"), "invalid")

        response = self.client.get(reverse("paiements"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paiements")

