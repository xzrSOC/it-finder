# 🔍 IT Finder

> Application web pour trouver les entreprises informatiques autour de vous, visualisées sur une carte interactive.

![Python](https://img.shields.io/badge/Python-3.10+-3b82f6?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-ff4b4b?style=flat-square&logo=streamlit&logoColor=white)
![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-ODbL-7ebc6f?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## ✨ Fonctionnalités

- 🗺️ **Carte interactive** (Folium + OpenStreetMap dark mode)
- 🔍 **Recherche par lieu + rayon** (1 à 50 km)
- ⚡ **Filtre IT strict** : évite les faux positifs
- 📊 **Export Excel** en un clic
- 📋 **Liste détaillée** avec adresse, téléphone, site web
- 📱 Design **responsive et moderne** (dark mode)

## 🚀 Déploiement sur Streamlit Cloud (gratuit)

1. **Fork** ce repository sur GitHub
2. Aller sur [share.streamlit.io](https://share.streamlit.io)
3. Connecter votre compte GitHub
4. Sélectionner ce repo → `app.py`
5. Cliquer **Deploy** — c'est tout ! ✅

## 💻 Lancer en local

```bash
# Cloner
git clone https://github.com/VOTRE_USERNAME/it-finder.git
cd it-finder

# Installer
pip install -r requirements.txt

# Lancer
streamlit run app.py
```

L'app s'ouvre sur http://localhost:8501

## 🗂️ Structure du projet

```
it-finder/
├── app.py                  # Application principale
├── requirements.txt        # Dépendances Python
├── .streamlit/
│   └── config.toml         # Thème dark mode
└── README.md
```

## 🔌 APIs utilisées

| Service | Usage | Limites |
|---------|-------|---------|
| [Nominatim](https://nominatim.org) | Géolocalisation ville → GPS | 1 req/s |
| [Overpass API](https://overpass-api.de) | Requête OpenStreetMap | 60s timeout |

## 🛠️ Stack technique

- **Frontend/Backend** : [Streamlit](https://streamlit.io)
- **Carte** : [Folium](https://python-visualization.github.io/folium) + CartoDB Dark Matter
- **Données** : [OpenStreetMap](https://www.openstreetmap.org) (ODbL)
- **Export** : pandas + openpyxl

## 📄 Licence

MIT — Données cartographiques © OpenStreetMap contributors (ODbL)
