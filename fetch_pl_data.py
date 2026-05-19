"""
Premier League 2025/26 Sezonu Veri Çekme Scripti
- Maç verileri
- Oyuncu verileri
- Teknik direktör verileri
API: football-data.org v4
"""

import requests
import json
import csv
import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_TOKEN = os.environ.get("FOOTBALL_DATA_API_TOKEN")
if not API_TOKEN:
    raise EnvironmentError(
        "FOOTBALL_DATA_API_TOKEN environment variable bulunamadi. "
        "Lutfen .env.example dosyasini .env olarak kopyalayip kendi API token'inizi giriniz. "
        "Token almak icin: https://www.football-data.org/client/register"
    )

BASE_URL = "http://api.football-data.org/v4"
SEASON = 2025
HEADERS = {"X-Auth-Token": API_TOKEN}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_json(url, params=None):
    """API'den JSON verisi çek."""
    print(f"  -> İstek: {url}")
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_matches():
    """Tüm maç verilerini çek ve kaydet."""
    print("\n[1/3] Maç verileri çekiliyor...")
    data = fetch_json(f"{BASE_URL}/competitions/PL/matches", {"season": SEASON})
    matches = data.get("matches", [])
    print(f"  Toplam {len(matches)} maç bulundu.")

    # Ham JSON kaydet
    with open(os.path.join(OUTPUT_DIR, "matches_raw.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # CSV'ye düzenle
    rows = []
    for m in matches:
        rows.append({
            "match_id": m["id"],
            "matchday": m["matchday"],
            "utc_date": m["utcDate"],
            "status": m["status"],
            "home_team_id": m["homeTeam"]["id"],
            "home_team": m["homeTeam"]["name"],
            "away_team_id": m["awayTeam"]["id"],
            "away_team": m["awayTeam"]["name"],
            "home_score": m["score"]["fullTime"]["home"],
            "away_score": m["score"]["fullTime"]["away"],
            "home_halftime": m["score"]["halfTime"]["home"],
            "away_halftime": m["score"]["halfTime"]["away"],
            "winner": m["score"]["winner"],
            "duration": m["score"]["duration"],
            "stage": m["stage"],
            "referees": "; ".join([r.get("name", "") for r in m.get("referees", [])]),
        })

    csv_path = os.path.join(OUTPUT_DIR, "matches.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅ Maçlar kaydedildi -> matches.csv ({len(rows)} satır)")

    return matches


def fetch_teams_and_squads():
    """Takım, oyuncu ve teknik direktör verilerini çek ve kaydet."""
    print("\n[2/3] Takım ve kadro verileri çekiliyor...")
    data = fetch_json(f"{BASE_URL}/competitions/PL/teams", {"season": SEASON})
    teams = data.get("teams", [])
    print(f"  Toplam {len(teams)} takım bulundu.")

    # Ham JSON kaydet
    with open(os.path.join(OUTPUT_DIR, "teams_raw.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # --- Teknik Direktörler ---
    coaches = []
    for t in teams:
        coach = t.get("coach")
        if coach:
            coaches.append({
                "coach_id": coach.get("id"),
                "coach_name": coach.get("name"),
                "first_name": coach.get("firstName"),
                "last_name": coach.get("lastName"),
                "date_of_birth": coach.get("dateOfBirth"),
                "nationality": coach.get("nationality"),
                "contract_start": coach.get("contract", {}).get("start") if coach.get("contract") else None,
                "contract_until": coach.get("contract", {}).get("until") if coach.get("contract") else None,
                "team_id": t["id"],
                "team_name": t["name"],
            })

    csv_path = os.path.join(OUTPUT_DIR, "coaches.csv")
    if coaches:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=coaches[0].keys())
            writer.writeheader()
            writer.writerows(coaches)
    print(f"  ✅ Teknik direktörler kaydedildi -> coaches.csv ({len(coaches)} satır)")

    # --- Oyuncular ---
    players = []
    for t in teams:
        squad = t.get("squad", [])
        for p in squad:
            players.append({
                "player_id": p.get("id"),
                "player_name": p.get("name"),
                "position": p.get("position"),
                "date_of_birth": p.get("dateOfBirth"),
                "nationality": p.get("nationality"),
                "team_id": t["id"],
                "team_name": t["name"],
            })

    csv_path = os.path.join(OUTPUT_DIR, "players.csv")
    if players:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=players[0].keys())
            writer.writeheader()
            writer.writerows(players)
    print(f"  ✅ Oyuncular kaydedildi -> players.csv ({len(players)} satır)")

    return teams, coaches, players


def fetch_standings():
    """Puan tablosunu çek ve kaydet."""
    print("\n[3/3] Puan tablosu çekiliyor...")
    data = fetch_json(f"{BASE_URL}/competitions/PL/standings", {"season": SEASON})

    # Ham JSON kaydet
    with open(os.path.join(OUTPUT_DIR, "standings_raw.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    standings = data.get("standings", [])
    rows = []
    for table in standings:
        if table.get("type") == "TOTAL":
            for entry in table.get("table", []):
                rows.append({
                    "position": entry["position"],
                    "team_id": entry["team"]["id"],
                    "team_name": entry["team"]["name"],
                    "played": entry["playedGames"],
                    "won": entry["won"],
                    "draw": entry["draw"],
                    "lost": entry["lost"],
                    "goals_for": entry["goalsFor"],
                    "goals_against": entry["goalsAgainst"],
                    "goal_difference": entry["goalDifference"],
                    "points": entry["points"],
                    "form": entry.get("form"),
                })

    csv_path = os.path.join(OUTPUT_DIR, "standings.csv")
    if rows:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    print(f"  ✅ Puan tablosu kaydedildi -> standings.csv ({len(rows)} satır)")

    return rows


def fetch_scorers():
    """Gol kralı tablosunu çek ve kaydet."""
    print("\n[BONUS] Gol kralları çekiliyor...")
    data = fetch_json(f"{BASE_URL}/competitions/PL/scorers", {"season": SEASON})

    with open(os.path.join(OUTPUT_DIR, "scorers_raw.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    scorers = data.get("scorers", [])
    rows = []
    for s in scorers:
        player = s.get("player", {})
        team = s.get("team", {})
        rows.append({
            "player_id": player.get("id"),
            "player_name": player.get("name"),
            "first_name": player.get("firstName"),
            "last_name": player.get("lastName"),
            "date_of_birth": player.get("dateOfBirth"),
            "nationality": player.get("nationality"),
            "position": player.get("position"),
            "team_id": team.get("id"),
            "team_name": team.get("name"),
            "goals": s.get("goals"),
            "assists": s.get("assists"),
            "penalties": s.get("penalties"),
            "played_matches": s.get("playedMatches"),
        })

    csv_path = os.path.join(OUTPUT_DIR, "scorers.csv")
    if rows:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    print(f"  ✅ Gol kralları kaydedildi -> scorers.csv ({len(rows)} satır)")

    return rows


if __name__ == "__main__":
    print("=" * 60)
    print("  Premier League 2025/26 - Veri Çekme")
    print("=" * 60)

    matches = fetch_matches()
    time.sleep(6)  # API rate limit: 10 istek/dakika (free tier)

    teams, coaches, players = fetch_teams_and_squads()
    time.sleep(6)

    standings = fetch_standings()
    time.sleep(6)

    scorers = fetch_scorers()

    print("\n" + "=" * 60)
    print("  ÖZET")
    print("=" * 60)
    print(f"  📂 Dosyalar: {OUTPUT_DIR}")
    print(f"  ⚽ Maçlar:           {len(matches)}")
    print(f"  👤 Oyuncular:        {len(players)}")
    print(f"  🧑‍💼 Teknik Direktörler: {len(coaches)}")
    print(f"  📊 Puan Tablosu:     {len(standings)}")
    print(f"  🥅 Gol Kralları:     {len(scorers)}")
    print("=" * 60)
    print("  Tüm veriler başarıyla çekildi! ✅")
