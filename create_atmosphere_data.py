import pandas as pd
import soccerdata as sd
import os
import sys

def flatten_cols(df):
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for col in df.columns:
            if col[0] != '':
                new_cols.append(f"{col[0]}_{col[1]}".strip('_'))
            else:
                new_cols.append(col[1])
        df.columns = new_cols
    return df

def main():
    print("="*60)
    print("Gercek Mac İci Atmosfer ve Baskı (Atmosphere & Pressure) Verisi Olusturuluyor...")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    stats2_path = os.path.join(base_dir, "data", "2526_PL_Clean Data", "team_match_stats2.csv")
    out_path = os.path.join(base_dir, "data", "2526_PL_Clean Data", "match_atmosphere_pressure.csv")

    if not os.path.exists(stats2_path):
        print(f"HATA: {stats2_path} bulunamadi!")
        sys.exit(1)
        
    # 1. Mevcut PPDA (Opta) verisini oku
    print("[1/3] team_match_stats2.csv dosyasi (PPDA verileri) okunuyor...")
    df_stats2 = pd.read_csv(stats2_path)
    
    # Sadece gerekli PPDA kolonlarini alalim
    df_ppda = df_stats2[['game_id', 'game', 'date', 'home_team', 'away_team', 'home_ppda', 'away_ppda']].copy()
    
    # 2. FBref'ten Faul ve Kart verilerini cek (Gercek gerilim verileri)
    print("[2/3] FBref'ten 'Misc' (Faul, Kart, Sertlik) istatistikleri cekiliyor...")
    try:
        fb = sd.FBref(leagues="ENG-Premier League", seasons="2526")
        df_misc = fb.read_team_match_stats(stat_type="misc").reset_index()
        df_misc = flatten_cols(df_misc)
        
        # Kolon isimlerini temizle (FBref yapisi degisebilir, en standart olanlari alacagiz)
        col_mapping = {
            'team': 'team',
            'game': 'game',
            'Performance_Fls': 'fouls_committed',
            'Performance_CrdY': 'yellow_cards',
            'Performance_CrdR': 'red_cards',
            'Performance_TklW': 'tackles_won',
            'Performance_Int': 'interceptions'
        }
        
        # Eger MultiIndex ayrismadiysa duz kolon isimlerini kontrol et
        if 'Fls' in df_misc.columns:
            col_mapping = {'team': 'team', 'game': 'game', 'Fls': 'fouls_committed', 'CrdY': 'yellow_cards', 'CrdR': 'red_cards', 'TklW': 'tackles_won', 'Int': 'interceptions'}
            
        available_cols = [c for c in col_mapping.keys() if c in df_misc.columns]
        df_misc_clean = df_misc[available_cols].rename(columns=col_mapping)
        
    except Exception as e:
        print(f"FBref verisi cekilirken hata olustu: {e}")
        return

    print("[3/3] Veriler birlestiriliyor ve 'Atmosfer Indeksi' hesaplaniyor...")
    
    # Ev sahibi ve Deplasman verilerini ayir ve merge icin hazirla
    df_home_misc = df_misc_clean.copy()
    df_home_misc.columns = [f'home_{c}' if c not in ['game'] else c for c in df_home_misc.columns]
    
    df_away_misc = df_misc_clean.copy()
    df_away_misc.columns = [f'away_{c}' if c not in ['game'] else c for c in df_away_misc.columns]

    # Ana tabloya (team_match_stats2 sirasina gore) merge edelim
    df_final = pd.merge(df_ppda, df_home_misc, on=['game', 'home_team'], how='left')
    df_final = pd.merge(df_final, df_away_misc, on=['game', 'away_team'], how='left')

    # --- ATMOSFER VE GERİLİM İNDEKSLERİNİ HESAPLAMA ---
    
    # 1. Total Match Tension (Macin Toplam Gerilimi: Faul ve Kartlar)
    # Sarikart carpanı 3, Kirmizi kart carpani 10 olarak agirliklandirildi.
    df_final['total_match_fouls'] = df_final['home_fouls_committed'] + df_final['away_fouls_committed']
    df_final['total_match_cards'] = (df_final['home_yellow_cards'] + df_final['away_yellow_cards']) * 3 + \
                                    (df_final['home_red_cards'] + df_final['away_red_cards']) * 10
                                    
    # 2. Pressing Intensity (Baskı Siddeti - PPDA)
    # PPDA ne kadar dusukse baski o kadar yuksektir. Ters oranti kuralim.
    df_final['avg_match_ppda'] = (df_final['home_ppda'] + df_final['away_ppda']) / 2
    # Maksimum PPDA genelde 25 civaridir, Baski skoru = 25 - PPDA
    df_final['pressing_intensity_score'] = 25 - df_final['avg_match_ppda']
    
    # 3. YEKPARE ATMOSFER & BASKI İNDEKSİ (0-100 arasi normalize edilebilir)
    # Formül: (Toplam Faul) + (Toplam Kart Puanı) + (Baskı Siddeti * 2)
    df_final['Atmosphere_Tension_Index'] = df_final['total_match_fouls'] + df_final['total_match_cards'] + (df_final['pressing_intensity_score'] * 2)

    # Dosyayi kaydet
    df_final.to_csv(out_path, index=False)
    print(f"\nISLEM TAMAMLANDI!")
    print(f"Gercek saha ici olaylara (Faul, PPDA, Kartlar) dayali yepyeni CSV dosyaniz yaratildi:")
    print(f"Dosya Yolu: {out_path}")
    print("="*60)

if __name__ == "__main__":
    main()
