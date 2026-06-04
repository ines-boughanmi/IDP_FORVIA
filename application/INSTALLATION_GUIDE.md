# 🚀 Guide d'Installation Complet - Django Application

## 📋 Table des Matières
1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Démarrage](#démarrage)
5. [Dépannage](#dépannage)

---

## ✅ Prérequis

### Système d'Exploitation
- **Windows 10+** / **macOS** / **Linux** (Ubuntu 20.04+)

### Logiciels Requis
- **Python 3.8+** → [Télécharger Python](https://www.python.org/downloads/)
- **Pip** (inclus avec Python)
- **Git** (optionnel) → [Télécharger Git](https://git-scm.com/)

### Vérifier l'Installation

**Windows (PowerShell)** :
```powershell
python --version
pip --version
```

**Linux/Mac (Terminal)** :
```bash
python3 --version
pip3 --version
```

---

## 💾 Installation

### Étape 1 : Naviguer dans le Dossier

**Windows (PowerShell)** :
```powershell
cd C:\Users\1boughai\Desktop\IDP-Monitoring-Project\application
```

**Linux/Mac (Terminal)** :
```bash
cd ~/Desktop/IDP-Monitoring-Project/application
```

### Étape 2 : Créer un Virtual Environment

**Windows (PowerShell)** :
```powershell
python -m venv venv
```

**Linux/Mac (Terminal)** :
```bash
python3 -m venv venv
```

### Étape 3 : Activer le Virtual Environment

**Windows (PowerShell)** :
```powershell
.\venv\Scripts\Activate.ps1
```

> ⚠️ Si vous avez une erreur de politique d'exécution, tapez :
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

**Windows (Command Prompt)** :
```cmd
.\venv\Scripts\activate.bat
```

**Linux/Mac (Terminal)** :
```bash
source venv/bin/activate
```

> ✅ Vous devriez voir `(venv)` au début de votre terminal

### Étape 4 : Installer les Dépendances

```bash
pip install -r requirements.txt
```

### Étape 5 : Initialiser la Base de Données

```bash
python manage.py migrate
```

> ✅ Cela crée le fichier `db.sqlite3`

### Étape 6 : (Optionnel) Créer un Utilisateur Admin

```bash
python manage.py createsuperuser
```

Répondez aux questions :
- **Username** : `admin` (ou votre choix)
- **Email** : `admin@example.com`
- **Password** : Entrez un mot de passe sécurisé

---

## ⚙️ Configuration

### Configuration Power BI

Les identifiants sont actuellement configurés dans `dashboard/views.py` :

```python
POWERBI_REPORT_ID = 'a3b6aa0f-43e0-45a7-882f-82fdc64055b4'
POWERBI_TENANT_ID = '5047bca2-da88-442e-a09a-d9b8af692adc'
```

Pour modifier les identifiants :

**Option 1 : Éditer le fichier Python**
```
dashboard/views.py → lignes 15-16
```

**Option 2 : Via l'interface Admin Django**
1. Démarrer le serveur
2. Aller à `http://127.0.0.1:8000/admin/`
3. Se connecter avec les identifiants créés
4. Aller à "Dashboard Configurations"
5. Modifier les valeurs

### Configuration Django (Optionnel)

Éditer `config/settings.py` pour personnaliser :
- `DEBUG` (développement/production)
- `ALLOWED_HOSTS` (domaines autorisés)
- `LANGUAGE_CODE` (langue)
- `TIME_ZONE` (fuseau horaire)

---

## 🎯 Démarrage

### Option 1 : Script Automatisé (Recommandé)

**Windows** :
```powershell
.\run_dev.bat
```

**Linux/Mac** :
```bash
chmod +x run_dev.sh
./run_dev.sh
```

### Option 2 : Manuel

1. **Activer le virtual environment** (voir Étape 3)

2. **Démarrer le serveur** :
```bash
python manage.py runserver
```

3. **Accéder à l'application** :
- Dashboard : http://127.0.0.1:8000/
- Admin Panel : http://127.0.0.1:8000/admin/

### Arrêter le Serveur

Appuyez sur **Ctrl+C** dans le terminal

---

## 🔧 Dépannage

### Problème : "Erreur de politique d'exécution"

**Solution (Windows PowerShell)** :
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### Problème : "ModuleNotFoundError: No module named 'django'"

**Solution** :
```bash
pip install -r requirements.txt
```

### Problème : "Port 8000 déjà utilisé"

**Solution 1 : Changer de port**
```bash
python manage.py runserver 8001
```

**Solution 2 : Trouver le processus (Windows)**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Problème : "Database connection error"

**Solution** :
```bash
python manage.py migrate
```

### Problème : Dashboard Power BI ne charge pas

**Vérifications** :
1. Connectez-vous à Power BI (https://powerbi.microsoft.com)
2. Vérifiez que vous avez accès au rapport
3. Vérifiez les identifiants dans `dashboard/views.py`
4. Vérifiez votre connexion Internet
5. Ouvrez la console navigateur (F12) pour les erreurs

### Problème : 404 Not Found

**Solution** :
```bash
python manage.py check
python manage.py migrate
```

---

## 📊 Commandes Utiles

| Commande | Description |
|----------|-------------|
| `python manage.py runserver` | Démarrer le serveur |
| `python manage.py migrate` | Appliquer les migrations |
| `python manage.py makemigrations` | Créer les migrations |
| `python manage.py createsuperuser` | Créer un admin |
| `python manage.py shell` | Console Python Django |
| `python manage.py test` | Exécuter les tests |
| `python manage.py check` | Vérifier la configuration |
| `python manage.py collectstatic` | Collecter fichiers statiques |

---

## 🌐 Déploiement

### Production avec Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Avec Nginx (Optionnel)

Voir documentation Nginx officiellement.

---

## 📞 Support

Pour toute question :
1. Vérifier les logs (console)
2. Ouvrir la console navigateur (F12)
3. Consulter la documentation Django : https://docs.djangoproject.com/

---

✅ **Installation terminée !** Vous pouvez commencer à utiliser l'application.
