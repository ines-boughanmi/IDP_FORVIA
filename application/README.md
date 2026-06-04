# 📊 IDP Monitoring Django Application

Application web Django avec intégration du Dashboard Power BI pour le suivi des contrats SAP P2P.

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.8+
- Pip ou Poetry
- Virtual Environment

### Installation

1. **Naviguer dans le dossier application** :
```bash
cd application
```

2. **Créer et activer un virtual environment** :

**Sur Windows (PowerShell)** :
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Sur Linux/Mac** :
```bash
python -m venv venv
source venv/bin/activate
```

3. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

4. **Appliquer les migrations** :
```bash
python manage.py migrate
```

5. **Créer un utilisateur administrateur** (optionnel) :
```bash
python manage.py createsuperuser
```

6. **Démarrer le serveur de développement** :
```bash
python manage.py runserver
```

L'application sera disponible à `http://127.0.0.1:8000/`

## 📱 Accès à l'Application

### Pages Disponibles

| Route | Description |
|-------|-------------|
| `/` | 🏠 Dashboard Power BI (page d'accueil) |
| `/dashboard/` | 📊 Accès alternatif au dashboard |
| `/admin/` | 🔐 Interface d'administration Django |

### Identifiants Admin

Si vous avez créé un superuser, utilisez :
- URL : `http://127.0.0.1:8000/admin/`
- Identifiants : ceux créés lors de `createsuperuser`

## 📦 Structure du Projet

```
application/
├── manage.py                    # Utilitaire de gestion Django
├── requirements.txt             # Dépendances Python
│
├── config/                      # Configuration principale
│   ├── settings.py             # Paramètres Django
│   ├── urls.py                 # Routage URL principal
│   ├── wsgi.py                 # Configuration WSGI
│   └── __init__.py
│
├── dashboard/                  # Application Django
│   ├── views.py               # Vues (logique métier)
│   ├── urls.py                # Routage de l'app
│   ├── models.py              # Modèles de données
│   ├── admin.py               # Configuration admin
│   ├── apps.py                # Configuration app
│   └── __init__.py
│
├── templates/                 # Modèles HTML
│   ├── base.html              # Template de base
│   └── dashboard/
│       └── powerbi_dashboard.html   # Dashboard Power BI
│
└── static/                    # Fichiers statiques (CSS, JS, images)
    ├── css/
    ├── js/
    └── images/
```

## ⚙️ Configuration Power BI

### Identifiants Actuels

```
Report ID  : a3b6aa0f-43e0-45a7-882f-82fdc64055b4
Tenant ID  : 5047bca2-da88-442e-a09a-d9b8af692adc
```

### Modifier les Identifiants

#### Option 1 : Via le Code
Éditer le fichier `dashboard/views.py` :
```python
POWERBI_REPORT_ID = 'votre-report-id'
POWERBI_TENANT_ID = 'votre-tenant-id'
```

#### Option 2 : Via l'Administration Django
1. Aller à `/admin/`
2. Naviguer à "Dashboard Configurations"
3. Modifier les identifiants Power BI

## 🔧 Configuration Supplémentaire

### Variables d'Environnement (Optionnel)

Créer un fichier `.env` :
```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Pour la Production

1. **Modifier `DEBUG` à `False` dans `settings.py`**
2. **Générer une nouvelle `SECRET_KEY`**
3. **Configurer `ALLOWED_HOSTS`** avec vos domaines
4. **Collecter les fichiers statiques** :
```bash
python manage.py collectstatic
```

## 📊 Intégration Power BI

L'application embed le rapport Power BI via une iframe sécurisée. 

### Points Importants

✅ **Sécurité** :
- L'authentification Power BI est gérée par Microsoft (`autoAuth=true`)
- La connexion utilise le protocol HTTPS

✅ **Responsive** :
- L'iframe s'adapte à tous les appareils
- Hauteur par défaut : 600px (modifiable)

✅ **Gestion Erreurs** :
- Affichage d'un message si le chargement échoue
- Indicateur de chargement

## 🛠️ Commandes Utiles

```bash
# Démarrer le serveur
python manage.py runserver

# Créer migrations
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Créer superuser
python manage.py createsuperuser

# Collecter fichiers statiques
python manage.py collectstatic

# Shell interactif Django
python manage.py shell

# Vérifier la configuration
python manage.py check
```

## 📝 Logs et Debugging

Les logs sont affichés dans la console. Vous pouvez les configurer davantage dans `config/settings.py`.

## 🚀 Déploiement

### Avec Gunicorn (Production)

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Avec Docker (Optionnel)

Un Dockerfile peut être créé si nécessaire.

## 📚 Documentation Supplémentaire

- [Django Official Docs](https://docs.djangoproject.com/)
- [Power BI Embedding Docs](https://docs.microsoft.com/en-us/power-bi/developer/embedded/)
- [Gunicorn Documentation](https://gunicorn.org/)

## 🤝 Support

Pour toute question ou problème, vérifiez :
1. Les logs de la console
2. Les erreurs navigateur (F12)
3. La page d'administration Django (`/admin/`)

## 📄 Licence

Propriétaire - Projet IDP Monitoring
