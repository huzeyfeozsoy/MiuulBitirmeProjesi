import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import RobustScaler, LabelEncoder

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)

def grab_col_names(dataframe, cat_th=10, car_th=20):
    cat_cols = [col for col in dataframe.columns if dataframe[col].dtypes == "O"]
    num_but_cat = [col for col in dataframe.columns if dataframe[col].nunique() < cat_th and dataframe[col].dtypes != "O"]
    cat_but_car = [col for col in dataframe.columns if dataframe[col].nunique() > car_th and dataframe[col].dtypes == "O"]
    cat_cols = cat_cols + num_but_cat
    cat_cols = [col for col in cat_cols if col not in cat_but_car]
    num_cols = [col for col in dataframe.columns if dataframe[col].dtypes != "O"]
    num_cols = [col for col in num_cols if col not in num_but_cat]
    return cat_cols, num_cols, cat_but_car

def outlier_thresholds(dataframe, col_name, q1=0.05, q3=0.95):
    quartile1 = dataframe[col_name].quantile(q1)
    quartile3 = dataframe[col_name].quantile(q3)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit

def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit

def rare_encoder(dataframe, rare_perc):
    temp_df = dataframe.copy()
    rare_columns = [col for col in temp_df.columns if temp_df[col].dtypes == 'O' and (temp_df[col].value_counts() / len(temp_df) < rare_perc).any(axis=None)]
    for var in rare_columns:
        tmp = temp_df[var].value_counts() / len(temp_df)
        rare_labels = tmp[tmp < rare_perc].index
        temp_df[var] = np.where(temp_df[var].isin(rare_labels), 'Rare', temp_df[var])
    return temp_df

def one_hot_encoder(dataframe, categorical_cols, drop_first=True):
    dataframe = pd.get_dummies(dataframe, columns=categorical_cols, drop_first=drop_first)
    return dataframe

def main():
    print("="*60)
    print("MİUUL STANDARTLARINDA VERİ ÖN İŞLEME BAŞLIYOR...")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'model_ready_data.csv')
    out_path = os.path.join(base_dir, 'model_ready_data_preprocessed.csv')
    
    df = pd.read_csv(data_path)
    
    # 0. Gereksiz ve yüksek kardinaliteli kolonların modele girmemesi için ayıklanması
    # id, isim gibi identifier kolonlar ve 'team', 'home_team', 'away_team' gibi 
    # OHE yapıldığında boyutu patlatacak (60+ kolon) ve modele direk katkısı olmayacak kolonları atıyoruz.
    # (Şut kalitesini takımın ismi değil, şutun açısı, mesafesi ve baskı belirler - xG mantığı)
    drop_cols = ['game_id', 'game', 'date', 'player', 'player_id', 'team_id', 'shot_id', 'result', 
                 'assist_player', 'assist_player_id', 'team', 'home_team', 'away_team', 'league', 'season']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')

    print("\n[EK] Duplicate Satır Kontrolü (Veri Temizliği)")
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        print(f"{duplicates} adet tekrar eden satır siliniyor.")
        df = df.drop_duplicates()
        
    print("\n1. Değişken Tiplerinin Yakalanması (grab_col_names)")
    cat_cols, num_cols, cat_but_car = grab_col_names(df)
    
    # Hedef değişken (is_goal) num_cols ya da cat_cols içinde olabilir, ona dokunmuyoruz.
    # Ayrıca sarı/kırmızı kart gibi değişkenler < 10 eşiğinden dolayı cat_cols içine düşebilir.
    # Bunları kategorik olarak OHE'ye sokmak boyutu patlatır (yellow_card_1, yellow_card_2...).
    # Bu yüzden içinde 'card' geçenleri zorla num_cols içine alıyoruz.
    cards_and_ordinal = [col for col in cat_cols if 'card' in col.lower() or 'foul' in col.lower()]
    cat_cols = [col for col in cat_cols if col not in ['is_goal'] + cards_and_ordinal]
    num_cols = [col for col in num_cols if col not in ['is_goal', 'NEW_IS_HIGH_TENSION']] + cards_and_ordinal
    
    print("\n2. Eksik Değerler (Missing Values) Gideriliyor...")
    # Sayısal değişkenlerdeki eksikleri medyan ile doldurma
    for col in num_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].median(), inplace=True)
            
    # Kategorik değişkenlerdeki eksikleri mode ile doldurma
    for col in cat_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].mode()[0], inplace=True)
            
    # is_high_tension eksikse mode ile dolduralım
    if df['NEW_IS_HIGH_TENSION'].isnull().sum() > 0:
        df['NEW_IS_HIGH_TENSION'].fillna(df['NEW_IS_HIGH_TENSION'].mode()[0], inplace=True)

    print("\n3. Aykırı Değerlerin (Outliers) Baskılanması...")
    for col in num_cols:
        replace_with_thresholds(df, col)
        
    print("\n4. Rare Encoding (Nadir Sınıflar)...")
    # %1'den az olanları Rare yapalım
    df = rare_encoder(df, 0.01)

    print("\n5. Encoding (One-Hot & Label Encoding)...")
    # Yeniden yakalayalım çünkü Rare encode ettik
    cat_cols, num_cols, cat_but_car = grab_col_names(df)
    
    cards_and_ordinal = [col for col in cat_cols if 'card' in col.lower() or 'foul' in col.lower()]
    cat_cols = [col for col in cat_cols if col not in ['is_goal', 'NEW_IS_HIGH_TENSION'] + cards_and_ordinal]
    
    # Binary kolonları (nunique == 2) bulup Label Encoder uygulama
    binary_cols = [col for col in cat_cols if df[col].nunique() == 2 and col not in ['is_goal', 'NEW_IS_HIGH_TENSION']]
    print(f"Label Encoding uygulanacak Binary Kolonlar: {binary_cols}")
    le = LabelEncoder()
    for col in binary_cols:
        df[col] = le.fit_transform(df[col])
        
    # Kalan 3+ sınıflı kategorik değişkenlere One-Hot Encoding uygulama
    ohe_cols = [col for col in cat_cols if df[col].nunique() > 2 and col not in ['is_goal', 'NEW_IS_HIGH_TENSION'] + cards_and_ordinal]
    print(f"One-Hot Encoding uygulanacak Kolonlar: {ohe_cols}")
    
    df = one_hot_encoder(df, ohe_cols, drop_first=True)
    

    # Bool olan OHE kolonlarını 0-1 int yapalım (Bazı modeller bool sevmez)
    for col in df.columns:
        if df[col].dtype == bool:
            df[col] = df[col].astype(int)

    # Kaydetme
    df.to_csv(out_path, index=False)
    print(f"\nİŞLEM TAMAMLANDI! Pre-process edilmiş tertemiz veri kaydedildi:")
    print(f"Satır: {df.shape[0]}, Sütun: {df.shape[1]}")
    print(f"Dosya: {out_path}")

if __name__ == "__main__":
    main()
