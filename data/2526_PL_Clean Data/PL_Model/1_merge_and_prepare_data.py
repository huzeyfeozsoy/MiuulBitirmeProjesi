import pandas as pd
import os
import datetime

def main():
    print("="*60)
    print("Makine Öğrenmesi İçin Veri Hazırlığı (Feature Engineering)")
    print("="*60)
    
    # Dosya yollarını ayarlayalım
    base_dir = os.path.dirname(os.path.abspath(__file__)) # PL_Model klasörü
    data_dir = os.path.dirname(base_dir) # 2526_PL_Clean Data klasörü
    
    shots_path = os.path.join(data_dir, 'shot_events_clean.csv')
    atmos_path = os.path.join(data_dir, 'match_atmosphere_pressure.csv')
    out_path = os.path.join(base_dir, 'model_ready_data.csv')
    
    print("[1/3] Veriler yükleniyor...")
    df_shots = pd.read_csv(shots_path)
    df_atmos = pd.read_csv(atmos_path)
    
    # Atmosfer verisinden sadece ihtiyacımız olan kolonları alalım
    atmos_cols = [
        'game_id', 'home_team', 'away_team', 
        'home_ppda', 'away_ppda', 
        'home_fouls_committed', 'away_fouls_committed',
        'home_yellow_cards', 'away_yellow_cards',
        'home_red_cards', 'away_red_cards',
        'total_match_fouls', 'total_match_cards', 
        'avg_match_ppda', 'pressing_intensity_score', 
        'Atmosphere_Tension_Index'
    ]
    df_atmos_sub = df_atmos[atmos_cols]
    
    print("[2/3] Şut verisi ile atmosfer verisi birleştiriliyor...")
    df_merged = pd.merge(df_shots, df_atmos_sub, on='game_id', how='left')
    
    print("[3/3] Bağlamsal özellikler (Feature Engineering) hesaplanıyor...")
    
    # 1. Domain knowledge feature (iş mantığı)
    # Neden: Şutu çeken takıma uygulanan asıl baskıyı (rakip PPDA) bulmak xG kalitesini etkiler.
    df_merged['NEW_OPPONENT_PPDA'] = df_merged.apply(lambda row: row['away_ppda'] if row['team'] == row['home_team'] else row['home_ppda'], axis=1)
    
    # 2. Flag/binary feature (koşullu 0/1)
    # Neden: Ortalama üstü tansiyonlu maçları belirleyip baskı altındaki oyuncu performansını görmek için.
    avg_tension = df_merged['Atmosphere_Tension_Index'].mean()
    df_merged['NEW_IS_HIGH_TENSION'] = (df_merged['Atmosphere_Tension_Index'] > avg_tension).astype(int)
    
    # 3. Date-based feature (zaman/süre)
    # Neden: Şutun maçın sonlarına doğru (yorgunluk anında) çekilip çekilmediğini modele öğretmek için.
    df_merged['NEW_IS_LATE_GAME'] = (df_merged['minute'] >= 75).astype(int)
    
    # 4. Interaction feature (iki sütunun kombinasyonu)
    # Neden: Hem yüksek baskı hem de yüksek maç gerilimi aynı anda olduğunda şut kalitesinin nasıl düştüğünü görmek için.
    df_merged['NEW_TENSION_X_PPDA'] = df_merged['Atmosphere_Tension_Index'] * df_merged['avg_match_ppda']
    
    # 5. Ratio feature (col1 / (col2 + 1))
    # Neden: Maçtaki faullerin genel takım baskısına (PPDA) oranını bularak oyunun ne kadar fiziksel geçtiğini ölçmek için.
    df_merged['NEW_FOULS_PER_PPDA'] = df_merged['total_match_fouls'] / (df_merged['avg_match_ppda'] + 1)
    
    # 6. Aggregation feature (sum/mean across columns)
    # Neden: Ev sahibi ve deplasman takımlarının tüm kartlarını toplayarak maçın toplam agresifliğini (agresiflik indeksi) bulmak için.
    df_merged['NEW_TOTAL_CARDS'] = df_merged[['home_yellow_cards', 'away_yellow_cards', 'home_red_cards', 'away_red_cards']].sum(axis=1)

    # Hedef Değişken (Target): Şut Gol Oldu Mu? (is_goal)
    if 'is_goal' not in df_merged.columns and 'result' in df_merged.columns:
        df_merged['is_goal'] = (df_merged['result'] == 'Goal').astype(int)
    
    df_merged.to_csv(out_path, index=False)
    print(f"\nİŞLEM TAMAMLANDI!")
    print(f"Modelleme için hazır veri kümesi (model_ready_data.csv) kaydedildi.")
    print(f"Toplam Şut (Satır): {len(df_merged)}, Toplam Özellik (Sütun): {len(df_merged.columns)}")
    print(f"Dosya Yolu: {out_path}")
    print("="*60)

if __name__ == '__main__':
    main()
