import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import requests

st.set_page_config(page_title="SmartClub 360", page_icon="⚽", layout="wide")

# ==============================================================================
# FUTBOL TEMALI CSS
# ==============================================================================
st.markdown("""
<style>
/* === ANA ARKA PLAN: Koyu yeşil saha hissi === */
.stApp {
    background: linear-gradient(135deg, #0a1a0a 0%, #0d1f0d 30%, #0e1117 60%, #0a1a0a 100%);
}

/* === SANTRA NOKTASI / SAHA ÇİZGİLERİ (Dekoratif) === */
.stApp::before {
    content: '';
    position: fixed;
    top: 50%;
    left: 55%;
    transform: translate(-50%, -50%);
    width: 400px;
    height: 400px;
    border: 2px solid rgba(0, 255, 135, 0.06);
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
}
.stApp::after {
    content: '';
    position: fixed;
    top: 50%;
    left: 55%;
    transform: translate(-50%, -50%);
    width: 12px;
    height: 12px;
    background: rgba(0, 255, 135, 0.12);
    border-radius: 50%;
    pointer-events: none;
    z-index: 0;
}

/* === SIDEBAR: Karanlık soyunma odası === */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a120a 0%, #0d1a0d 50%, #111a11 100%) !important;
    border-right: 2px solid rgba(0, 255, 135, 0.15);
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00ff87 !important;
}

/* === BAŞLIKLAR: Neon yeşil === */
h1 {
    color: #00ff87 !important;
    text-shadow: 0 0 20px rgba(0, 255, 135, 0.3);
}
h2 {
    color: #00e676 !important;
    border-left: 4px solid #00ff87;
    padding-left: 12px;
}
h3 { color: #b9f6ca !important; }

/* === METRİK KARTLAR: Stadyum tablo tarzı === */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d1f0d 0%, #1a2f1a 100%);
    border: 1px solid rgba(0, 255, 135, 0.2);
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 4px 15px rgba(0, 255, 135, 0.08);
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 700;
}
[data-testid="stMetricLabel"] {
    color: #81c784 !important;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    letter-spacing: 1px;
}
[data-testid="stMetricDelta"] > div {
    color: #00ff87 !important;
}

/* === BUTONLAR: Saha çizgisi tarzı === */
.stButton > button {
    background: linear-gradient(135deg, #1a3a1a 0%, #0d2f0d 100%) !important;
    color: #00ff87 !important;
    border: 1px solid rgba(0, 255, 135, 0.3) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    text-shadow: 0 0 8px rgba(0, 255, 135, 0.3);
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00ff87 0%, #00e676 100%) !important;
    color: #0a1a0a !important;
    border-color: #00ff87 !important;
    box-shadow: 0 0 20px rgba(0, 255, 135, 0.4) !important;
    text-shadow: none;
}

/* === SEKMELER (TABS): Stadyum bölmeleri === */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(0, 255, 135, 0.05);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #81c784 !important;
    font-weight: 600;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    background: rgba(0, 255, 135, 0.15) !important;
    color: #00ff87 !important;
    border-bottom: 3px solid #00ff87 !important;
}

/* === TABLOLAR === */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(0, 255, 135, 0.15);
    border-radius: 10px;
    overflow: hidden;
}

/* === BAŞARI / HATA KUTULARI === */
.stSuccess {
    background-color: rgba(0, 255, 135, 0.08) !important;
    border-left: 4px solid #00ff87 !important;
    color: #b9f6ca !important;
}
.stError {
    background-color: rgba(255, 82, 82, 0.08) !important;
    border-left: 4px solid #ff5252 !important;
}

/* === SELECTBOX / SLIDER === */
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label {
    color: #81c784 !important;
    font-weight: 600;
}

/* === DIVIDER: Saha çizgisi === */
hr {
    border-color: rgba(0, 255, 135, 0.15) !important;
}

/* === RADIO BUTONLARI === */
[data-testid="stRadio"] label {
    color: #b9f6ca !important;
}

/* === GENEL SCROLLBAR === */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0a1a0a; }
::-webkit-scrollbar-thumb { background: #1a3a1a; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #00ff87; }
</style>
""", unsafe_allow_html=True)

