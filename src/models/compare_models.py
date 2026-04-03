import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score


def get_suspicion_score(prob):
    return round(prob * 100, 2)


def load_data():
    df = pd.read_csv("data/processed/final_ml_dataset.csv")

    X = df.drop(columns=['fraud_label']).values
    y = df['fraud_label'].values

    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def evaluate_xgb(X_test, y_test):
    model = joblib.load("models/xgboost/xgb_model.pkl")

    y_prob = model.predict_proba(X_test)[:, 1]

    threshold = 0.25
    y_pred = (y_prob > threshold).astype(int)

    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "probs": y_prob
    }


def compare_models():
    print("🚀 Evaluating XGBoost Model...\n")

    X_train, X_test, y_train, y_test = load_data()

    xgb_results = evaluate_xgb(X_test, y_test)

    print("📊 XGBoost Performance:")
    print(xgb_results)

    print("\n🔍 Sample Predictions (First 5):")
    for i in range(5):
        print(f"\nSample {i+1}:")
        print(f"Suspicion Score: {get_suspicion_score(xgb_results['probs'][i])}")


if __name__ == "__main__":
    compare_models()