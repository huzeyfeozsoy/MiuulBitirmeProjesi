import soccerdata as sd
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "understat")
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    print(f"{'='*60}")
    print("Understat Veri Cekme Islemi Basliyor (Sezon: 25/26)")
    print(f"{'='*60}")

    try:
        # Understat sinifini baslat
        us = sd.Understat(leagues="ENG-Premier League", seasons="2526")

        print("\n[1/3] Takim mac istatistikleri (Team Match Stats) cekiliyor...")
        team_stats = us.read_team_match_stats()
        if team_stats is not None and not team_stats.empty:
            team_stats.to_csv(os.path.join(DATA_DIR, "team_match_stats.csv"))
            print(f"  -> Basarili! ({len(team_stats)} kayit kaydedildi)")
        else:
            print("  -> Takim mac istatistikleri bulunamadi.")

        print("\n[2/3] Oyuncu sezonluk istatistikleri (Player Season Stats) cekiliyor...")
        player_stats = us.read_player_season_stats()
        if player_stats is not None and not player_stats.empty:
            player_stats.to_csv(os.path.join(DATA_DIR, "player_season_stats.csv"))
            print(f"  -> Basarili! ({len(player_stats)} oyuncu istatistigi kaydedildi)")
        else:
            print("  -> Oyuncu sezon istatistikleri bulunamadi.")

        print("\n[3/3] Detayli sut verileri (Shot Events) cekiliyor...")
        print("      (Maç bazinda her sutun koordinati vs. Cok uzun surebilir...)")
        shots = us.read_shot_events()
        if shots is not None and not shots.empty:
            shots.to_csv(os.path.join(DATA_DIR, "shot_events.csv"))
            print(f"  -> Basarili! ({len(shots)} sut olayi kaydedildi)")
        else:
            print("  -> Sut verileri bulunamadi.")

        print(f"\n{'='*60}")
        print("Understat Veri Cekme Islemi TAMAMLANDI!")
        print(f"Veriler suraya kaydedildi: {DATA_DIR}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\nHATA OLUSTU: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
