import streamlit as st
import requests
import pandas as pd
from math import radians, cos, sin, asin, sqrt
import time
import io
import folium
from streamlit_folium import st_folium

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IT Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Google Fonts */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Background */
  .stApp {
    background-color: #0f1117;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background-color: #161b27;
    border-right: 1px solid #1e2535;
  }

  /* Cards */
  .card {
    background: #161b27;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s ease;
  }
  .card:hover {
    border-color: #3b82f6;
  }
  .card-title {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 0.3rem;
  }
  .card-address {
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 0.2rem;
  }
  .card-meta {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
  }
  .badge {
    font-size: 0.72rem;
    font-weight: 500;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    background: #1e3a5f;
    color: #60a5fa;
  }
  .badge-green {
    background: #14291f;
    color: #34d399;
  }

  /* KPI boxes */
  .kpi-box {
    background: #161b27;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
  }
  .kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #3b82f6;
  }
  .kpi-label {
    font-size: 0.78rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
  }

  /* Inputs */
  .stTextInput > div > div > input,
  .stNumberInput > div > div > input {
    background-color: #1e2535 !important;
    border: 1px solid #2e3a52 !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
  }
  .stButton > button {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    width: 100%;
    transition: opacity 0.2s;
  }
  .stButton > button:hover {
    opacity: 0.85;
  }

  /* Section titles */
  .section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 1.5rem 0 0.75rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1e2535;
  }

  /* Hero */
  .hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem 1rem;
  }
  .hero h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 0.4rem;
  }
  .hero p {
    color: #64748b;
    font-size: 1rem;
  }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0f1117; }
  ::-webkit-scrollbar-thumb { background: #1e2535; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── UTILS ─────────────────────────────────────────────────────────────────────
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371

@st.cache_data(ttl=3600)
def geocode(location: str):
    url = "https://nominatim.openstreetmap.org/search"
    r = requests.get(url, params={"q": location, "format": "json", "limit": 1},
                     headers={"User-Agent": "IT-Finder-App/2.0"}, timeout=10)
    data = r.json()
    if not data:
        return None, None, None
    return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]

@st.cache_data(ttl=3600)
def fetch_companies(lat, lon, radius_km):
    r = int(radius_km * 1000)
    # Requête sans indentation pour éviter "encoding error: whitespace only"
    lines = [
        "[out:json][timeout:90];",
        "(",
        # Tags OSM explicitement IT — aucun faux positif possible
        f'node["office"="it"](around:{r},{lat},{lon});',
        f'way["office"="it"](around:{r},{lat},{lon});',
        f'node["office"="computer"](around:{r},{lat},{lon});',
        f'way["office"="computer"](around:{r},{lat},{lon});',
        f'node["office"="software"](around:{r},{lat},{lon});',
        f'way["office"="software"](around:{r},{lat},{lon});',
        f'node["shop"="computer"](around:{r},{lat},{lon});',
        f'way["shop"="computer"](around:{r},{lat},{lon});',
        f'node["office"="telecommunication"](around:{r},{lat},{lon});',
        f'way["office"="telecommunication"](around:{r},{lat},{lon});',
        # Recherche nom uniquement sur des mots très spécifiques IT
        # (pas "tech", "digital" qui matchent n'importe quoi)
        f'node["name"~"informatique|SSII|ESN|infogérance|cybersécurité|infogestion",i](around:{r},{lat},{lon});',
        f'way["name"~"informatique|SSII|ESN|infogérance|cybersécurité|infogestion",i](around:{r},{lat},{lon});',
        ");",
        "out center;",
    ]
    query = "\n".join(lines)
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            headers={"User-Agent": "IT-Finder-App/2.0"},
            timeout=90
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("elements", [])
    except requests.exceptions.JSONDecodeError:
        st.warning("⚠️ L'API Overpass a retourné une erreur. Réessayez dans quelques secondes.")
        return []
    except requests.exceptions.Timeout:
        st.warning("⚠️ Timeout : réduisez le rayon ou réessayez plus tard.")
        return []
    except Exception as e:
        st.error(f"❌ Erreur réseau : {e}")
        return []

