from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string

import io

from progress.models import Action, JuryPV, JuryNote, Stagiaire
from progress.forms import JuryPVForm, JuryNoteFormSet
from progress.permissions import can_grade_jury, can_manage_action, can_view_action


class JuryActionPermissionMixin:
    def get_authorized_action(self, request, action_pk, permission):
        action = get_object_or_404(
            Action.objects.select_related("formation__filiere__service"), pk=action_pk
        )
        allowed = {
            "manage": can_manage_action,
            "grade": can_grade_jury,
            "view": can_view_action,
        }[permission](request.user, action)
        if not allowed:
            raise PermissionDenied("Vous n'avez pas accès à cette opération sur l'action.")
        return action


@method_decorator(login_required, name="dispatch")
class JuryPVCustomView(JuryActionPermissionMixin, View):
    template_name = "progress/jurypv_form.html"

    def dispatch(self, request, action_pk, *args, **kwargs):
        self.action = self.get_authorized_action(request, action_pk, "manage")
        self.jury_pv = JuryPV.objects.filter(action=self.action).first()
        return super().dispatch(request, action_pk, *args, **kwargs)

    def get(self, request, action_pk):
        all_stagiaires = []
        if self.jury_pv:
            form = JuryPVForm(instance=self.jury_pv)
            formset = JuryNoteFormSet(
                instance=self.jury_pv,
                prefix="notes",
                form_kwargs={"action": self.action},
            )
            titre = "Modifier le PV Jury"
            all_stagiaires = Stagiaire.objects.filter(
                detailaction__action=self.action, detailaction__active=True
            ).order_by("nom", "postnom", "prenom")
        else:
            from datetime import date
            initial = {}
            if self.action.date_jury:
                initial["date_jury"] = self.action.date_jury.strftime("%Y-%m-%d")
            else:
                initial["date_jury"] = date.today().strftime("%Y-%m-%d")
            form = JuryPVForm(initial=initial)
            all_stagiaires = Stagiaire.objects.filter(
                detailaction__action=self.action, detailaction__active=True
            ).order_by("nom", "postnom", "prenom")
            notes_data = [
                {"stagiaire": s.pk, "note_formation": None, "note_jury": None}
                for s in all_stagiaires
            ]
            formset = JuryNoteFormSet(
                queryset=JuryNote.objects.none(),
                prefix="notes",
                initial=notes_data,
                form_kwargs={"action": self.action},
            )
            titre = "Ajouter le PV Jury"

        context = {
            "form": form,
            "formset": formset,
            "action": self.action,
            "jury_pv": self.jury_pv,
            "titre": titre,
            "all_stagiaires": all_stagiaires,
        }
        return render(request, self.template_name, context)

    def post(self, request, action_pk):
        if self.jury_pv:
            form = JuryPVForm(request.POST, request.FILES, instance=self.jury_pv)
            titre = "Modifier le PV Jury"
        else:
            form = JuryPVForm(request.POST, request.FILES)
            titre = "Ajouter le PV Jury"

        formset = JuryNoteFormSet(
            request.POST,
            prefix="notes",
            form_kwargs={"action": self.action},
        )

        if form.is_valid() and formset.is_valid():
            jury_pv = form.save(commit=False)
            jury_pv.action = self.action
            jury_pv.date_jury = self.action.date_jury
            jury_pv.save()

            instances = formset.save(commit=False)
            for instance in instances:
                instance.jury_pv = jury_pv
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "PV Jury enregistré avec succès.")
            return redirect(reverse_lazy("action", kwargs={"pk": action_pk}))

        context = {
            "form": form,
            "formset": formset,
            "action": self.action,
            "jury_pv": self.jury_pv,
            "titre": titre,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class JuryPVDeleteView(JuryActionPermissionMixin, View):
    template_name = "progress/jurypv_confirm_delete.html"

    def get(self, request, action_pk):
        action = self.get_authorized_action(request, action_pk, "manage")
        jury_pv = get_object_or_404(JuryPV, action=action)
        context = {
            "jury_pv": jury_pv,
            "action": action,
            "titre": "Supprimer le PV Jury",
        }
        return render(request, self.template_name, context)

    def post(self, request, action_pk):
        action = self.get_authorized_action(request, action_pk, "manage")
        jury_pv = get_object_or_404(JuryPV, action=action)
        jury_pv.delete()
        messages.success(request, "PV Jury supprimé avec succès.")
        return redirect(reverse_lazy("action", kwargs={"pk": action_pk}))


@method_decorator(login_required, name="dispatch")
class JuryPVCoterView(JuryActionPermissionMixin, View):
    template_name = "progress/jurypv_coter.html"

    def get(self, request, action_pk):
        action = self.get_authorized_action(request, action_pk, "grade")
        jury_pv = JuryPV.objects.filter(action=action).first()
        stagiaires = Stagiaire.objects.filter(
            detailaction__action=action, detailaction__active=True
        ).order_by("nom", "postnom", "prenom")

        notes_by_stagiaire = {
            note.stagiaire_id: note
            for note in jury_pv.notes.all()
        } if jury_pv else {}
        stagiaires_notes = []
        for s in stagiaires:
            note_obj = notes_by_stagiaire.get(s.pk)
            note_formation = note_obj.note_formation if note_obj else None
            note_jury = note_obj.note_jury if note_obj else None
            total = (note_formation or 0) + (note_jury or 0)
            stagiaires_notes.append({
                "stagiaire": s,
                "note_formation": note_formation,
                "note_jury": note_jury,
                "total": total,
            })

        return render(request, self.template_name, {
            "action": action,
            "stagiaires_notes": stagiaires_notes,
        })

    def post(self, request, action_pk):
        action = self.get_authorized_action(request, action_pk, "grade")
        jury_pv = JuryPV.objects.filter(action=action).first()
        if not jury_pv:
            messages.error(request, "Veuillez d'abord créer le PV Jury avant de saisir les notes.")
            return redirect(reverse_lazy("jurypv_form", kwargs={"action_pk": action_pk}))

        stagiaires = Stagiaire.objects.filter(
            detailaction__action=action, detailaction__active=True
        ).order_by("nom", "postnom", "prenom")

        for s in stagiaires:
            nf = request.POST.get(f"note_formation_{s.pk}")
            nj = request.POST.get(f"note_jury_{s.pk}")
            if nf is not None or nj is not None:
                note_obj, _ = JuryNote.objects.get_or_create(
                    jury_pv=jury_pv,
                    stagiaire=s,
                    defaults={
                        'note_formation': nf if nf not in (None, '') else 0,
                        'note_jury': nj if nj not in (None, '') else 0,
                    }
                )
                if not _:
                    note_obj.note_formation = nf if nf not in (None, '') else 0
                    note_obj.note_jury = nj if nj not in (None, '') else 0
                    note_obj.save()

        messages.success(request, "Notes enregistrées avec succès.")
        return redirect(reverse_lazy("action", kwargs={"pk": action_pk}))


@method_decorator(login_required, name="dispatch")
class JuryPVGeneratePDFView(JuryActionPermissionMixin, View):
    def get(self, request, action_pk):
        action = self.get_authorized_action(request, action_pk, "view")
        jury_pv = get_object_or_404(JuryPV, action=action)

        try:
            from xhtml2pdf import pisa
        except ImportError:
            messages.error(request, "xhtml2pdf n'est pas installé. Impossible de générer le PDF.")
            return redirect(reverse_lazy("action", kwargs={"pk": action_pk}))

        stagiaires = Stagiaire.objects.filter(
            detailaction__action=action, detailaction__active=True
        ).order_by("nom", "postnom", "prenom")
        notes_map = {n.stagiaire_id: n for n in jury_pv.notes.all()}
        stagiaires_notes = []
        for s in stagiaires:
            note = notes_map.get(s.pk)
            total = (note.note_formation or 0) + (note.note_jury or 0) if note else 0
            if note and note.note_jury is not None and note.note_jury > 0:
                stagiaires_notes.append({
                    "stagiaire": s,
                    "note_formation": note.note_formation,
                    "note_jury": note.note_jury,
                    "total": total,
                })
        html_string = render_to_string("progress/jurypv_pdf.html", {
            "pv": jury_pv,
            "stagiaires_notes": stagiaires_notes,
        })

        # Génération du PDF avec xhtml2pdf (pur-Python, compatible avec les
        # environnements serverless comme Vercel — contrairement à WeasyPrint).
        buffer = io.BytesIO()
        pdf = pisa.CreatePDF(
            src=io.BytesIO(html_string.encode("utf-8")),
            dest=buffer,
            encoding="utf-8",
        )
        if pdf.err:
            messages.error(request, "Une erreur est survenue lors de la génération du PDF.")
            return redirect(reverse_lazy("action", kwargs={"pk": action_pk}))

        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="PV_Jury_{}.pdf"'.format(action.pk)
        return response
