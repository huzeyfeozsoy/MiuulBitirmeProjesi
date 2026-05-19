"""
Premier League 2025/26 - Detaylik Mac ve Oyuncu Istatistikleri
- Her mac icin: goller, kartlar, degisiklikler, ilk 11, formasyon, istatistikler
- Her oyuncu icin: toplam gol, asist, dakika, kart vb. agregasyonlar
API: football-data.org v4
"""

import requests
import json
import csv
import os
import time
import sys
from datetime import datetime

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

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Rate limiting: 10 requests per minute (free tier)
REQUEST_COUNT = 0
REQUEST_WINDOW_START = time.time()


def rate_limited_get(url, params=None):
    """API istegi yap, rate limit'e uy."""
    global REQUEST_COUNT, REQUEST_WINDOW_START

    # Her 10 istekte 62 saniye bekle
    if REQUEST_COUNT >= 10:
        elapsed = time.time() - REQUEST_WINDOW_START
        if elapsed < 62:
            wait = 62 - elapsed
            print(f"    [Rate limit] {wait:.0f}s bekleniyor...", flush=True)
            time.sleep(wait)
        REQUEST_COUNT = 0
        REQUEST_WINDOW_START = time.time()

    resp = requests.get(url, headers=HEADERS, params=params)

    REQUEST_COUNT += 1

    if resp.status_code == 429:
        # Rate limited - bekle ve tekrar dene
        print("    [429] Rate limited! 65s bekleniyor...", flush=True)
        time.sleep(65)
        REQUEST_COUNT = 0
        REQUEST_WINDOW_START = time.time()
        return rate_limited_get(url, params)

    resp.raise_for_status()
    return resp.json()