IT_KEYWORDS = [
    # Mots 100% spécifiques IT — pas de faux positifs possibles
    "informatique",
    "logiciel", "progiciel",
    "cybersécurité", "cybersecurite", "cyber sécurité",
    "infogérance", "infogérance", "infogestion",
    "esn ", " esn", "ssii",
    "erp ", "sap ", " crm",
    "intelligence artificielle",
    "machine learning", "deep learning",
    "développement logiciel", "développement web",
    "maintenance informatique", "dépannage informatique",
    "réseau informatique", "infrastructure informatique",
    "cloud computing", "hébergement web", "hébergement informatique",
    "téléphonie ip", "voip",
    "it services", "it solutions", "it consulting", "managed services",
    "software house", "software editor",
    "datacenter", "data center",
]
EXCLUDE = [
    # Alimentaire
    "restaurant","brasserie","boulangerie","pâtisserie","boucherie",
    "poissonnerie","épicerie","supermarché","traiteur","pizzeria",
    "kebab","sushi","burger","sandwicherie","snack","friterie",
    # Beauté / Santé
    "coiffeur","coiffure","barbier","esthétique","spa","manucure",
    "pharmacie","médecin","dentiste","kiné","ostéopathe","infirmier",
    "opticien","audioprothésiste","vétérinaire",
    # Services pro non-IT
    "notaire","avocat","huissier","comptable","expert-comptable",
    "assurance","banque","agence immobilière","immobilier","agence de voyage",
    # Commerce généraliste
    "garage","carrosserie","fleuriste","jardinerie","bricolage",
    "pressing","laverie","cordonnerie","serrurerie","plombier","électricien",
    # Éducation / Religion / Sport
    "école","maternelle","primaire","collège","lycée","université",
    "église","mosquée","temple","synagogue",
    "salle de sport","fitness","gym","yoga","danse",
    # Hébergement / Restauration
    "hôtel","auberge","chambre d'hôtes","gîte",
    "café","bar ","pub ","discothèque","night-club",
    # Divers
    "pompes funèbres","tatouage","piercing",
]

def is_it(tags):
    office = tags.get("office","").lower()
    shop   = tags.get("shop","").lower()
    name   = tags.get("name","").lower()
    desc   = tags.get("description","").lower()
    text   = f" {name} {desc} "  # espaces pour éviter les sous-chaînes

    # 1. Exclusion immédiate si secteur non-IT
    if any(e in text for e in EXCLUDE):
        return False

    # 2. Tag OSM explicitement IT → accepté directement
    if office in {"it","computer","software","telecommunication"}:
        return True
    if shop == "computer":
        return True

    # 3. Vérification stricte par mots-clés longs (min 8 chars)
    #    évite "net" dans "Benet", "info" dans "Informel", etc.
    for kw in IT_KEYWORDS:
        if len(kw.strip()) >= 8 and kw in text:
            return True
        elif len(kw.strip()) < 8 and f" {kw.strip()} " in text:
            return True  # mot court : exiger espaces autour

    return False

def parse_address(tags):
    parts = []
    if "addr:housenumber" in tags: parts.append(tags["addr:housenumber"])
    if "addr:street"      in tags: parts.append(tags["addr:street"])
    city = []
    if "addr:postcode" in tags: city.append(tags["addr:postcode"])
    if "addr:city"     in tags: city.append(tags["addr:city"])
    if city: parts.append(", ".join(city))
    if not parts and "addr:full" in tags: return tags["addr:full"]
    return ", ".join(parts) if parts else "Adresse non renseignée"

def process(elements, clat, clon, radius_km):
    companies, seen = [], set()
    for el in elements:
        tags = el.get("tags", {})
        if not is_it(tags): continue
        name = tags.get("name", "Sans nom")
        if name in seen: continue
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        elif el["type"] == "way" and "center" in el:
            lat, lon = el["center"].get("lat"), el["center"].get("lon")
        else:
            continue
        if lat is None or lon is None: continue
        dist = haversine(clon, clat, lon, lat)
        if dist > radius_km: continue
        companies.append({
            "Nom":         name,
            "Adresse":     parse_address(tags),
            "Téléphone":   tags.get("phone", tags.get("contact:phone","")),
            "Site_Web":    tags.get("website", tags.get("contact:website","")),
            "Latitude":    round(lat, 6),
            "Longitude":   round(lon, 6),
            "Distance_km": round(dist, 2),
        })
        seen.add(name)
    return sorted(companies, key=lambda x: x["Distance_km"])

