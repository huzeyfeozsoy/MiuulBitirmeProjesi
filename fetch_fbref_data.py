import soccerdata as sd
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fbref")
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    print(f"{'='*60}")
    print("FBref Veri Cekme Islemi Basliyor (Sezon: 25/26)")
    print(f"{'='*60}")

    try:
        # FBref sinifini baslat
        fb = sd.FBref(leagues="ENG-Premier League", seasons="2526")

        print("\n[1/3] Mac takvimi (Schedule) cekiliyor...")
        schedule = fb.read_schedule()
        if schedule is not None and not schedule.empty:
            schedule.to_csv(os.path.join(DATA_DIR, "schedule.csv"))
            print(f"  -> Basarili! ({len(schedule)} mac kaydedildi)")
        else:
            print("  -> Mac takvimi bulunamadi.")

        print("\n[2/3] Oyuncu mac loglari (Player Match Stats) cekiliyor...")
        print("      (Bu islem mac sayisina gore biraz surebilir...)")
        player_stats = fb.read_player_match_stats(stat_type="summary")
        if player_stats is not None and not player_stats.empty:
            # MultiIndex sutunlari duzlestir ve temiz adlar ver
            player_stats = player_stats.reset_index()
            flat_cols = [
                'league', 'season', 'game', 'team', 'player',
                'jersey_number', 'nation', 'position', 'age', 'minutes',
                'goals', 'assists', 'penalty_goals', 'penalty_attempts',
                'shots', 'shots_on_target', 'yellow_cards', 'red_cards',
                'fouls_committed', 'fouls_drawn', 'offsides', 'crosses',
                'tackles_won', 'interceptions', 'own_goals',
                'penalty_won', 'penalty_conceded', 'game_id',
            ]
            player_stats.columns = flat_cols
            # Tamamen bos sutunlari sil
            player_stats.drop(columns=['penalty_won', 'penalty_conceded'], inplace=True, errors='ignore')
            # age_years sutunu ekle (FBref formati: YY-GGG)
            player_stats['age_years'] = player_stats['age'].str.split('-').str[0].astype(int)
            # age_years'i age'den hemen sonraya tasi
            cols = list(player_stats.columns)
            age_idx = cols.index('age')
            cols.remove('age_years')
            cols.insert(age_idx + 1, 'age_years')
            player_stats = player_stats[cols]
            player_stats.to_csv(os.path.join(DATA_DIR, "player_match_stats_summary.csv"), index=False)
            print(f"  -> Basarili! ({len(player_stats)} oyuncu performansi kaydedildi)")
        else:
            print("  -> Oyuncu mac loglari bulunamadi.")

        print("\n[3/3] Takim mac loglari (Team Match Stats) cekiliyor...")
        team_stats = fb.read_team_match_stats(stat_type="schedule")
        if team_stats is not None and not team_stats.empty:
            team_stats.to_csv(os.path.join(DATA_DIR, "team_match_stats.csv"))
            print(f"  -> Basarili! ({len(team_stats)} takim performansi kaydedildi)")
        else:
            print("  -> Takim mac loglari bulunamadi.")

        print(f"\n{'='*60}")
        print("FBref Veri Cekme Islemi TAMAMLANDI!")
        print(f"Veriler suraya kaydedildi: {DATA_DIR}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\nHATA OLUSTU: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
