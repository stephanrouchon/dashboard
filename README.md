# Tableau de bord comptable

Application web Django qui lit un export d'écritures comptables et affiche des
indicateurs et états de synthèse.

## Prérequis

- Windows
- Python 3.15 ou plus récent (version déclarée dans `pyproject.toml`)
- Une connexion Internet pour installer Django

> `requirements.txt` ne contient pas actuellement une liste de dépendances
> installable. Le projet ne déclare pas non plus Django dans `pyproject.toml`.
> La procédure ci-dessous installe donc Django directement dans l'environnement
> virtuel.

## Installation et démarrage

Depuis la racine du dépôt, dans PowerShell :

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install Django
python manage.py migrate
python manage.py runserver
```

Ouvrir ensuite <http://127.0.0.1:8000/> dans un navigateur. Pour arrêter le
serveur de développement, utiliser `Ctrl+C` dans le terminal.

Si PowerShell interdit l'activation de l'environnement, il est possible
d'utiliser directement son interpréteur sans l'activer :

```powershell
.\.venv\Scripts\python.exe -m pip install Django
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

## Utilisation

Le menu latéral donne accès aux vues suivantes :

- **Tableau de bord** : nombre d'écritures et de comptes, totaux débit/crédit,
  charges, produits et résultat, avec une ventilation mensuelle.
- **Balance** : soldes par compte, filtrables par classe comptable ou par
  recherche sur le numéro et l'intitulé.
- **Compte de résultat** : produits et charges regroupés par mois.
- **Soldes intermédiaires de gestion** : calcul des soldes de gestion par mois.
- **Résultat analytique** : compte de résultat filtrable par plan et par poste.
- **Trésorerie** : évolution du solde cumulé des comptes de classe 5.
- **Journaux** : nombre d'écritures et totaux débit/crédit par journal.
- **Grand livre** : sélectionner un compte pour consulter ses écritures et son
  solde cumulé. La liste est paginée par 100 lignes.

Les filtres se font directement dans les formulaires des pages concernées.

## Données comptables

L'application charge les données depuis `data/ecritures.txt`. Pour utiliser un
autre export, remplacer ce fichier en conservant le format attendu :

- export texte encodé en Windows-1252, avec les champs séparés par `;` ;
- première ligne contenant les en-têtes ;
- dates au format `JJ/MM/AAAA` ;
- débits et crédits sous forme de nombres, avec une virgule ou un point comme
  séparateur décimal ;
- au moins 12 colonnes, avec la date en 3e position, le compte en 4e, le débit
  en 11e et le crédit en 12e. Les colonnes de plan et de poste analytiques,
  si elles sont présentes, sont en 14e et 15e position.

Le fichier est relu automatiquement lorsqu'il est modifié. Si l'export ne
respecte pas ce format, les vues comptables risquent de ne pas se charger.
Vérifier et sauvegarder le fichier avant de remplacer les données.

## Vérifications

Pour vérifier la configuration Django et lancer les tests de l'application :

```powershell
python manage.py check
python manage.py test app.comptabilite
```

## Développement

`python manage.py runserver` démarre uniquement le serveur de développement
Django. Il n'est pas destiné à exposer l'application en production.