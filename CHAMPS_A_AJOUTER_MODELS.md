# Champs a ajouter aux models

Ce document liste les champs recommandes a ajouter aux models existants pour rendre l'application plus robuste, plus exploitable en gestion, et plus facile a faire evoluer.

Les champs ci-dessous sont des propositions. Ils sont a valider selon les regles metier du projet.

## `intern.Categorie`

Champs proposes :

- `code = models.CharField(max_length=20, unique=True, blank=True, null=True)`
  Permet d'identifier une categorie de facon courte et stable.
- `description = models.TextField(blank=True, null=True)`
  Utile si le titre seul ne suffit pas pour expliquer la categorie.

## `intern.Stagiaire`

Champs proposes :

- `email = models.EmailField(blank=True, null=True, unique=True)`
  Permet les notifications et evite les doublons.
- `date_naissance = models.DateField(blank=True, null=True)`
  Important pour l'identification et certains reportings.
- `lieu_naissance = models.CharField(max_length=100, blank=True, null=True)`
  Souvent utile dans les fiches administratives.
- `numero_piece = models.CharField(max_length=50, blank=True, null=True, unique=True)`
  Pour la piece d'identite ou le numero matricule interne.
- `niveau_etude = models.CharField(max_length=100, blank=True, null=True)`
  Utile pour les statistiques et l'orientation.
- `photo = models.ImageField(upload_to='stagiaires/', blank=True, null=True)`
  Pratique pour le suivi visuel.
- Nationalité
- Nom du père
- Nom de la mère
- un stagiaire a une ou plusieurs études faites

## `training.Service`

Champs proposes :

- `code = models.CharField(max_length=20, unique=True, blank=True, null=True)`
  Donne une reference metier stable.
- `description = models.TextField(blank=True, null=True)`
  Aide a documenter le role du service.
- `responsable = models.CharField(max_length=150, blank=True, null=True)`
  Permet d'identifier le contact principal.

## `training.Filiere`

Champs proposes :

- `code = models.CharField(max_length=20, unique=True, blank=True, null=True)`
  Pratique pour les affichages et imports.
- `description = models.TextField(blank=True, null=True)`
  Donne plus de contexte que le nom seul.
- `niveau = models.CharField(max_length=50, blank=True, null=True)`
  Exemple : debutant, intermediaire, avance.

## `training.Formation`

Champs proposes :

- `code = models.CharField(max_length=20, unique=True, blank=True, null=True)`
  Permet de gerer une reference unique par formation.
- `description = models.TextField(blank=True, null=True)`
  Pour presenter clairement le contenu.
- `cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)`
  Plus adapte que `FloatField` pour la gestion financiere.
- `capacite = models.PositiveIntegerField(default=0)`
  Definit le nombre maximum de stagiaires.
- `prerequis = models.TextField(blank=True, null=True)`
  Important pour l'inscription.

Remarque :

- `fraismateriels` gagnerait a etre remplace par un `DecimalField` plutot qu'un `FloatField`.

## `progress.TypeAction`

Champs proposes :

- `description = models.TextField(blank=True, null=True)`
  Pour preciser la nature du type d'action.
- `ordre = models.PositiveIntegerField(default=0)`
  Utile si les types doivent etre tries dans un ordre metier.

## `progress.Formateur`

Champs proposes :

- `prenom = models.CharField(max_length=50, blank=True, null=True)`
  Pour completer l'identite.
- `specialite = models.CharField(max_length=150, blank=True, null=True)`
  Permet d'assigner les bonnes formations.
- `fonction = models.CharField(max_length=100, blank=True, null=True)`
  Utile pour distinguer consultant, instructeur, superviseur, etc.
- `date_embauche = models.DateField(blank=True, null=True)`
  Peut servir a l'historique RH.
- `photo = models.ImageField(upload_to='formateurs/', blank=True, null=True)`
  Pratique dans les fiches et listings.

## `progress.Action`

Champs proposes :

- `code = models.CharField(max_length=20, unique=True, blank=True, null=True)`
  Identifiant court pour chaque action.
- `type_action = models.ForeignKey(TypeAction, on_delete=models.SET_NULL, null=True, blank=True)`
  Semble manque au vu du modele actuel.
- `formateur = models.ForeignKey(Formateur, on_delete=models.SET_NULL, null=True, blank=True)`
  Important pour savoir qui anime l'action.
- `lieu = models.CharField(max_length=150, blank=True, null=True)`
  Necessaire pour la logistique.
- `statut = models.CharField(max_length=30, blank=True, null=True)`
  Exemple : planifiee, en cours, terminee, annulee.
- `observation = models.TextField(blank=True, null=True)`
  Pour garder des notes de suivi.

## `progress.DetailAction`

Champs proposes :

- `presence = models.BooleanField(default=False)`
  Permet de suivre la participation.
- `note = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)`
  Pour les evaluations.
- `resultat = models.CharField(max_length=50, blank=True, null=True)`
  Exemple : admis, ajourne, abandon.
- `commentaire = models.TextField(blank=True, null=True)`
  Pour les remarques du formateur.
- `date_evaluation = models.DateField(blank=True, null=True)`
  Utile si une note est saisie plus tard.

## `users.Profile`

Champs proposes :

- `description = models.TextField(blank=True, null=True)`
  Pour documenter le role du profil.
- `code = models.CharField(max_length=30, unique=True, blank=True, null=True)`
  Permet une reference stable en base.

## `users.User`

Champs proposes :

- `telephone = models.CharField(max_length=20, blank=True, null=True)`
  Utile pour joindre l'utilisateur.
- `adresse = models.CharField(max_length=255, blank=True, null=True)`
  Selon les besoins administratifs.
- `fonction = models.CharField(max_length=100, blank=True, null=True)`
  Permet de distinguer les roles terrain.
- `is_verified = models.BooleanField(default=False)`
  Utile si vous ajoutez une logique de verification.
- `last_password_change = models.DateTimeField(blank=True, null=True)`
  Pratique pour la securite et le suivi.

## Priorite recommandee

Si vous voulez avancer vite, commencez par ajouter ces champs en premier :

1. `Action.type_action`
2. `Action.formateur`
3. `DetailAction.presence`
4. `DetailAction.note`
5. `Stagiaire.email`
6. `Formation.code`
7. `Formation.capacite`
8. `Formateur.specialite`

## Suite logique apres ajout

Apres ajout des champs :

1. Creer les migrations.
2. Mettre a jour les formulaires et vues de creation.
3. Adapter l'admin Django.
4. Ajouter des tests de creation et de validation.