def load_match_ids():
    """Onceden cekilmis matches_raw.json'dan bitmis maclarin ID'lerini al."""
    path = os.path.join(DATA_DIR, "matches_raw.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    matches = data.get("matches", [])
    finished = [m for m in matches if m["status"] == "FINISHED"]
    print(f"  Toplam {len(matches)} mac, {len(finished)} tanesi bitmis (FINISHED).", flush=True)
    return finished


def load_player_ids():
    """Onceden cekilmis teams_raw.json'dan oyuncu ID'lerini al."""
    path = os.path.join(DATA_DIR, "teams_raw.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    players = []
    for team in data.get("teams", []):
        for p in team.get("squad", []):
            players.append({
                "player_id": p["id"],
                "player_name": p.get("name", ""),
                "team_id": team["id"],
                "team_name": team["name"],
            })
    print(f"  Toplam {len(players)} oyuncu bulundu.", flush=True)
    return players


# ==============================================================================
# PART 1: MAC DETAYLARI
# ==============================================================================

def fetch_match_details(finished_matches):
    """Her bitmis mac icin detayli veri cek."""
    print(f"\n{'='*60}", flush=True)
    print(f"  PART 1: Mac Detaylari Cekiliyor ({len(finished_matches)} mac)", flush=True)
    print(f"  Tahmini sure: ~{len(finished_matches) // 10 * 1 + 2} dakika", flush=True)
    print(f"{'='*60}", flush=True)

    all_goals = []
    all_bookings = []
    all_substitutions = []
    all_lineups = []
    all_match_stats = []
    all_match_details_raw = []

    # Check for existing progress
    progress_file = os.path.join(DATA_DIR, "_match_progress.json")
    done_ids = set()
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress = json.load(f)
            done_ids = set(progress.get("done_ids", []))
            all_goals = progress.get("goals", [])
            all_bookings = progress.get("bookings", [])
            all_substitutions = progress.get("substitutions", [])
            all_lineups = progress.get("lineups", [])
            all_match_stats = progress.get("match_stats", [])
        print(f"  Onceki ilerleme yuklendi: {len(done_ids)} mac zaten cekilmis.", flush=True)

    remaining = [m for m in finished_matches if m["id"] not in done_ids]
    total = len(finished_matches)

    for i, match in enumerate(remaining):
        mid = match["id"]
        matchday = match.get("matchday", "?")
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        idx = len(done_ids) + i + 1
        print(f"  [{idx}/{total}] MD{matchday}: {home} vs {away} (id={mid})", flush=True)

        try:
            detail = rate_limited_get(f"{BASE_URL}/matches/{mid}")
        except Exception as e:
            print(f"    HATA: {e}", flush=True)
            continue

        all_match_details_raw.append(detail)

        # --- Goals ---
        for g in detail.get("goals", []):
            all_goals.append({
                "match_id": mid,
                "matchday": matchday,
                "minute": g.get("minute"),
                "injury_time": g.get("injuryTime"),
                "goal_type": g.get("type"),
                "team_id": g.get("team", {}).get("id"),
                "team_name": g.get("team", {}).get("name"),
                "scorer_id": g.get("scorer", {}).get("id") if g.get("scorer") else None,
                "scorer_name": g.get("scorer", {}).get("name") if g.get("scorer") else None,
                "assist_id": g.get("assist", {}).get("id") if g.get("assist") else None,
                "assist_name": g.get("assist", {}).get("name") if g.get("assist") else None,
                "score_home": g.get("score", {}).get("home"),
                "score_away": g.get("score", {}).get("away"),
            })

        # --- Bookings ---
        for b in detail.get("bookings", []):
            all_bookings.append({
                "match_id": mid,
                "matchday": matchday,
                "minute": b.get("minute"),
                "team_id": b.get("team", {}).get("id"),
                "team_name": b.get("team", {}).get("name"),
                "player_id": b.get("player", {}).get("id"),
                "player_name": b.get("player", {}).get("name"),
                "card": b.get("card"),
            })

        # --- Substitutions ---
        for s in detail.get("substitutions", []):
            all_substitutions.append({
                "match_id": mid,
                "matchday": matchday,
                "minute": s.get("minute"),
                "team_id": s.get("team", {}).get("id"),
                "team_name": s.get("team", {}).get("name"),
                "player_out_id": s.get("playerOut", {}).get("id"),
                "player_out_name": s.get("playerOut", {}).get("name"),
                "player_in_id": s.get("playerIn", {}).get("id"),
                "player_in_name": s.get("playerIn", {}).get("name"),
            })

        # --- Lineups ---
        for side in ["homeTeam", "awayTeam"]:
            team_data = detail.get(side, {})
            team_id = team_data.get("id")
            team_name = team_data.get("name")
            formation = team_data.get("formation")
            coach_name = team_data.get("coach", {}).get("name") if team_data.get("coach") else None

            for p in team_data.get("lineup", []):
                all_lineups.append({
                    "match_id": mid,
                    "matchday": matchday,
                    "team_id": team_id,
                    "team_name": team_name,
                    "formation": formation,
                    "coach": coach_name,
                    "player_id": p.get("id"),
                    "player_name": p.get("name"),
                    "position": p.get("position"),
                    "shirt_number": p.get("shirtNumber"),
                    "lineup_type": "STARTING",
                })

            for p in team_data.get("bench", []):
                all_lineups.append({
                    "match_id": mid,
                    "matchday": matchday,
                    "team_id": team_id,
                    "team_name": team_name,
                    "formation": formation,
                    "coach": coach_name,
                    "player_id": p.get("id"),
                    "player_name": p.get("name"),
                    "position": p.get("position"),
                    "shirt_number": p.get("shirtNumber"),
                    "lineup_type": "BENCH",
                })

            # --- Match Statistics ---
            stats = team_data.get("statistics", {})
            if stats:
                all_match_stats.append({
                    "match_id": mid,
                    "matchday": matchday,
                    "team_id": team_id,
                    "team_name": team_name,
                    "side": side.replace("Team", ""),
                    "corner_kicks": stats.get("corner_kicks"),
                    "free_kicks": stats.get("free_kicks"),
                    "goal_kicks": stats.get("goal_kicks"),
                    "offsides": stats.get("offsides"),
                    "fouls": stats.get("fouls"),
                    "ball_possession": stats.get("ball_possession"),
                    "saves": stats.get("saves"),
                    "throw_ins": stats.get("throw_ins"),
                    "shots": stats.get("shots"),
                    "shots_on_goal": stats.get("shots_on_goal"),
                    "shots_off_goal": stats.get("shots_off_goal"),
                    "yellow_cards": stats.get("yellow_cards"),
                    "yellow_red_cards": stats.get("yellow_red_cards"),
                    "red_cards": stats.get("red_cards"),
                })

        done_ids.add(mid)

        # Her 20 macta bir progress kaydet
        if (i + 1) % 20 == 0:
            print(f"  ... Ilerleme kaydediliyor ({len(done_ids)}/{total})...", flush=True)
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump({
                    "done_ids": list(done_ids),
                    "goals": all_goals,
                    "bookings": all_bookings,
                    "substitutions": all_substitutions,
                    "lineups": all_lineups,
                    "match_stats": all_match_stats,
                }, f, ensure_ascii=False)

    # Save all CSVs
    print(f"\n  CSV dosyalari kaydediliyor...", flush=True)

    def save_csv(filename, data):
        if not data:
            print(f"    {filename}: Veri yok, atlanıyor.", flush=True)
            return
        path = os.path.join(DATA_DIR, filename)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"    {filename}: {len(data)} satir", flush=True)

    save_csv("goals.csv", all_goals)
    save_csv("bookings.csv", all_bookings)
    save_csv("substitutions.csv", all_substitutions)
    save_csv("lineups.csv", all_lineups)
    save_csv("match_stats.csv", all_match_stats)

    # Save raw JSON
    if all_match_details_raw:
        with open(os.path.join(DATA_DIR, "match_details_raw.json"), "w", encoding="utf-8") as f:
            json.dump(all_match_details_raw, f, ensure_ascii=False, indent=2)

    # Cleanup progress file
    if os.path.exists(progress_file):
        os.remove(progress_file)

    return all_goals, all_bookings, all_substitutions, all_lineups, all_match_stats


# ==============================================================================
# PART 2: OYUNCU BAZLI ISTATISTIKLER
# ==============================================================================

def fetch_player_stats(players):
    """Her oyuncu icin sezon agregasyon istatistiklerini cek."""
    print(f"\n{'='*60}", flush=True)
    print(f"  PART 2: Oyuncu Istatistikleri Cekiliyor ({len(players)} oyuncu)", flush=True)
    print(f"  Tahmini sure: ~{len(players) // 10 * 1 + 2} dakika", flush=True)
    print(f"{'='*60}", flush=True)

    all_player_stats = []

    # Check for existing progress
    progress_file = os.path.join(DATA_DIR, "_player_progress.json")
    done_ids = set()
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress = json.load(f)
            done_ids = set(progress.get("done_ids", []))
            all_player_stats = progress.get("player_stats", [])
        print(f"  Onceki ilerleme yuklendi: {len(done_ids)} oyuncu zaten cekilmis.", flush=True)

    remaining = [p for p in players if p["player_id"] not in done_ids]
    total = len(players)

    for i, player in enumerate(remaining):
        pid = player["player_id"]
        pname = player["player_name"]
        team = player["team_name"]
        idx = len(done_ids) + i + 1
        print(f"  [{idx}/{total}] {pname} ({team})", flush=True)

        try:
            data = rate_limited_get(
                f"{BASE_URL}/persons/{pid}/matches",
                params={"competitions": "PL", "season": SEASON, "limit": 100}
            )
        except Exception as e:
            print(f"    HATA: {e}", flush=True)
            continue

        agg = data.get("aggregations", {})
        person = data.get("person", {})
        result_set = data.get("resultSet", {})

        all_player_stats.append({
            "player_id": pid,
            "player_name": person.get("name", pname),
            "first_name": person.get("firstName"),
            "last_name": person.get("lastName"),
            "date_of_birth": person.get("dateOfBirth"),
            "nationality": person.get("nationality"),
            "position": person.get("position"),
            "shirt_number": person.get("shirtNumber"),
            "team_id": player["team_id"],
            "team_name": player["team_name"],
            "matches_on_pitch": agg.get("matchesOnPitch", 0),
            "starting_xi": agg.get("startingXI", 0),
            "minutes_played": agg.get("minutesPlayed", 0),
            "goals": agg.get("goals", 0),
            "own_goals": agg.get("ownGoals", 0),
            "assists": agg.get("assists", 0),
            "penalties": agg.get("penalties", 0),
            "subbed_out": agg.get("subbedOut", 0),
            "subbed_in": agg.get("subbedIn", 0),
            "yellow_cards": agg.get("yellowCards", 0),
            "yellow_red_cards": agg.get("yellowRedCards", 0),
            "red_cards": agg.get("redCards", 0),
            "total_matches_in_result": result_set.get("count", 0),
        })

        done_ids.add(pid)

        # Her 30 oyuncuda bir progress kaydet
        if (i + 1) % 30 == 0:
            print(f"  ... Ilerleme kaydediliyor ({len(done_ids)}/{total})...", flush=True)
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump({
                    "done_ids": list(done_ids),
                    "player_stats": all_player_stats,
                }, f, ensure_ascii=False)

    # Save CSV
    print(f"\n  CSV dosyasi kaydediliyor...", flush=True)
    if all_player_stats:
        path = os.path.join(DATA_DIR, "player_season_stats.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_player_stats[0].keys())
            writer.writeheader()
            writer.writerows(all_player_stats)
        print(f"    player_season_stats.csv: {len(all_player_stats)} satir", flush=True)

    # Save raw JSON
    with open(os.path.join(DATA_DIR, "player_stats_raw.json"), "w", encoding="utf-8") as f:
        json.dump(all_player_stats, f, ensure_ascii=False, indent=2)

    # Cleanup progress file
    if os.path.exists(progress_file):
        os.remove(progress_file)

    return all_player_stats


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    start_time = time.time()
    print(f"{'='*60}", flush=True)
    print(f"  Premier League 2025/26 - Detayli Veri Cekme", flush=True)
    print(f"  Baslangic: {datetime.now().strftime('%H:%M:%S')}", flush=True)
    print(f"{'='*60}", flush=True)

    # Load existing data
    finished_matches = load_match_ids()
    players = load_player_ids()

    # PART 1: Match details
    goals, bookings, subs, lineups, match_stats = fetch_match_details(finished_matches)

    # PART 2: Player stats
    player_stats = fetch_player_stats(players)

    # SUMMARY
    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print(f"\n{'='*60}", flush=True)
    print(f"  OZET", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  Dosyalar: {DATA_DIR}", flush=True)
    print(f"  Goller:              {len(goals)}", flush=True)
    print(f"  Kartlar:             {len(bookings)}", flush=True)
    print(f"  Degisiklikler:       {len(subs)}", flush=True)
    print(f"  Kadro kayitlari:     {len(lineups)}", flush=True)
    print(f"  Mac istatistikleri:  {len(match_stats)}", flush=True)
    print(f"  Oyuncu sezon stat:   {len(player_stats)}", flush=True)
    print(f"  Sure: {mins}dk {secs}s", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"  Tamamlandi!", flush=True)
