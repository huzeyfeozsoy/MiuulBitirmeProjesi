import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.model_selection import cross_val_score, KFold

# CSV dosyalarını oku
market_df = pd.read_csv(r"..\..\players_market_data.csv")
season_df = pd.read_csv(r"..\..\player_season_stats.csv")

# Dataset boyutları
print("Market Shape:", market_df.shape)
print("Season Shape:", season_df.shape)

# İlk 5 satır
print("\nMARKET DATA:")
print(market_df.head())

print("\nSEASON DATA:")
print(season_df.head())

# Kolon isimleri
print("\nMARKET COLUMNS:")
print(market_df.columns)

print("\nSEASON COLUMNS:")
print(season_df.columns)

def convert_market_value(value):
    if pd.isna(value):
        return np.nan

    value = str(value).replace("€", "").strip().lower()

    # boş / bilinmeyen değerleri yakala
    if value in ["-", "", "nan", "none"]:
        return np.nan

    if "m" in value:
        return float(value.replace("m", "")) * 1_000_000

    elif "k" in value:
        return float(value.replace("k", "")) * 1_000

    else:
        return float(value)


market_df["market_value_numeric"] = market_df["market_value"].apply(convert_market_value)

print(market_df[["player", "market_value", "market_value_numeric"]].head(10))
print("Eksik market value:", market_df["market_value_numeric"].isna().sum())

df_market_clean = market_df.dropna(subset=["market_value_numeric"])

print("Clean Market Shape:", df_market_clean.shape)

df = pd.merge(
    df_market_clean,
    season_df,
    on=["player"],
    how="inner",
    suffixes=("_market", "_season")
)
df["team"] = df["team_market"]

print("Merged Shape:", df.shape)
print(df.head())
print(df.columns)

print(df.columns)




# ==============================
# FEATURE ENGINEERING
# ==============================

# Yaş kolonunu temizle
df["dob_age"] = df["dob_age"].astype(str).str.extract(r"\((\d+)\)")[0]
df["dob_age"] = pd.to_numeric(df["dob_age"], errors="coerce")

numeric_cols = [
    "matches", "minutes", "goals", "assists",
    "xg", "np_xg", "xa", "shots", "key_passes",
    "yellow_cards", "red_cards", "xg_chain", "xg_buildup"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print("Before Cleaning Shape:", df.shape)

print(df[[
    "player", "dob_age", "minutes", "goals", "assists",
    "xg", "xa", "shots", "market_value_numeric"
]].head(10))

df["goal_contribution"] = df["goals"] + df["assists"]
df["goal_contribution_per90"] = (df["goal_contribution"] / df["minutes"]) * 90
df["xg_xa_per90"] = ((df["xg"] + df["xa"]) / df["minutes"]) * 90
df["shots_per90"] = (df["shots"] / df["minutes"]) * 90
df["key_passes_per90"] = (df["key_passes"] / df["minutes"]) * 90
df["np_xg_per90"] = (df["np_xg"] / df["minutes"]) * 90
df["age_potential_score"] = df["goal_contribution_per90"] / df["dob_age"]

df = df.replace([np.inf, -np.inf], np.nan)

df = df[df["minutes"] > 400]

critical_columns = [
    "dob_age",
    "minutes",
    "goals",
    "assists",
    "xg",
    "xa",
    "shots",
    "market_value_numeric"
]

print("\nMissing Values Before Drop:")
print(df[critical_columns].isna().sum())

df = df.dropna(subset=critical_columns)

print("\nFinal Model Data Shape:", df.shape)

print(df[[
    "player",
    "dob_age",
    "minutes",
    "market_value_numeric",
    "goal_contribution_per90",
    "xg_xa_per90"
]].head(10))
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
# ==============================
# MODEL TRAINING
# ==============================

X = df[model_columns]
y = df["market_value_numeric"]

y_log = np.log1p(y)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_log,
    test_size=0.2,
    random_state=42
)

model = RandomForestRegressor(
    n_estimators=300,
    random_state=42
)

model.fit(X_train, y_train)

# ==============================
# CROSS VALIDATION
# ==============================
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y_log, cv=kf, scoring='r2')

y_pred_log = model.predict(X_test)

y_test_real = np.expm1(y_test)
y_pred_real = np.expm1(y_pred_log)

mae = mean_absolute_error(y_test_real, y_pred_real)
rmse = np.sqrt(mean_squared_error(y_test_real, y_pred_real))
r2 = r2_score(y_test_real, y_pred_real)

print("\nMODEL RESULTS (HOLDOUT)")
print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 3))

print("\nCROSS VALIDATION RESULTS (5-Fold)")
print(f"CV R2 Scores: {cv_scores}")
print(f"Mean CV R2: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")


# ==============================
# SCOUTING INSIGHT SYSTEM
# ==============================

# Tüm oyuncular için tahmin üret
all_predictions_log = model.predict(X)

# Log tahmini gerçek para değerine çevir
all_predictions_real = np.expm1(all_predictions_log)

# Tahminleri dataframe'e ekle
df["predicted_market_value"] = all_predictions_real

# Gerçek değer - tahmin farkı
df["value_difference"] = df["predicted_market_value"] - df["market_value_numeric"]

# Yüzdesel fark
df["value_difference_pct"] = (
    df["value_difference"] / df["market_value_numeric"]
) * 100


# ==============================
# TOP UNDERVALUED PLAYERS
# ==============================

undervalued_players = df.sort_values(
    by="value_difference",
    ascending=False
)

print("\nTOP UNDERVALUED PLAYERS")
print(undervalued_players[[
    "player",
    "team",
    "market_value_numeric",
    "predicted_market_value",
    "value_difference",
    "value_difference_pct",
    "goal_contribution_per90",
    "xg_xa_per90"
]].head(15))

# Yapılan model çıktısında ki oyuncular modelin gözünde daha değerli. Yani normal değeri marketplaceden daha fazla oyuncuları çıkartıyor


# ==============================
# FEATURE IMPORTANCE
# ==============================

#Oyuncunun değerini neler belirlediğini bulacaz

importance_df = pd.DataFrame({
    "feature": model_columns,
    "importance": model.feature_importances_
})

importance_df = importance_df.sort_values(
    by="importance",
    ascending=False
)

print("\nFEATURE IMPORTANCE")
print(importance_df)

# Market valuesine en çok etkileyenleri buluyoruz
# (1.şut sayısı 2.maç sayısı 3.oynanan dakika 4.yaş 5.xA) etkiliyormuş

# ==============================
# TRANSFER RECOMMENDATION ENGINE (TRANSFER ÖNERİ MOTORU)
# ==============================

transfer_targets = df[
    (df["dob_age"] <= 24) &
    (df["value_difference_pct"] > 20)
]

transfer_targets = transfer_targets.sort_values(
    by="value_difference_pct",
    ascending=False
)

print("\nTOP TRANSFER TARGETS")

print(transfer_targets[[
    "player",
    "team",
    "dob_age",
    "market_value_numeric",
    "predicted_market_value",
    "value_difference_pct",
    "goal_contribution_per90",
    "xg_xa_per90"
]].head(10))

#Çıkan çıktıda ki oyuncular mevcut fiyatlarına göre hala ucuz diyor


# ==============================
# SAVE MODEL
# ==============================

import joblib

joblib.dump(model, "player_value_model.pkl")

print("\nMODEL SAVED SUCCESSFULLY")



































