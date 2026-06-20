from users.models import Profile


def createprofile():
    profiles = [
        "Manager",
        "User",
        "Chef de filière",
        "Chef de service",
        "Formateur", # Ajout du profil Formateur
        "Caisse",       # Nouveau
        "Conseiller",   # Nouveau
        "Inspecteur",   # Nouveau
        "Pédagogique",  # Nouveau
    ]
    for profileName in profiles:
        temp = Profile.objects.filter(name=profileName).first()
        if temp is None:
            profile = Profile()
            profile.name = profileName
            profile.save()