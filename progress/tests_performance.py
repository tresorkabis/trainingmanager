from django.test import TestCase
from django.utils import timezone
from .models import Formateur, Action, FormateurPerformance
from .forms import FormateurPerformanceForm
from training.models import Formation, Module

class PerformanceTest(TestCase):
    def setUp(self):
        self.formateur = Formateur.objects.create(
            matricule="F001", nom="Kabise", postnom="Tresor", email="tresor@example.com"
        )
        self.formation = Formation.objects.create(nom="Django Pro")
        self.action = Action.objects.create(
            description="Session 2023", 
            date_debut=timezone.now().date(), 
            date_fin=timezone.now().date(),
            formation=self.formation
        )
        self.module = Module.objects.create(titre="Vues", formation=self.formation, ordre=1)

    def test_performance_creation(self):
        perf = FormateurPerformance.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module,
            note_pedagogique=4.5
        )
        self.assertEqual(perf.formateur.nom, "Kabise")
        self.assertIn("Kabise", str(perf))

    def test_multiple_sessions_for_same_module_are_allowed(self):
        """Vérifie qu'on peut enregistrer plusieurs séances pour le même trio formateur/action/module."""
        FormateurPerformance.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module,
            date_debut_reelle=timezone.now().date(),
        )
        second = FormateurPerformance.objects.create(
            formateur=self.formateur,
            action=self.action,
            module=self.module,
            date_debut_reelle=timezone.now().date(),
            heures_effectuees=2,
        )
        self.assertEqual(FormateurPerformance.objects.filter(
            formateur=self.formateur,
            action=self.action,
            module=self.module,
        ).count(), 2)
        self.assertIsNotNone(second.pk)

    def test_form_filters_modules_by_action(self):
        other_formation = Formation.objects.create(nom="Autre formation")
        other_module = Module.objects.create(titre="Sécurité", formation=other_formation, ordre=1)

        form = FormateurPerformanceForm(action=self.action)
        self.assertQuerysetEqual(
            form.fields["module"].queryset.order_by("pk"),
            [self.module.pk],
            transform=lambda module: module.pk,
        )
        self.assertNotIn(other_module.pk, list(form.fields["module"].queryset.values_list("pk", flat=True)))

    def test_form_rejects_module_outside_action_formation(self):
        other_formation = Formation.objects.create(nom="Autre formation")
        other_module = Module.objects.create(titre="Sécurité", formation=other_formation, ordre=1)

        form = FormateurPerformanceForm(
            data={
                "formateur": self.formateur.pk,
                "action": self.action.pk,
                "module": other_module.pk,
            },
            action=self.action,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("module", form.errors)
