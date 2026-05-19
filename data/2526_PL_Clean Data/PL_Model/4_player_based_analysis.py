################################################
# Player-Based Contextual xG (cxG) Analysis
################################################

import os
import joblib
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def main():
    print("="*60)
    print("OYUNCU BAZLI CONTEXTUAL xG (cxG) ANALİZİ BAŞLIYOR...")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dosya yolları
    original_data_path = os.path.join(base_dir, 'model_ready_data.csv')
    preprocessed_data_path = os.path.join(base_dir, 'model_ready_data_preprocessed.csv')
    model_path = os.path.join(base_dir, 'xg_voting_clf.pkl')
    output_path = os.path.join(base_dir, 'player_cxg_analysis.csv')
    
    # 1. Verileri ve Modeli Yükle
    print("1. Orijinal veriler, ön işlemeli veriler ve eğitilmiş model yükleniyor...")
    df_orig = pd.read_csv(original_data_path)
    df_prep = pd.read_csv(preprocessed_data_path)
    model = joblib.load(model_path)
    
    # 2. Modeli kullanarak tahmin (Probability) üretme
    print("2. Veri setindeki her bir şut için Contextual xG (cxG) hesaplanıyor...")
    # 'is_goal' kolonunu atarak özellikleri (X) oluşturuyoruz
    X = df_prep.drop(["is_goal"], axis=1)
    
    # predict_proba bize 2 değer döner: [Gol Olmama İhtimali, Gol Olma İhtimali]
    # Bize gol olma ihtimali lazım, yani index 1.
    cxg_probabilities = model.predict_proba(X)[:, 1]
    
    # 3. Hesaplanan cxG'leri orijinal veri setine ekleme
    df_orig['cxG'] = cxg_probabilities
    
    # 4. Oyuncu bazlı gruplama ve istatistik çıkarma
    print("3. Oyuncu bazında istatistikler gruplanıyor...")
    
    # Sadece golleri saymak için (is_goal 1 ise gol, 0 ise değil)
    # Eğer orijinal veride is_goal yoksa 'result' kolonunu kullanabiliriz ama model_ready'de is_goal var.
    
    player_stats = df_orig.groupby(['player', 'team']).agg(
        Total_Shots=('shot_id', 'count'),          # Toplam şut sayısı
        Actual_Goals=('is_goal', 'sum'),           # Gerçekleşen gol
        Classic_xG=('xg', 'sum'),                  # Understat'tan gelen klasik xG
        Contextual_xG=('cxG', 'sum')               # Bizim modelin hesapladığı cxG
    ).reset_index()
    
    # Sadece belli bir şut sayısının üstündeki oyuncuları alalım (Örn: en az 10 şut)
    player_stats = player_stats[player_stats['Total_Shots'] >= 10]
    
    # Performans Metrikleri Hesaplama
    # Gerçek Gol - cxG (Pozitifse, oyuncu baskı/atmosfer zorluklarına rağmen beklenenden çok gol atmış demektir)
    player_stats['Overperformance_cxG'] = player_stats['Actual_Goals'] - player_stats['Contextual_xG']
    
    # Klasik xG ile bizim cxG arasındaki fark (Modelimizin baskıyı ne kadar hesaba kattığını gösterir)
    player_stats['xG_Difference'] = player_stats['Contextual_xG'] - player_stats['Classic_xG']
    
    # Sıralama: En çok gol atandan aşağıya doğru
    player_stats = player_stats.sort_values(by='Actual_Goals', ascending=False).round(2)
    
    # 5. Sonuçları Kaydetme
    player_stats.to_csv(output_path, index=False)
    
    print("\n" + "="*60)
    print("ANALİZ TAMAMLANDI! EN GOLCÜ 15 OYUNCUNUN TABLOSU:")
    print("="*60)
    print(player_stats.head(15).to_string(index=False))
    
    print("\nSonuçlar detaylı incelenebilmesi için şu dosyaya kaydedildi:")
    print(output_path)

if __name__ == "__main__":
    main()
