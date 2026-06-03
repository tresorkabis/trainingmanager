from django.contrib import admin

from progress.models import Formateur, TypeAction, Action, DetailAction, ModuleProgress, SessionProgress, FormateurPerformance, Paiement

admin.site.register(Formateur)
admin.site.register(TypeAction)
admin.site.register(Action)
admin.site.register(DetailAction)
admin.site.register(ModuleProgress)
admin.site.register(SessionProgress)
admin.site.register(FormateurPerformance)
admin.site.register(Paiement)