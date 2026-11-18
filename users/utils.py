from users.models import Profile


DEFAULT_PROFILE_NAMES = (
    "Manager",
    "User",
    "Chef de filière",
    "Chef de service",
    "Formateur",
    "Caisse",
    "Conseiller",
    "Inspecteur",
    "Pédagogique",
)


def createprofile():
    """Crée les profils standards absents et retourne leur nombre."""
    created = 0
    for name in DEFAULT_PROFILE_NAMES:
        _, was_created = Profile.objects.get_or_create(name=name)
        created += int(was_created)
    return created
