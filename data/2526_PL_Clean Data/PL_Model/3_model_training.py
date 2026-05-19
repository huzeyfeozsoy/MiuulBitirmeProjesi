################################################
# Contextual Shot Quality (xG) Machine Learning Pipeline
################################################

import os
import joblib
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import shap

from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split, cross_validate, GridSearchCV
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

warnings.simplefilter(action='ignore', category=Warning)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)

# CONSTANTS (Magic Numbers Sabitleri)
TEST_SIZE = 0.20
RANDOM_STATE = 42
CV_FOLDS = 5

def load_and_split_data(file_path):
    """
    Verisetini okur, bağımlı ve bağımsız değişkenleri ayırır,
    ve Train-Test split (Eğitim-Test ayrımı) işlemini gerçekleştirir.
    """
    df = pd.read_csv(file_path)
    
    y = df["is_goal"]
    X = df.drop(["is_goal"], axis=1)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    return X_train, X_test, y_train, y_test

def apply_scaling(X_train, X_test):
    """
    Sadece numerik kolonlara RobustScaler uygular.
    Data Leakage'i önlemek için fit() sadece train setine,
    transform() hem train hem test setine uygulanır.
    """
    # Sadece sayısal (bool/0-1 olmayan) değişkenleri seç
    num_cols = [col for col in X_train.columns if X_train[col].nunique() > 2]
    
    scaler = RobustScaler()
    X_train[num_cols] = scaler.fit_transform(X_train[num_cols])
    X_test[num_cols] = scaler.transform(X_test[num_cols])
    
    return X_train, X_test

def base_models(X_train, y_train):
    """
    Baseline model (Logistic Regression) ve 5 farklı Ağaç tabanlı modeli
    Cross Validation (cv=5) ile Accuracy, F1 ve ROC-AUC metrikleriyle karşılaştırır.
    """
    print("="*50)
    print("Model Karşılaştırması (Cross-Validation)")
    print("="*50)
    
    classifiers = [
        ('Baseline (LR)', LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
        ("Random Forest", RandomForestClassifier(random_state=RANDOM_STATE)),
        ('GBM', GradientBoostingClassifier(random_state=RANDOM_STATE)),
        ('XGBoost', XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=RANDOM_STATE)),
        ('LightGBM', LGBMClassifier(random_state=RANDOM_STATE, verbose=-1)),
        ('CatBoost', CatBoostClassifier(random_state=RANDOM_STATE, verbose=False))
    ]

    results_list = []
    
    for name, classifier in classifiers:
        cv_results = cross_validate(classifier, X_train, y_train, cv=CV_FOLDS, scoring=['roc_auc', 'f1', 'accuracy'])
        results_list.append({
            "Model": name,
            "Accuracy": round(cv_results['test_accuracy'].mean(), 4),
            "F1_Score": round(cv_results['test_f1'].mean(), 4),
            "ROC_AUC": round(cv_results['test_roc_auc'].mean(), 4)
        })
        
    results_df = pd.DataFrame(results_list).sort_values(by="ROC_AUC", ascending=False)
    print(results_df.to_string(index=False))
    print("\nModel karşılaştırma tablosu terminale basıldı (Sunum için kullanılabilir).")
    return results_df

def hyperparameter_optimization(X_train, y_train):
    """
    Seçilen modeller için GridSearchCV ile Hyperparameter Tuning yapar.
    En iyi parametrelerle modelleri tekrar eğitir.
    """
    print("="*50)
    print("Hyperparameter Tuning (GridSearch)")
    print("="*50)
    
    lightgbm_params = {
        "learning_rate": [0.01, 0.1],
        "n_estimators": [100, 300],
        "max_depth": [3, 5]
    }
    
    xgboost_params = {
        "learning_rate": [0.1, 0.01],
        "max_depth": [3, 5],
        "n_estimators": [100, 200]
    }

    classifiers_for_tuning = [
        ('XGBoost', XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=RANDOM_STATE), xgboost_params),
        ('LightGBM', LGBMClassifier(random_state=RANDOM_STATE, verbose=-1), lightgbm_params)
    ]
    
    best_models = {}
    for name, classifier, params in classifiers_for_tuning:
        print(f"Tuning {name}...")
        gs_best = GridSearchCV(classifier, params, cv=CV_FOLDS, n_jobs=-1, verbose=False, scoring='roc_auc').fit(X_train, y_train)
        final_model = classifier.set_params(**gs_best.best_params_)
        best_models[name] = final_model.fit(X_train, y_train)
        print(f"{name} Best Params: {gs_best.best_params_}")
        
    return best_models

