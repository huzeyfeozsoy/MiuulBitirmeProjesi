import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

def grab_col_names(dataframe, cat_th=10, car_th=20):
    cat_cols = [col for col in dataframe.columns if dataframe[col].dtypes == "O"]
    num_but_cat = [col for col in dataframe.columns if dataframe[col].nunique() < cat_th and dataframe[col].dtypes != "O"]
    cat_but_car = [col for col in dataframe.columns if dataframe[col].nunique() > car_th and dataframe[col].dtypes == "O"]
    cat_cols = cat_cols + num_but_cat
    cat_cols = [col for col in cat_cols if col not in cat_but_car]
    num_cols = [col for col in dataframe.columns if dataframe[col].dtypes != "O"]
    num_cols = [col for col in num_cols if col not in num_but_cat]
    return cat_cols, num_cols, cat_but_car

def main():
    print("="*60)
    print("EDA - Keşifçi Veri Analizi Başlıyor...")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'model_ready_data.csv') # 1. scriptin çıktısı üzerinden
    
    if not os.path.exists(data_path):
        print(f"HATA: {data_path} bulunamadı! Önce 1_merge_and_prepare_data.py çalıştırılmalı.")
        return

    df = pd.read_csv(data_path)
    
    # Görselleri kaydedeceğimiz klasör
    eda_out_dir = os.path.join(base_dir, 'EDA_Results')
    os.makedirs(eda_out_dir, exist_ok=True)
    
    print("\n[1] TEMEL BİLGİLER")
    print(f"Shape: {df.shape}")
    print("\n--- Info ---")
    df.info()
    print("\n--- Describe ---")
    print(df.describe().T)
    
    print("\n[2] DEĞİŞKENLERİN AYRILMASI (grab_col_names)")
    cat_cols, num_cols, cat_but_car = grab_col_names(df)
    print(f"Kategorik Değişkenler ({len(cat_cols)}): {cat_cols}")
    print(f"Sayısal Değişkenler ({len(num_cols)}): {num_cols}")
    print(f"Kardinal Değişkenler ({len(cat_but_car)}): {cat_but_car}")
    
    print("\n[3] GÖRSELLEŞTİRME: Hedef Değişken (Target) Dağılımı")
    if 'is_goal' in df.columns:
        plt.figure(figsize=(6,4))
        sns.countplot(x='is_goal', data=df)
        plt.title('Hedef Değişken (is_goal) Dağılımı')
        plt.savefig(os.path.join(eda_out_dir, '1_target_distribution.png'))
        plt.close()
    
    print("\n[4] GÖRSELLEŞTİRME: Kategorik Değişkenler (Countplot)")
    for col in cat_cols:
        # Çok fazla benzersiz değer varsa atla (görsel karmaşası olmasın)
        if df[col].nunique() <= 20:
            plt.figure(figsize=(8,4))
            sns.countplot(x=col, data=df, hue='is_goal' if 'is_goal' in df.columns else None)
            plt.title(f'{col} Dağılımı')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(eda_out_dir, f'2_cat_{col}_countplot.png'))
            plt.close()
            
    print("\n[5] GÖRSELLEŞTİRME: Sayısal Değişkenler (Histogram & Boxplot)")
    for col in num_cols:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        sns.histplot(df[col], bins=20, kde=True, ax=axes[0])
        axes[0].set_title(f'{col} - Histogram')
        sns.boxplot(x=df[col], ax=axes[1])
        axes[1].set_title(f'{col} - Boxplot')
        plt.tight_layout()
        plt.savefig(os.path.join(eda_out_dir, f'3_num_{col}_hist_box.png'))
        plt.close()
        
    print("\n[6] GÖRSELLEŞTİRME: Korelasyon Heatmap")
    plt.figure(figsize=(14,10))
    corr = df[num_cols].corr()
    sns.heatmap(corr, annot=False, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1)
    plt.title('Sayısal Değişkenler Korelasyon Isı Haritası')
    plt.tight_layout()
    plt.savefig(os.path.join(eda_out_dir, '4_correlation_heatmap.png'))
    plt.close()
    
    print("\n[7] GÖRSELLEŞTİRME: Missing Value (Eksik Değer) Heatmap")
    plt.figure(figsize=(10,6))
    sns.heatmap(df.isnull(), yticklabels=False, cbar=False, cmap='viridis')
    plt.title('Eksik Değerler (Sarı kısımlar eksik veriyi gösterir)')
    plt.tight_layout()
    plt.savefig(os.path.join(eda_out_dir, '5_missing_values_heatmap.png'))
    plt.close()
    
    print(f"\nİŞLEM TAMAMLANDI! Tüm görseller '{eda_out_dir}' klasörüne kaydedildi.")

if __name__ == "__main__":
    main()
