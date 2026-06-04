# 🔐 Guide d'Authentification Power BI - Django Application

## ❌ Problème : "Sign in to view this report"

Si le dashboard Power BI affiche un écran de connexion, c'est **normal et attendu**. Voici les solutions :

---

## ✅ Solution 1 : Utiliser le Bouton "Ouvrir dans Power BI" (Recommandé)

**C'est la méthode la plus simple et la plus rapide.**

1. Sur la page du dashboard, cliquez sur le bouton **"🔗 Ouvrir dans Power BI"** (en orange)
2. Cela ouvre le rapport directement dans Power BI Service
3. Vous aurez peut-être besoin de vous connecter avec votre compte Microsoft/Azure
4. Vous verrez le rapport complet avec toutes les fonctionnalités

✅ **Avantage** : Accès complet, toutes les fonctionnalités Power BI disponibles  
⚠️ **Limitation** : S'ouvre dans une nouvelle fenêtre

---

## ✅ Solution 2 : Authentification directe dans l'iframe

**Si vous voulez voir le rapport directement dans l'application :**

1. Attendez que le message de connexion apparaisse dans l'iframe
2. Cliquez sur le bouton **"Se Connecter à Power BI"** qui apparaît sous le message d'alerte
3. Une fenêtre de connexion s'ouvre
4. Connectez-vous avec votre compte Microsoft/Azure
5. Retournez à l'application et le rapport devrait charger

✅ **Avantage** : Reste dans l'application  
⚠️ **Limitation** : Nécessite une licence Power BI Pro ou Premium

---

## ✅ Solution 3 : Configuration avec Service Principal (Avancé)

**Pour une intégration complète sans authentification utilisateur :**

Cette solution nécessite :
- Une application Azure AD enregistrée
- Une clé API Power BI
- Configuration backend Python

### Étapes :

1. **Créer une application Azure AD** :
   - Aller sur https://portal.azure.com
   - Accéder à Azure Active Directory → App registrations
   - Créer une nouvelle application
   - Noter l'ID de l'application (Client ID) et créer une clé secrète

2. **Installer le package Python** :
   ```bash
   pip install msal powerbi-client
   ```

3. **Ajouter les variables d'environnement** :
   Créer/modifier `.env` :
   ```
   POWERBI_CLIENT_ID=votre-client-id
   POWERBI_CLIENT_SECRET=votre-client-secret
   POWERBI_TENANT_ID=5047bca2-da88-442e-a09a-d9b8af692adc
   POWERBI_REPORT_ID=a3b6aa0f-43e0-45a7-882f-82fdc64055b4
   ```

4. **Implémenter l'API d'authentification** :
   Je peux créer un endpoint Django qui génère automatiquement les tokens.

---

## 📋 Prérequis pour chaque solution

| Solution | Prérequis | Complexité |
|----------|-----------|-----------|
| **1. Ouvrir dans Power BI** | Compte Microsoft/Azure | 🟢 Très Facile |
| **2. Authentification iframe** | Licence Power BI Pro | 🟡 Facile |
| **3. Service Principal** | App Azure AD + Configuration | 🔴 Avancé |

---

## 🔧 Configuration Actuelle

```
Report ID:      a3b6aa0f-43e0-45a7-882f-82fdc64055b4
Tenant ID:      5047bca2-da88-442e-a09a-d9b8af692adc
Embedding Mode: autoAuth (utilisateur doit être connecté)
```

---

## ❓ FAQ

### Q: Pourquoi dois-je me connecter ?
**R:** Power BI Embedded via iframe web nécessite une authentification pour raisons de sécurité. Seuls les rapports partagés publiquement peuvent charger sans connexion.

### Q: Puis-je éviter la connexion ?
**R:** Oui, avec la **Solution 3 (Service Principal)**, mais cela nécessite une configuration backend plus complexe.

### Q: Pourquoi le bouton "Ouvrir dans Power BI" fonctionne mieux ?
**R:** Parce qu'il utilise le Power BI Service directement au lieu d'une iframe, qui a des limitations de sécurité.

### Q: Quelle solution recommandez-vous ?
**R:** Utilisez la **Solution 1** pour accéder rapidement au rapport. Si vous voulez une intégration complète, demandez à implémenter la **Solution 3**.

---

## 📞 Support

Si vous avez besoin d'aide pour configurer l'une de ces solutions, contactez l'équipe de développement avec :
1. Votre région Azure
2. Vos identifiants de service principal (si applicable)
3. Des captures d'écran des erreurs

---

## 🎯 Prochaines Étapes

1. **Essayez d'abord** le bouton "Ouvrir dans Power BI" ✅
2. **Si vous voulez l'iframe**, utilisez l'authentification directe 
3. **Pour production**, mettez en place le Service Principal

Besoin d'aide ? Consultez la documentation Power BI officielle : https://docs.microsoft.com/power-bi/
