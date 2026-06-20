from django.contrib import admin

from progress.models import Formateur, TypeAction, Action, ActionSchedule, DetailAction, ModuleProgress, ModuleSubject, SessionProgress, FormateurPerformance, Paiement, JuryPV, JuryNote

admin.site.register(Formateur)
admin.site.register(TypeAction)
admin.site.register(Action)
admin.site.register(ActionSchedule)
admin.site.register(DetailAction)
admin.site.register(ModuleProgress)
admin.site.register(ModuleSubject)
admin.site.register(SessionProgress)
admin.site.register(FormateurPerformance)
admin.site.register(Paiement)
admin.site.register(JuryPV)
admin.site.register(JuryNote)