# Yan menü navigasyonu
st.sidebar.title("⚽ SmartClub 360")
st.sidebar.markdown("*Veri Odaklı Scouting Portalı*")
st.sidebar.divider()
panel_secimi = st.sidebar.radio("🧭 Modül Seçiniz:", ["Piyasa Değeri Paneli (Taha)", "Bağlamsal xG Paneli (Huzeyfe)"])

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
market_data_path = os.path.join(base_dir, "data", "2526_PL_Clean Data", "players_market_data.csv")
season_data_path = os.path.join(base_dir, "data", "2526_PL_Clean Data", "player_season_stats.csv")
kisi2_model_path = os.path.join(base_dir, "data", "2526_PL_Clean Data", "PL_Model", "Kişi2", "player_value_model.pkl")


# ==============================================================================
# FPL API: OYUNCU FOTOĞRAFLARI ve KULÜP LOGOLARI
# ==============================================================================
@st.cache_data(ttl=7200, show_spinner="FPL verileri yükleniyor...")
def load_fpl_data_v2():
    """Fantasy Premier League API'sinden oyuncu fotoğrafları ve kulüp logolarını çeker."""
    try:
        r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
        data = r.json()

        # Takım logoları
        team_logos = {}
        for t in data["teams"]:
            logo_url = f"https://resources.premierleague.com/premierleague/badges/100/t{t['code']}@x2.png"
            team_logos[t["name"]] = logo_url

        # Oyuncu fotoğrafları
        player_photos = {}
        for p in data["elements"]:
            full_name = f"{p['first_name']} {p['second_name']}"
            web_name = p["web_name"]
            photo_url = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{p['code']}.png"
            player_photos[full_name] = photo_url
            player_photos[web_name] = photo_url
            player_photos[p["second_name"]] = photo_url

        return team_logos, player_photos
    except Exception:
        return {}, {}

fpl_team_logos, fpl_player_photos = load_fpl_data_v2()

def show_player_img(player_name, width=120):
    """Oyuncu fotoğrafını gösterir; yüklenemezse otomatik avatar'a döner."""
    photo_url = get_player_photo(player_name)
    safe_name = player_name.replace(" ", "+")
    fallback = f"https://ui-avatars.com/api/?name={safe_name}&background=1a1a2e&color=e94560&size=140&rounded=true&bold=true&font-size=0.33"
    st.markdown(
        f'<img src="{photo_url}" onerror="this.onerror=null;this.src=\'{fallback}\';" '
        f'style="width:{width}px;height:auto;border-radius:12px;object-fit:cover;" />',
        unsafe_allow_html=True
    )

def show_team_logo(team_name, width=80):
    """Takım logosunu gösterir; yüklenemezse genel futbol ikonu döner."""
    logo_url = get_team_logo(team_name)
    fallback = "https://cdn-icons-png.flaticon.com/512/33/33736.png"
    st.markdown(
        f'<img src="{logo_url}" onerror="this.onerror=null;this.src=\'{fallback}\';" '
        f'style="width:{width}px;height:auto;" />',
        unsafe_allow_html=True
    )

# Bizim veri setimizdeki takım isimlerini FPL'deki isimlere çeviren sabit tablo
OUR_TO_FPL_TEAM = {
    "Arsenal FC": "Arsenal",
    "Aston Villa": "Aston Villa",
    "AFC Bournemouth": "Bournemouth",
    "Brentford FC": "Brentford",
    "Brighton & Hove Albion": "Brighton",
    "Burnley FC": "Burnley",
    "Chelsea FC": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton FC": "Everton",
    "Fulham FC": "Fulham",
    "Leeds United": "Leeds",
    "Liverpool FC": "Liverpool",
    "Liverpool": "Liverpool",
    "Manchester City": "Man City",
    "Manchester City FC": "Man City",
    "Manchester United": "Man Utd",
    "Manchester United FC": "Man Utd",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Sunderland AFC": "Sunderland",
    "Tottenham Hotspur": "Spurs",
    "Tottenham Hotspur FC": "Spurs",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
}

