"""Quick script to train all models from sample_data.csv"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from src.data_engine import run_full_pipeline
from src.model_trainer import train_all_models

print("Loading data...")
p = run_full_pipeline()
r = p["validation_report"]
print(f"Dataset: {r['total_rows']} rows | Fraud: {r['fraud_count']} ({r['fraud_percentage']}%)")
print(f"SMOTE Before: {p['before_smote']}")
print(f"SMOTE After:  {p['after_smote']}")

print("\nTraining models...")
results = train_all_models(
    p["X_train"], p["y_train"],
    p["X_test"], p["y_test"],
    p["feature_names"]
)

print(f"\n{'Model':<25} {'Acc':>7} {'F1':>7} {'AUC':>7}")
print("-" * 50)
for name, m in results.items():
    print(f"{name:<25} {m['accuracy']:>6.2f}% {m['f1_score']:>6.2f}% {m['auc_roc']:>6.2f}%")

best = max(results.keys(), key=lambda k: results[k]["f1_score"])
print(f"\nBest Model (F1): {best} ({results[best]['f1_score']}%)")
print("All .pkl files saved to models/")
