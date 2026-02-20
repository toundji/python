# Application de Gestion des Paroisses

Application Flask pour la gestion des demandes de messes dans les paroisses du Bénin.

## Déploiement sur Render.com

### Étapes à suivre :

1. **Créer un dépôt GitHub**
   - Allez sur github.com
   - Créez un nouveau dépôt (par exemple : `paroisse-app`)
   - Uploadez tous vos fichiers (app.py, requirements.txt, render.yaml, templates/, static/)

2. **Connecter Render à GitHub**
   - Sur Render.com, cliquez sur "New Web Service"
   - Connectez votre compte GitHub
   - Sélectionnez le dépôt `paroisse-app`

3. **Configuration automatique**
   - Render détectera automatiquement le fichier `render.yaml`
   - La base de données PostgreSQL sera créée automatiquement
   - L'application sera déployée automatiquement

4. **Accéder à votre application**
   - Une fois le déploiement terminé, vous obtiendrez une URL comme : `https://paroisse-app.onrender.com`

## Structure du projet

```
votre-projet/
│
├── app.py                 # Application Flask principale
├── requirements.txt       # Dépendances Python
├── render.yaml           # Configuration Render
├── .gitignore            # Fichiers à ignorer
│
├── templates/            # Templates HTML
│   ├── index.html
│   ├── liste.html
│   ├── details.html
│   ├── demande.html
│   ├── recu.html
│   ├── espace_paroisse.html
│   ├── gestion_paroisse.html
│   ├── intention_paroisse.html
│   └── admin.html
│
└── static/              # Fichiers CSS/JS/Images
    ├── css/
    ├── js/
    └── images/
```

## Développement local

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python app.py

# Accéder à l'application
http://127.0.0.1:5000
```

## Notes importantes

- En production, l'application utilise PostgreSQL
- En développement local, elle utilise SQLite
- La base de données est créée automatiquement au premier lancement
