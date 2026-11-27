from django.db.utils import OperationalError, ProgrammingError

from users.models import (
    DEFAULT_INSTITUTION_ACRONYM,
    DEFAULT_INSTITUTION_NAME,
    InstitutionSettings,
)


def institution_identity(request):
    """Expose configurable institute branding to pages and printable documents."""
    try:
        identity = InstitutionSettings.objects.filter(pk=1).values_list(
            "institution_name", "institution_acronym"
        ).first()
    except (OperationalError, ProgrammingError):
        # Keep login and migration-time pages available before the first migration.
        identity = None
    name, acronym = identity or (None, None)
    return {
        "institution_name": name or DEFAULT_INSTITUTION_NAME,
        "institution_acronym": acronym or DEFAULT_INSTITUTION_ACRONYM,
    }