def get_team_logo(team_name):
    """Takım adından logo URL'i döndürür."""
    fpl_name = OUR_TO_FPL_TEAM.get(team_name, team_name)
    if fpl_name in fpl_team_logos:
        return fpl_team_logos[fpl_name]
    # Son çare: genel futbol ikonu
    return "https://cdn-icons-png.flaticon.com/512/33/33736.png"

def _normalize(name):
    """İsmi küçük harfe çevirip aksanları temizler."""
    import unicodedata
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    return name.lower().strip()

def get_player_photo(player_name):
    """Oyuncu adından fotoğraf URL'i döndürür."""
    # 1. Direkt eşleşme
    if player_name in fpl_player_photos:
        return fpl_player_photos[player_name]
    # 2. Normalize edilmiş eşleşme (aksanlar vb.)
    norm_name = _normalize(player_name)
    for fpl_name, url in fpl_player_photos.items():
        if _normalize(fpl_name) == norm_name:
            return url
    # 3. Soyadı eşleştirmesi
    parts = player_name.split()
    for part in reversed(parts):
        norm_part = _normalize(part)
        for fpl_name, url in fpl_player_photos.items():
            if _normalize(fpl_name) == norm_part:
                return url
    # 4. Kısmi eşleşme (isimlerden biri tutuyorsa)
    for fpl_name, url in fpl_player_photos.items():
        fpl_parts = set(_normalize(fpl_name).split())
        our_parts = set(norm_name.split())
        if len(fpl_parts & our_parts) >= 2:
            return url
    # 5. Bulunamazsa avatar
    safe_name = player_name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={safe_name}&background=1a1a2e&color=e94560&size=128&rounded=true&bold=true&font-size=0.33"


