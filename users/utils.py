from users.models import Profile


def createprofile():
    profiles = [
        "Manager",
        "User",
        "Chef de filière",  # Nouveau profil
        "Chef de service"   # Nouveau profil
    ]
    for profileName in profiles:
        temp = Profile.objects.filter(name=profileName).first()
        if temp is None:
            profile = Profile()
            profile.name = profileName
            profile.save()