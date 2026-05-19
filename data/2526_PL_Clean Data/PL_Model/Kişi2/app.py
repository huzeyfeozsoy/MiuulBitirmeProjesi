import streamlit as st
import pandas as pd
import numpy as np
import joblib

st.set_page_config(
    page_title="SmartClub 360",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ SmartClub 360")
st.subheader("Yapay Zeka Destekli Futbol İzleme ve Piyasa Değeri İstihbaratı")

# MODEL LOAD
model = joblib.load("player_value_model.pkl")

st.success("Model başarıyla yüklendi ✅")


# MARKET VALUE CONVERTER
def convert_market_value(value):

    if pd.isna(value):
        return np.nan

    value = str(value).replace("€", "").strip().lower()

    if value in ["-", "", "nan", "none"]:
        return np.nan

    if "m" in value:
        return float(value.replace("m", "")) * 1_000_000

    if "k" in value:
        return float(value.replace("k", "")) * 1_000

    return float(value)


# DATA LOAD
market_df = pd.read_csv("players_market_data.csv")
season_df = pd.read_csv("player_season_stats.csv")


# MARKET VALUE CLEAN
market_df["market_value_numeric"] = market_df["market_value"].apply(convert_market_value)

market_df = market_df.dropna(subset=["market_value_numeric"])


# MERGE
df = pd.merge(
    market_df,
    season_df,
    on=["team", "player"],
    how="inner"
)


# AGE CLEAN
df["display_age"] = df["dob_age"]

df["dob_age"] = (
    df["dob_age"]
    .astype(str)
    .str.extract(r"\((\d+)\)")
)

df["dob_age"] = pd.to_numeric(df["dob_age"], errors="coerce")


# NUMERIC COLUMNS
numeric_cols = [
    "matches",
    "minutes",
    "goals",
    "assists",
    "xg",
    "np_xg",
    "xa",
    "shots",
    "key_passes"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# FILTER
df = df[df["minutes"] > 0]


# FEATURE ENGINEERING
df["goal_contribution"] = df["goals"] + df["assists"]

df["goal_contribution_per90"] = (
    df["goal_contribution"] / df["minutes"]
) * 90

df["xg_xa_per90"] = (
    (df["xg"] + df["xa"]) / df["minutes"]
) * 90

df["shots_per90"] = (
    df["shots"] / df["minutes"]
) * 90

df["key_passes_per90"] = (
    df["key_passes"] / df["minutes"]
) * 90

df["np_xg_per90"] = (
    df["np_xg"] / df["minutes"]
) * 90

df["age_potential_score"] = (
    df["goal_contribution_per90"] / df["dob_age"]
)


# CLEAN
df = df.replace([np.inf, -np.inf], np.nan)


# MODEL COLUMNS
model_columns = [
    "dob_age",
    "matches",
    "minutes",
    "goals",
    "assists",
    "xg",
    "np_xg",
    "xa",
    "shots",
    "key_passes",
    "goal_contribution",
    "goal_contribution_per90",
    "xg_xa_per90",
    "shots_per90",
    "key_passes_per90",
    "np_xg_per90",
    "age_potential_score"
]


# FINAL CLEAN
df = df.dropna(subset=model_columns + ["market_value_numeric"])


st.write("Kullanılabilir oyuncu sayısı:", df.shape[0])

st.divider()


# PLAYER SELECT
st.header("🔍 Oyuncu Piyasa Değeri Tahmini")

selected_player = st.selectbox(
    "Oyuncu Seç",
    sorted(df["player"].unique())
)

player_data = df[df["player"] == selected_player].iloc[0]


# PLAYER INFO
st.subheader(f"📋 {selected_player} Oyuncu Bilgileri")


col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Takım", player_data["team"])

with col2:
    st.metric("Yaş", player_data["display_age"])

with col3:
    st.metric("Maç", int(player_data["matches"]))

with col4:
    st.metric("Gol", int(player_data["goals"]))

with col5:
    st.metric("Asist", int(player_data["assists"]))


# PREDICTION
input_data = pd.DataFrame(
    [player_data[model_columns]]
)

predicted_log = model.predict(input_data)[0]

predicted_value = np.expm1(predicted_log)

real_value = player_data["market_value_numeric"]

difference = predicted_value - real_value

difference_pct = (
    difference / real_value
) * 100


st.divider()

st.header("💰 Yapay Zeka Pazar Analizi")


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Gerçek Piyasa Değeri",
        f"{real_value:,.0f} €"
    )

with col2:
    st.metric(
        "AI Tahmini Değer",
        f"{predicted_value:,.0f} €"
    )

with col3:
    st.metric(
        "Fark",
        f"%{difference_pct:.1f}"
    )


# RESULT
if difference > 0:

    st.success(
        "🟢 Bu oyuncu DEĞERLENDİRİLMEMİŞ görünüyor. "
        "AI modeline göre piyasaya kayıtlı olabilir."
    )

else:

    st.error(
        "🔴 Bu oyuncu AŞIRI DEĞERLENMİŞ görünüyor. "
        "AI modeline göre piyasanın üzerinde olabilir."
    )


# ==============================
# SCOUT CENTER
# ==============================

st.divider()


df["predicted_market_value"] = np.expm1(model.predict(df[model_columns]))
df["value_difference"] = df["predicted_market_value"] - df["market_value_numeric"]
df["value_difference_pct"] = (df["value_difference"] / df["market_value_numeric"]) * 100

scout_df = df[[
    "player",
    "team",
    "display_age",
    "market_value_numeric",
    "predicted_market_value",
    "value_difference_pct"
]].copy()

scout_df = scout_df.rename(columns={
    "player": "Oyuncu",
    "team": "Takım",
    "display_age": "Yaş",
    "market_value_numeric": "Gerçek Değer",
    "predicted_market_value": "AI Tahmini",
    "value_difference_pct": "Fark %"
})

# ==============================
# KPI CARDS
# ==============================

best_opportunity = scout_df.sort_values("Fark %", ascending=False).iloc[0]
most_overpriced = scout_df.sort_values("Fark %", ascending=True).iloc[0]
avg_difference = scout_df["Fark %"].mean()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🎯 En Büyük Fırsat",
        best_opportunity["Oyuncu"],
        f"{best_opportunity['Fark %']:.1f}%"
    )