# ==============================================================================
# PANEL 1: PİYASA DEĞERİ (TAHA)
# ==============================================================================
if panel_secimi == "Piyasa Değeri Paneli (Taha)":
    st.title("⚽ SmartClub 360")
    st.subheader("Yapay Zeka Destekli Futbol İzleme ve Piyasa Değeri İstihbaratı")

    # --- Model Yükle ---
    try:
        model = joblib.load(kisi2_model_path)
        st.success("Model başarıyla yüklendi ✅")
    except Exception as e:
        st.error(f"Model dosyası yüklenemedi: {e}")
        st.stop()

    # --- Veri Hazırla ---
    def convert_market_value(value):
        if pd.isna(value): return np.nan
        value = str(value).replace("€", "").strip().lower()
        if value in ["-", "", "nan", "none"]: return np.nan
        if "m" in value: return float(value.replace("m", "")) * 1_000_000
        if "k" in value: return float(value.replace("k", "")) * 1_000
        return float(value)

    market_df = pd.read_csv(market_data_path)
    season_df = pd.read_csv(season_data_path)
    market_df["market_value_numeric"] = market_df["market_value"].apply(convert_market_value)
    market_df = market_df.dropna(subset=["market_value_numeric"])

    # İsim uyumsuzlukları düzeltme tablosu (Transfermarkt -> Understat)
    name_fixes = {
        "Rayan Cherki": "Mathis Cherki",
        "Martin Ødegaard": "Martin Odegaard",
        "Savinho": "Sávio",
        "Viktor Gyökeres": "Viktor Gyokeres",
        "Dejan Kulusevski": "Dejan Kulusevski",
        "Amad Diallo": "Amad Diallo Traore",
        "Emile Smith Rowe": "Emile Smith-Rowe",
        "Emiliano Martínez": "Emiliano Martinez",
        "Jérémy Doku": "Jéremy Doku",
        "Joe Gomez": "Joseph Gomez",
        "Caoimhín Kelleher": "Caoimhin Kelleher",
        "Benoît Badiashile": "Benoit Badiashile Mukinayi",
        "Marc Guéhi": "Marc Guehi",
        "Ezri Konsa": "Ezri Konsa Ngoyo",
        "Tomáš Souček": "Tomas Soucek",
        "Radu Drăgușin": "Radu Dragusin",
        "Destiny Udogie": "Iyenoma Destiny Udogie",
        "Pape Matar Sarr": "Pape Sarr",
        "Roméo Lavia": "Romeo Lavia",
        "Hugo Ekitiké": "Hugo Ekitike",
        "Ferdi Kadıoğlu": "Ferdi Kadioglu",
        "Filip Jørgensen": "Filip Jorgensen",
        "Ismaïla Sarr": "Ismaila Sarr",
        "Ibrahim Sangaré": "Ibrahim Sangare",
        "Martin Dúbravka": "Martin Dubravka",
        "Séamus Coleman": "Seamus Coleman",
        "Vitaliy Mykolenko": "Vitalii Mykolenko",
        "Rayan Aït-Nouri": "Rayan Ait Nouri",
        "Nikola Milenković": "Nikola Milenkovic",
        "Tino Livramento": "Valentino Livramento",
        "Taty Castellanos": "Valentín Castellanos",
        "Yegor Yarmolyuk": "Yehor Yarmolyuk",
        "Yéremy Pino": "Yeremi Pino",
        "Saša Lukić": "Sasa Lukic",
        "Jamie Gittens": "Jamie Bynoe-Gittens",
        "Maximilian Kilman": "Max Kilman",
        "Matty Cash": "Matthew Cash",
        "James Maddison": "James Maddison",
        "Abdukodir Khusanov": "Abduqodir Khusanov",
        "Josh King": "Joshua King",
        "Altay Bayındır": "Altay Bayindir",
        "Ladislav Krejčí": "Ladislav Krejcí",
        "Hee-chan Hwang": "Hee-Chan Hwang",
        "Fábio Carvalho": "Fabio Carvalho",
        "Bafodé Diakité": "Bafode Diakite",
        "Ben Gannon-Doak": "Ben Doak",
        "Chido Obi": "Chido Obi",
        "Stefan Ortega": "Stefan Ortega Moreno",
        "Florentino": "Florentino Luís",
        "Hannibal": "Hannibal Mejbri",
        "Lesley Ugochukwu": "Chimuanya Ugochukwu",
        "Mike Tresor": "Mike Trésor",
        "Trey Nyoni": "Treymaurice Nyoni",
        "Junior Kroupi": "Eli Junior Kroupi",
        "Álex Jiménez": "Alejandro Jiménez",
        "Reinildo Mandava": "Reinildo",
        "Antonín Kinský": "Antonín Kinsky",
        "Max Weiß": "Max Weiss",
        "Jair Cunha": "Jair",
        "Alysson": "Alysson Edward",
        "Cheick Doucouré": "Cheick Doucouré",
        "Igor Thiago": "Thiago",
        "Sverre Nypan": "Sverre Nypan",
    }
    market_df["player"] = market_df["player"].replace(name_fixes)

    df = pd.merge(market_df, season_df, on=["player"], how="inner")
    # Aynı oyuncunun birden fazla satırda çıkmasını engelle (merge çarprazı)
    df = df.drop_duplicates(subset=["player"], keep="first")
    df["team"] = df["team_x"]
    df["position"] = df["position_x"]

    df["dob_age"] = df["dob_age"].astype(str).str.extract(r"\((\d+)\)")
    df["dob_age"] = pd.to_numeric(df["dob_age"], errors="coerce")

    numeric_cols = ["matches", "minutes", "goals", "assists", "xg", "np_xg", "xa", "shots", "key_passes"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["minutes"] > 400]

    df["goal_contribution"] = df["goals"] + df["assists"]
    df["goal_contribution_per90"] = (df["goal_contribution"] / df["minutes"]) * 90
    df["xg_xa_per90"] = ((df["xg"] + df["xa"]) / df["minutes"]) * 90
    df["shots_per90"] = (df["shots"] / df["minutes"]) * 90
    df["key_passes_per90"] = (df["key_passes"] / df["minutes"]) * 90
    df["np_xg_per90"] = (df["np_xg"] / df["minutes"]) * 90
    df["age_potential_score"] = (df["goal_contribution_per90"] / df["dob_age"])
    df = df.replace([np.inf, -np.inf], np.nan)

    model_columns = [
        "dob_age", "matches", "minutes", "goals", "assists", "xg", "np_xg", "xa", "shots", "key_passes",
        "goal_contribution", "goal_contribution_per90", "xg_xa_per90", "shots_per90", "key_passes_per90",
        "np_xg_per90", "age_potential_score"
    ]
    df = df.dropna(subset=model_columns + ["market_value_numeric"])

    # --- Shrinkage Tahminler ---
    raw_preds = np.expm1(model.predict(df[model_columns]))
    df["predicted_market_value"] = (raw_preds * 0.25) + (df["market_value_numeric"] * 0.75)
    df["value_difference"] = df["predicted_market_value"] - df["market_value_numeric"]
    df["value_difference_pct"] = (df["value_difference"] / df["market_value_numeric"]) * 100

    # --- Sidebar Filtreler ---
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Filtreler")
    teams_list = ["Tümü"] + sorted(df["team"].dropna().unique().tolist())
    selected_team = st.sidebar.selectbox("Kulüp Seç", teams_list)

    pos_list = ["Tümü"] + sorted(df["position"].dropna().unique().tolist())
    selected_pos = st.sidebar.selectbox("Mevki Seç", pos_list)

    age_min, age_max = int(df["dob_age"].min()), int(df["dob_age"].max())
    age_range = st.sidebar.slider("Yaş Aralığı", age_min, age_max, (age_min, age_max))

    filtered_df = df.copy()
    if selected_team != "Tümü":
        filtered_df = filtered_df[filtered_df["team"] == selected_team]
    if selected_pos != "Tümü":
        filtered_df = filtered_df[filtered_df["position"] == selected_pos]
    filtered_df = filtered_df[(filtered_df["dob_age"] >= age_range[0]) & (filtered_df["dob_age"] <= age_range[1])]

    st.write(f"Kullanılabilir oyuncu sayısı: **{len(filtered_df)}**")
    st.divider()

    # === SEKMELER ===
    tab_genel, tab_ilk11 = st.tabs(["📊 Genel Pazar Analizi", "🏟️ Pozisyona Göre İlk 11"])

    # --- TAB 1: GENEL ---
    with tab_genel:
        if filtered_df.empty:
            st.warning("Bu filtrelere uygun oyuncu bulunamadı. Filtreleri genişletin.")
        else:
            st.header("🔍 Oyuncu Piyasa Değeri Tahmini")
            selected_player = st.selectbox("Oyuncu Seç", sorted(filtered_df["player"].unique()))
            player_data = filtered_df[filtered_df["player"] == selected_player].iloc[0]

            # --- Profil Kartı (FOTOĞRAF + LOGO) ---
            st.subheader(f"📋 {selected_player} Oyuncu Bilgileri")
            c_img, c_info, c_logo = st.columns([1, 4, 1])
            with c_img:
                show_player_img(selected_player, width=120)
            with c_info:
                st.markdown(f"**Takım:** {player_data['team']}")
                st.markdown(f"**Mevki:** {player_data['position']} &nbsp; | &nbsp; **Yaş:** {int(player_data['dob_age'])}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Maç", int(player_data["matches"]))
                col2.metric("Gol", int(player_data["goals"]))
                col3.metric("Asist", int(player_data["assists"]))
            with c_logo:
                show_team_logo(player_data["team"], width=80)

            # --- Değerleme ---
            predicted_value = player_data["predicted_market_value"]
            real_value = player_data["market_value_numeric"]
            difference = predicted_value - real_value
            difference_pct = (difference / real_value) * 100

            st.divider()
            st.header("💰 Yapay Zeka Pazar Analizi")
            c1, c2, c3 = st.columns(3)
            c1.metric("Gerçek Piyasa Değeri", f"{real_value:,.0f} €")
            c2.metric("AI Tahmini Değer", f"{predicted_value:,.0f} €")
            c3.metric("Fark", f"%{difference_pct:.1f}")

            if difference > 0:
                st.success("🟢 Bu oyuncu DEĞERLENDİRİLMEMİŞ görünüyor. AI modeline göre piyasaya kayıtlı olabilir.")
            else:
                st.error("🔴 Bu oyuncu AŞIRI DEĞERLENMİŞ görünüyor. AI modeline göre piyasanın üzerinde olabilir.")

            # --- KPI ---
            st.divider()
            scout_df = filtered_df[["player", "team", "position", "dob_age", "market_value_numeric", "predicted_market_value", "value_difference_pct"]].copy()
            scout_df = scout_df.rename(columns={
                "player": "Oyuncu", "team": "Takım", "position": "Mevki", "dob_age": "Yaş",
                "market_value_numeric": "Gerçek Değer", "predicted_market_value": "AI Tahmini", "value_difference_pct": "Fark %"
            })

            best = scout_df.sort_values("Fark %", ascending=False).iloc[0]
            worst = scout_df.sort_values("Fark %", ascending=True).iloc[0]
            avg_diff = scout_df["Fark %"].mean()
            k1, k2, k3 = st.columns(3)
            k1.metric("🎯 En Büyük Fırsat", best["Oyuncu"], f"{best['Fark %']:.1f}%")
            k2.metric("💸 En Pahalı Görünen", worst["Oyuncu"], f"{worst['Fark %']:.1f}%")
            k3.metric("📈 Ortalama AI Farkı", f"{avg_diff:.1f}%")

            # --- Scout Yorumu ---
            st.divider()
            st.subheader("🧠 AI Scout Yorumu")
            if difference > 0:
                st.info(f"AI modeli, **{selected_player}** oyuncusunun mevcut piyasa değerine göre daha yüksek bir potansiyele sahip olabileceğini düşünüyor. Fark: **%{difference_pct:.1f}**")
            else:
                st.warning(f"AI modeli, **{selected_player}** oyuncusunun mevcut piyasa değerinin performans verilerine göre yüksek kalmış olabileceğini düşünüyor. Fark: **%{difference_pct:.1f}**")

            # --- Tablolar ---
            st.divider()
            def show_scout_table(data):
                st.dataframe(
                    data.style.format({"Gerçek Değer": "€{:,.0f}", "AI Tahmini": "€{:,.0f}", "Fark %": "{:.1f}%"}),
                    use_container_width=True, hide_index=True
                )

            t1, t2, t3 = st.tabs(["🟢 Fırsat Oyuncular", "🔴 Pahalı Oyuncular", "💎 Transfer Hedefleri"])
            with t1:
                st.caption("AI modeline göre gerçek piyasa değerinden daha değerli görünen oyuncular.")
                show_scout_table(scout_df.sort_values("Fark %", ascending=False).head(8))
            with t2:
                st.caption("AI modeline göre piyasa değeri performansına kıyasla yüksek görünen oyuncular.")
                show_scout_table(scout_df.sort_values("Fark %", ascending=True).head(8))
            with t3:
                st.caption("AI modeline göre fiyat/performans fırsatı sunan oyuncular.")
                targets = scout_df[scout_df["Fark %"] > 20].sort_values("Fark %", ascending=False).head(8)
                if targets.empty:
                    st.info("Bu filtrelerde %20 üzeri fark gösteren oyuncu yok.")
                else:
                    show_scout_table(targets)

    # --- TAB 2: İLK 11 ---
    with tab_ilk11:
        st.header("🏟️ Pozisyon Odaklı Transfer Araması")
        st.markdown("Eksik bölgenizi seçin, yapay zeka o pozisyondaki en iyi fırsat transferlerini getirsin.")
        st.markdown("---")

        st.markdown("#### ⬆️ Hücum")
        fw1, fw2, fw3 = st.columns(3)
        with fw1: btn_lw = st.button("🟢 Sol Kanat", use_container_width=True)
        with fw2: btn_cf = st.button("🟢 Santrafor", use_container_width=True)
        with fw3: btn_rw = st.button("🟢 Sağ Kanat", use_container_width=True)

        st.markdown("#### 🔄 Orta Saha")
        mf1, mf2, mf3 = st.columns(3)
        with mf1: btn_cm = st.button("🟡 Merkez OS", use_container_width=True)
        with mf2: btn_am = st.button("🟡 Ofansif OS", use_container_width=True)
        with mf3: btn_dm = st.button("🟡 Defansif OS", use_container_width=True)

        st.markdown("#### 🛡️ Defans")
        df1, df2, df3, df4 = st.columns(4)
        with df1: btn_lb = st.button("🔵 Sol Bek", use_container_width=True)
        with df2: btn_cb1 = st.button("🔵 Stoper (1)", use_container_width=True)
        with df3: btn_cb2 = st.button("🔵 Stoper (2)", use_container_width=True)
        with df4: btn_rb = st.button("🔵 Sağ Bek", use_container_width=True)

        st.markdown("#### 🧤 Kale")
        gk1, gk2, gk3 = st.columns([1, 1, 1])
        with gk2: btn_gk = st.button("🟣 Kaleci", use_container_width=True)

        target_pos = None
        if btn_cf: target_pos = "Centre-Forward"
        elif btn_lw: target_pos = "Left Winger"
        elif btn_rw: target_pos = "Right Winger"
        elif btn_cm: target_pos = "Central Midfield"
        elif btn_am: target_pos = "Attacking Midfield"
        elif btn_dm: target_pos = "Defensive Midfield"
        elif btn_cb1 or btn_cb2: target_pos = "Centre-Back"
        elif btn_lb: target_pos = "Left-Back"
        elif btn_rb: target_pos = "Right-Back"
        elif btn_gk: target_pos = "Goalkeeper"

        if target_pos:
            pos_df = df[df["position"] == target_pos][["player", "team", "dob_age", "market_value_numeric", "predicted_market_value", "value_difference_pct"]].copy()
            pos_df = pos_df.rename(columns={
                "player": "Oyuncu", "team": "Takım", "dob_age": "Yaş",
                "market_value_numeric": "Gerçek Değer", "predicted_market_value": "AI Tahmini", "value_difference_pct": "Fark %"
            })
            st.success(f"🔍 **{target_pos}** mevkisi için en iyi fırsat transferleri:")
            if not pos_df.empty:
                # Üst 3 oyuncunun fotoğraflarını göster
                top3 = pos_df.sort_values("Fark %", ascending=False).head(3)
                img_cols = st.columns(3)
                for idx, (_, row) in enumerate(top3.iterrows()):
                    with img_cols[idx]:
                        show_player_img(row["Oyuncu"], width=100)
                        st.markdown(f"**{row['Oyuncu']}**")
                        st.caption(f"{row['Takım']} | Fark: {row['Fark %']:.1f}%")

                st.markdown("---")
                def show_scout_table(data):
                    st.dataframe(
                        data.style.format({"Gerçek Değer": "€{:,.0f}", "AI Tahmini": "€{:,.0f}", "Fark %": "{:.1f}%"}),
                        use_container_width=True, hide_index=True
                    )
                show_scout_table(pos_df.sort_values("Fark %", ascending=False).head(8))
            else:
                st.warning("Bu pozisyonda yeterli veri bulunamadı.")


