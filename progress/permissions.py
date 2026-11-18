"""Shared action access checks used by action and jury views."""


ACTION_MANAGE_PROFILES = {"Manager", "Chef de filière", "Chef de service"}
ACTION_VIEW_PROFILES = {"Caisse", "Conseiller", "Inspecteur", "Pédagogique", "Formateur"}


def _profile_name(user):
    return getattr(getattr(user, "profile", None), "name", None)


def _within_action_scope(user, action, profile_name):
    if profile_name == "Chef de filière":
        return bool(user.filiere_id and user.filiere_id == action.formation.filiere_id)
    if profile_name == "Chef de service":
        return bool(
            user.service_id
            and action.formation.filiere.service_id == user.service_id
        )
    return False


def can_manage_action(user, action):
    if not user.is_authenticated:
        return False
    name = _profile_name(user)
    if user.is_superuser or name == "Manager":
        return True
    return name in ACTION_MANAGE_PROFILES and _within_action_scope(user, action, name)


def can_view_action(user, action):
    if can_manage_action(user, action):
        return True
    return user.is_authenticated and _profile_name(user) in ACTION_VIEW_PROFILES


def can_grade_jury(user, action):
    return can_manage_action(user, action) or (
        user.is_authenticated and _profile_name(user) == "Pédagogique"
    )
