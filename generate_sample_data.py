"""
generate_sample_data.py — Creates a realistic sample_data.csv
Mimics the Kaggle Credit Card Fraud Detection dataset structure.
Columns: Time, V1-V28, Amount, Class
"""
import numpy as np
import pandas as pd
import os

np.random.seed(42)

N_LEGIT = 1900
N_FRAUD = 100
N_TOTAL = N_LEGIT + N_FRAUD

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT = os.path.join(DATA_DIR, "sample_data.csv")

# --- Time: seconds elapsed (0 to ~172800 = 2 days) ---
time_legit = np.sort(np.random.uniform(0, 172800, N_LEGIT))
time_fraud = np.random.uniform(0, 172800, N_FRAUD)

# --- V1-V28: PCA-transformed features ---
# Legitimate transactions: roughly standard normal
v_legit = np.random.randn(N_LEGIT, 28)
# Fraud transactions: shifted means to be separable
fraud_means = np.zeros(28)
fraud_means[0] = -3.5   # V1
fraud_means[1] = 2.8    # V2
fraud_means[2] = -4.2   # V3
fraud_means[3] = 3.0    # V4
fraud_means[4] = -2.0   # V5
fraud_means[6] = -3.5   # V7
fraud_means[9] = -4.0   # V10
fraud_means[10] = 3.5   # V11
fraud_means[11] = -5.0  # V12
fraud_means[13] = -5.5  # V14
fraud_means[15] = -4.0  # V16
fraud_means[16] = -4.5  # V17
v_fraud = np.random.randn(N_FRAUD, 28) * 1.2 + fraud_means

# --- Amount ---
amount_legit = np.abs(np.random.lognormal(mean=3.5, sigma=1.5, size=N_LEGIT))
amount_legit = np.clip(amount_legit, 0.01, 25000)
amount_fraud = np.abs(np.random.lognormal(mean=4.5, sigma=1.8, size=N_FRAUD))
amount_fraud = np.clip(amount_fraud, 1.0, 20000)

# --- Combine ---
times = np.concatenate([time_legit, time_fraud])
v_features = np.concatenate([v_legit, v_fraud], axis=0)
amounts = np.concatenate([amount_legit, amount_fraud])
classes = np.concatenate([np.zeros(N_LEGIT), np.ones(N_FRAUD)])

# Shuffle
idx = np.random.permutation(N_TOTAL)
times = times[idx]
v_features = v_features[idx]
amounts = amounts[idx]
classes = classes[idx]

# Build DataFrame
cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
data = np.column_stack([times, v_features, amounts, classes])
df = pd.DataFrame(data, columns=cols)

# Round for cleanliness
df["Time"] = df["Time"].round(1)
df["Amount"] = df["Amount"].round(2)
for c in [f"V{i}" for i in range(1, 29)]:
    df[c] = df[c].round(6)
df["Class"] = df["Class"].astype(int)

df.to_csv(OUTPUT, index=False)
print(f"Created {OUTPUT}")
print(f"  Rows: {len(df)} | Fraud: {int(df['Class'].sum())} | Legit: {int((df['Class']==0).sum())}")
print(f"  Fraud rate: {df['Class'].mean()*100:.2f}%")
