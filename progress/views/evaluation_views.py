from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from progress.forms import ActionEvaluationForm
from progress.models import Action, ActionEvaluation


@method_decorator(login_required, name="dispatch")
class ActionEvaluationView(View):
    template_name = "progress/action_evaluation_form.html"

    def dispatch(self, request, *args, **kwargs):
        if getattr(getattr(request.user, "profile", None), "name", None) not in {"Pédagogique", "Manager"}:
            raise PermissionDenied("Cette fonction est réservée aux profils Pédagogique et Manager.")
        return super().dispatch(request, *args, **kwargs)

    def get_objects(self):
        action = get_object_or_404(Action.objects.select_related("formation"), pk=self.kwargs["action_pk"])
        evaluation = None
        if "evaluation_pk" in self.kwargs:
            evaluation = get_object_or_404(ActionEvaluation, pk=self.kwargs["evaluation_pk"], action=action)
        return action, evaluation

    def get(self, request, *args, **kwargs):
        action, evaluation = self.get_objects()
        form = ActionEvaluationForm(action=action, instance=evaluation)
        return render(request, self.template_name, self.get_context(action, evaluation, form))

    def post(self, request, *args, **kwargs):
        action, evaluation = self.get_objects()
        form = ActionEvaluationForm(request.POST, action=action, instance=evaluation)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.action = action
            evaluation.evaluateur = request.user
            evaluation.save()
            messages.success(request, "L’évaluation pédagogique a été enregistrée.")
            return redirect(f"{reverse('action', kwargs={'pk': action.pk})}#evaluations")
        return render(request, self.template_name, self.get_context(action, evaluation, form))

    @staticmethod
    def get_context(action, evaluation, form):
        return {
            "action": action,
            "evaluation": evaluation,
            "form": form,
            "title": "Modifier l’évaluation pédagogique" if evaluation else "Évaluer l’action",
        }