def ensemble_and_evaluate(best_models, X_train, y_train, X_test, y_test):
    """
    Tuning edilmiş modellerden Voting Classifier oluşturur ve test seti üzerinde değerlendirir.
    """
    print("="*50)
    print("Ensemble (Voting) & Test Set Evaluation")
    print("="*50)
    
    voting_clf = VotingClassifier(
        estimators=[
            ('XGB', best_models["XGBoost"]),
            ('LGBM', best_models["LightGBM"])
        ],
        voting='soft'
    ).fit(X_train, y_train)
    
    # Test seti performansı
    y_pred = voting_clf.predict(X_test)
    y_prob = voting_clf.predict_proba(X_test)[:, 1]
    
    print("TEST SET SONUÇLARI:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred):.4f}")
    print(f"ROC AUC : {roc_auc_score(y_test, y_prob):.4f}")
    
    return voting_clf

def shap_explainability(model, X_train):
    """
    Modelin kararlarını SHAP (SHapley Additive exPlanations) grafiği ile görselleştirir.
    """
    print("="*50)
    print("SHAP Feature Importance Analysis...")
    print("="*50)
    
    # Tree tabanlı bir model gerektiği için LightGBM modelini kullanıyoruz
    explainer = shap.TreeExplainer(model)
    X_sample = shap.sample(X_train, 1000) 
    shap_values = explainer.shap_values(X_sample)
    
    if isinstance(shap_values, list):
        shap_values_to_plot = shap_values[1] 
    else:
        shap_values_to_plot = shap_values
        
    plt.figure()
    shap.summary_plot(shap_values_to_plot, X_sample, show=False)
    plt.title("SHAP Summary Plot (Feature Importance)")
    plt.tight_layout()
    plt.savefig('shap_summary.png')
    plt.close()
    print("SHAP grafiği 'shap_summary.png' olarak kaydedildi.")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'model_ready_data_preprocessed.csv')
    
    print("1. Data Loading and Splitting...")
    X_train, X_test, y_train, y_test = load_and_split_data(data_path)
    
    print("\n2. Standardization (RobustScaler)...")
    X_train, X_test = apply_scaling(X_train, X_test)
    
    print("\n3. Cross Validation Model Comparison...")
    base_models(X_train, y_train)
    
    print("\n4. Hyperparameter Tuning...")
    best_models = hyperparameter_optimization(X_train, y_train)
    
    print("\n5. Final Evaluation on Test Set...")
    voting_clf = ensemble_and_evaluate(best_models, X_train, y_train, X_test, y_test)
    
    print("\n6. SHAP Explainability...")
    shap_explainability(best_models["LightGBM"], X_train)
    
    print("\n7. Saving the Final Model...")
    # Modeli istenilen 'models' klasörüne kaydetme
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
    models_dir = os.path.join(project_root, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_save_path = os.path.join(models_dir, "xg_voting_clf.pkl")
    joblib.dump(voting_clf, model_save_path)
    
    # Data scaling transform için gerekecek scaler'ı ve feature'ları da app'te kullanmak için test setini kaydedebiliriz, ama model yeterli
    print(f"Voting Classifier başarıyla kaydedildi: {model_save_path}")
    print("="*50)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*50)

if __name__ == "__main__":
    main()