def build_map(companies, clat, clon):
    m = folium.Map(location=[clat, clon], zoom_start=12,
                   tiles="CartoDB dark_matter")
    # Centre
    folium.CircleMarker(
        location=[clat, clon], radius=8,
        color="#3b82f6", fill=True, fill_color="#3b82f6", fill_opacity=0.9,
        tooltip="📍 Centre de recherche"
    ).add_to(m)
    # Rayon
    folium.Circle(
        location=[clat, clon],
        radius=st.session_state.get("radius_m", 10000),
        color="#3b82f6", fill=True, fill_color="#3b82f6", fill_opacity=0.05,
        weight=1.5, dash_array="6"
    ).add_to(m)
    # Entreprises
    for c in companies:
        popup_html = f"""
        <div style='font-family:Inter,sans-serif;min-width:180px'>
          <b style='color:#f1f5f9'>{c['Nom']}</b><br>
          <span style='color:#94a3b8;font-size:0.8rem'>{c['Adresse']}</span><br>
          <span style='color:#60a5fa;font-size:0.8rem'>📏 {c['Distance_km']} km</span>
          {"<br><a href='" + c['Site_Web'] + "' target='_blank' style='color:#34d399;font-size:0.8rem'>🌐 Site web</a>" if c['Site_Web'] else ""}
        </div>"""
        folium.CircleMarker(
            location=[c["Latitude"], c["Longitude"]],
            radius=6, color="#f59e0b",
            fill=True, fill_color="#f59e0b", fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=c["Nom"]
        ).add_to(m)
    return m

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1rem 0 1.5rem 0'>
      <div style='font-size:2rem'>🔍</div>
      <div style='font-size:1.2rem;font-weight:700;color:#f1f5f9'>IT Finder</div>
      <div style='font-size:0.75rem;color:#64748b;margin-top:0.2rem'>
        Moteur de recherche d'entreprises IT
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**📍 Localisation**")
    location = st.text_input("", placeholder="Ex: Toulouse, Paris 8e...",
                             label_visibility="collapsed")

    st.markdown("**📏 Rayon de recherche**")
    radius_km = st.slider("", min_value=1, max_value=50, value=10, step=1,
                          format="%d km", label_visibility="collapsed")
    st.session_state["radius_m"] = radius_km * 1000

    st.markdown("**📋 Nombre de résultats**")
    max_results = st.selectbox(
        "", options=[10, 25, 50, 100],
        index=1, format_func=lambda x: f"Top {x} entreprises",
        label_visibility="collapsed"
    )

    search = st.button("🔍  Rechercher")

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem;color:#475569;line-height:1.6'>
      <b style='color:#64748b'>Sources de données</b><br>
      🗺️ OpenStreetMap (ODbL)<br>
      🔌 Overpass API<br>
      📍 Nominatim
    </div>
    """, unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
if not search or not location:
    st.markdown("""
    <div class='hero'>
      <h1>🔍 IT Finder</h1>
      <p>Trouvez toutes les entreprises informatiques autour de vous,<br>
         visualisez-les sur une carte et exportez les résultats en Excel.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class='kpi-box'>
          <div style='font-size:1.8rem'>🗺️</div>
          <div style='color:#94a3b8;font-size:0.85rem;margin-top:0.5rem'>
            Carte interactive avec toutes les entreprises IT localisées
          </div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class='kpi-box'>
          <div style='font-size:1.8rem'>⚡</div>
          <div style='color:#94a3b8;font-size:0.85rem;margin-top:0.5rem'>
            Recherche en temps réel via l'API Overpass d'OpenStreetMap
          </div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class='kpi-box'>
          <div style='font-size:1.8rem'>📊</div>
          <div style='color:#94a3b8;font-size:0.85rem;margin-top:0.5rem'>
            Export Excel avec nom, adresse, GPS et distance
          </div>
        </div>""", unsafe_allow_html=True)

else:
    with st.spinner("🔍 Géolocalisation en cours..."):
        clat, clon, display_name = geocode(location)

    if clat is None:
        st.error(f"❌ Lieu « {location} » introuvable. Vérifiez l'orthographe.")
        st.stop()

    time.sleep(0.5)

    with st.spinner("🌐 Interrogation de l'API Overpass..."):
        elements = fetch_companies(clat, clon, radius_km)

    companies = process(elements, clat, clon, radius_km)

    # Appliquer la limite de résultats
    companies = companies[:max_results]

    # ── KPIs ──
    total = len(companies)
    zone1 = sum(1 for c in companies if c["Distance_km"] < 5)
    zone2 = sum(1 for c in companies if 5 <= c["Distance_km"] < 10)
    with_web = sum(1 for c in companies if c["Site_Web"])

    st.markdown(f"""
    <div style='padding:0.5rem 0 1rem 0'>
      <div style='font-size:0.8rem;color:#64748b;margin-bottom:0.2rem'>
        📍 {display_name}
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, total,    f"Entreprises IT (top {max_results})"),
        (c2, zone1,    "À moins de 5 km"),
        (c3, zone2,    "Entre 5 et 10 km"),
        (c4, with_web, "Avec site web"),
    ]:
        with col:
            st.markdown(f"""<div class='kpi-box'>
              <div class='kpi-value'>{val}</div>
              <div class='kpi-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    if total == 0:
        st.warning("Aucune entreprise IT trouvée. Essayez d'augmenter le rayon.")
        st.stop()

    # ── TABS ──
    tab_map, tab_list, tab_data = st.tabs(["🗺️  Carte", "📋  Liste", "📊  Données"])

    # ── TAB MAP ──
    with tab_map:
        st.markdown(f"""<div class='section-title'>
          Carte — {total} entreprise{"s" if total > 1 else ""} affichée{"s" if total > 1 else ""} (top {max_results}, rayon {radius_km} km)
        </div>""", unsafe_allow_html=True)
        m = build_map(companies, clat, clon)
        st_folium(m, width="100%", height=520, returned_objects=[])

    # ── TAB LIST ──
    with tab_list:
        st.markdown(f"""<div class='section-title'>
          Résultats triés par distance
        </div>""", unsafe_allow_html=True)

        # Filtre distance
        max_dist = st.slider("Afficher jusqu'à", 1, radius_km, radius_km,
                              format="%d km", key="filter_dist")
        filtered = [c for c in companies if c["Distance_km"] <= max_dist]
        st.caption(f"{len(filtered)} entreprises affichées")

        for c in filtered:
            phone_badge = f"<span class='badge'>📞 {c['Téléphone']}</span>" if c["Téléphone"] else ""
            web_badge = f"<a href='{c['Site_Web']}' target='_blank'><span class='badge badge-green'>🌐 Site web</span></a>" if c["Site_Web"] else ""
            st.markdown(f"""
            <div class='card'>
              <div class='card-title'>{c['Nom']}</div>
              <div class='card-address'>📍 {c['Adresse']}</div>
              <div class='card-meta'>
                <span class='badge'>📏 {c['Distance_km']} km</span>
                <span class='badge'>🌍 {c['Latitude']}, {c['Longitude']}</span>
                {phone_badge}
                {web_badge}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB DATA ──
    with tab_data:
        st.markdown("""<div class='section-title'>Tableau et export</div>""",
                    unsafe_allow_html=True)
        df = pd.DataFrame(companies)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "Nom":         st.column_config.TextColumn("🏢 Nom"),
                         "Adresse":     st.column_config.TextColumn("📍 Adresse"),
                         "Distance_km": st.column_config.NumberColumn("📏 Distance (km)", format="%.2f"),
                         "Site_Web":    st.column_config.LinkColumn("🌐 Site web"),
                         "Téléphone":   st.column_config.TextColumn("📞 Téléphone"),
                     })

        # Export Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Entreprises IT")
        st.download_button(
            label="⬇️  Télécharger Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"entreprises_it_{location.replace(' ','_').lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
