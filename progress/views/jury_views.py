from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string

import io

from progress.models import Action, JuryPV, JuryNote, Stagiaire
from progress.forms import JuryPVForm, JuryNoteFormSet


@method_decorator(login_required, name="dispatch")
class JuryPVCustomView(View):
    template_name = "progress/jurypv_form.html"

    def dispatch(self, request, action_pk, *args, **kwargs):
        self.action = get_object_or_404(Action, pk=action_pk)
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
class JuryPVDeleteView(View):
    template_name = "progress/jurypv_confirm_delete.html"

    def get(self, request, action_pk):
        action = get_object_or_404(Action, pk=action_pk)
        jury_pv = get_object_or_404(JuryPV, action=action)
        context = {
            "jury_pv": jury_pv,
            "action": action,
            "titre": "Supprimer le PV Jury",
        }
        return render(request, self.template_name, context)

    def post(self, request, action_pk):
        action = get_object_or_404(Action, pk=action_pk)
        jury_pv = get_object_or_404(JuryPV, action=action)
        jury_pv.delete()
        messages.success(request, "PV Jury supprimé avec succès.")
        return redirect(reverse_lazy("action", kwargs={"pk": action_pk}))


@method_decorator(login_required, name="dispatch")
class JuryPVCoterView(View):
    template_name = "progress/jurypv_coter.html"

    def get(self, request, action_pk):
        action = get_object_or_404(Action, pk=action_pk)
        jury_pv = JuryPV.objects.filter(action=action).first()
        stagiaires = Stagiaire.objects.filter(
            detailaction__action=action, detailaction__active=True
        ).order_by("nom", "postnom", "prenom")

        stagiaires_notes = []
        for s in stagiaires:
            note_formation = None
            note_jury = None
            if jury_pv:
                note_obj = jury_pv.notes.filter(stagiaire=s).first()
                if note_obj:
                    note_formation = note_obj.note_formation
                    note_jury = note_obj.note_jury
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
        action = get_object_or_404(Action, pk=action_pk)
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
class JuryPVGeneratePDFView(View):
    def get(self, request, action_pk):
        action = get_object_or_404(Action, pk=action_pk)
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
