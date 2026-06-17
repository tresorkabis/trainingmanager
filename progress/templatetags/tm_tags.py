from django import template

register = template.Library()

@register.inclusion_tag('progress/tm_hero.html')
def tm_hero(title, subtitle, icon, actions=None, stats=None, theme='primary'):
    """
    Génère la section Hero standardisée.
    - title: Titre H3
    - subtitle: Texte de description
    - icon: Classe CSS de l'icône (ex: 'bi bi-wallet-fill')
    - actions: Liste de dictionnaires {'label': ..., 'url': ..., 'icon': ..., 'class': ...}
    - stats: Liste de dictionnaires {'label': ..., 'value': ...}
    - theme: 'primary', 'success', 'danger', 'warning', 'info'
    """
    return {
        'title': title,
        'subtitle': subtitle,
        'icon': icon,
        'actions': actions,
        'stats': stats,
        'theme': theme,
    }