# ==============================================================================
# PANEL 2: BAĞLAMSAL xG (HUZEYFE)
# ==============================================================================
elif panel_secimi == "Bağlamsal xG Paneli (Huzeyfe)":
    st.header("⚽ Bağlamsal xG (cxG) Analizi")
    st.markdown("Bu modül, şut çekilen anın tansiyonunu ve rakip baskısını hesaba katarak oyuncuların gerçek bitiricilik yeteneklerini (Contextual xG) hesaplar.")

    cxg_data_path = os.path.join(base_dir, "data", "2526_PL_Clean Data", "PL_Model", "player_cxg_analysis.csv")

    if os.path.exists(cxg_data_path):
        cxg_df = pd.read_csv(cxg_data_path)
        st.success("Bağlamsal xG Verileri Başarıyla Yüklendi ✅")

        st.subheader("📊 En Yüksek Katkı Verenler (cxG Overperformance)")
        st.markdown("**Modelimizin tahmininden çok daha fazla gol atan** en bitirici oyuncular:")

        top_performers = cxg_df.sort_values(by="Overperformance_cxG", ascending=False).head(10)
        st.dataframe(
            top_performers[["player", "team", "Total_Shots", "Actual_Goals", "Classic_xG", "Contextual_xG", "Overperformance_cxG"]].style.format({
                "Classic_xG": "{:.2f}", "Contextual_xG": "{:.2f}", "Overperformance_cxG": "{:+.2f}"
            }),
            use_container_width=True, hide_index=True
        )

        st.divider()
        st.subheader("👤 Bireysel Oyuncu Karşılaştırması")
        selected_cxg_player = st.selectbox("Oyuncu Seç:", sorted(cxg_df["player"].unique()))
        cxg_player_data = cxg_df[cxg_df["player"] == selected_cxg_player].iloc[0]

        # Profil (FOTOĞRAF + LOGO)
        c_img, c_info, c_logo = st.columns([1, 4, 1])
        with c_img:
            show_player_img(selected_cxg_player, width=120)
        with c_info:
            st.markdown(f"### {selected_cxg_player}")
            st.markdown(f"**Takım:** {cxg_player_data['team']}")
        with c_logo:
            show_team_logo(cxg_player_data["team"], width=80)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Şut Sayısı", int(cxg_player_data["Total_Shots"]))
        c2.metric("Gerçek Gol", int(cxg_player_data["Actual_Goals"]))
        c3.metric("Klasik xG", f"{cxg_player_data['Classic_xG']:.2f}")
        c4.metric("Bağlamsal cxG", f"{cxg_player_data['Contextual_xG']:.2f}", f"{cxg_player_data['Overperformance_cxG']:+.2f}")

        if cxg_player_data['Overperformance_cxG'] > 0:
            st.success(f"💡 {selected_cxg_player}, baskı ve maç atmosferi zorluklarına rağmen beklenenden {cxg_player_data['Overperformance_cxG']:.2f} daha fazla gol attı. Zihinsel dayanıklılığı ve bitiriciliği çok yüksek!")
        else:
            st.error(f"⚠️ {selected_cxg_player}, baskı altında beklenenden daha az gol attı (Fark: {cxg_player_data['Overperformance_cxG']:.2f}). Baskı toleransı düşük olabilir.")

        st.divider()
        st.subheader("🧠 SHAP Model Açıklanabilirliği")
        shap_path = os.path.join(base_dir, "data", "2526_PL_Clean Data", "PL_Model", "shap_summary.png")
        if os.path.exists(shap_path):
            st.image(shap_path, caption="SHAP Summary Plot", use_container_width=True)
        else:
            st.info("SHAP görseli bulunamadı. Lütfen 3_model_training.py çalıştırıldığından emin olun.")
    else:
        st.error("Oyuncu bazlı xG veri tablosu bulunamadı. Lütfen önce 4_player_based_analysis.py dosyasını çalıştırın.")