with col2:
    st.metric(
        "💸 En Pahalı Görünen",
        most_overpriced["Oyuncu"],
        f"{most_overpriced['Fark %']:.1f}%"
    )

with col3:
    st.metric(
        "📈 Ortalama AI Farkı",
        f"{avg_difference:.1f}%"
    )

st.divider()

# ==============================
# SCOUT COMMENT
# ==============================

st.subheader("🧠 AI Scout Yorumu")

if difference > 0:
    st.info(
        f"AI modeli, **{selected_player}** oyuncusunun mevcut piyasa değerine göre "
        f"daha yüksek bir potansiyele sahip olabileceğini düşünüyor. "
        f"Tahmini değer ile gerçek değer arasında **%{difference_pct:.1f}** pozitif fark var. "
        f"Bu oyuncu scout listesine alınabilecek bir fırsat profili taşıyor."
    )
else:
    st.warning(
        f"AI modeli, **{selected_player}** oyuncusunun mevcut piyasa değerinin "
        f"performans verilerine göre yüksek kalmış olabileceğini düşünüyor. "
        f"Tahmini değer ile gerçek değer arasında **%{difference_pct:.1f}** fark var. "
        f"Bu oyuncu transfer açısından dikkatli değerlendirilmelidir."
    )

st.divider()

# ==============================
# TABLE HELPER
# ==============================

def show_scout_table(data):
    st.dataframe(
        data.style.format({
            "Gerçek Değer": "€{:,.0f}",
            "AI Tahmini": "€{:,.0f}",
            "Fark %": "{:.1f}%"
        }),
        use_container_width=True,
        hide_index=True
    )


# ==============================
# TABS
# ==============================

tab1, tab2, tab3 = st.tabs([
    "🟢 Fırsat Oyuncular",
    "🔴 Pahalı Oyuncular",
    "💎 Transfer Hedefleri"
])

with tab1:
    st.caption("AI modeline göre gerçek piyasa değerinden daha değerli görünen oyuncular.")
    undervalued = scout_df.sort_values("Fark %", ascending=False).head(8)
    show_scout_table(undervalued)

with tab2:
    st.caption("AI modeline göre piyasa değeri performansına kıyasla yüksek görünen oyuncular.")
    overvalued = scout_df.sort_values("Fark %", ascending=True).head(8)
    show_scout_table(overvalued)

with tab3:
    st.caption("AI modeline göre fiyat/performans fırsatı sunan oyuncular.")
    transfer_targets = scout_df[
        scout_df["Fark %"] > 20
    ].sort_values("Fark %", ascending=False).head(8)

    show_scout_table(transfer_targets)







































