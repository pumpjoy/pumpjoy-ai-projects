# train_model.py
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle
import os


current_dir = os.getcwd()
MODEL_FILE = './app/isolation_forest_model.pkl'
FEATURES = ["amount", "txn_count_5min", "avg_amount_10min"]

# 1. Create Dummy Data
# Normal transactions (most data points)
rng = np.random.RandomState(42)
X_normal = 0.5 * rng.randn(100, 3) + np.array([50, 5, 500]) 

# Anomalous transactions (outliers)
X_outliers = rng.uniform(low=0, high=1000, size=(20, 3)) 

# Combine and create DataFrame
X = np.r_[X_normal, X_outliers]
df = pd.DataFrame(X, columns=FEATURES)

# 2. Train the Isolation Forest Model
# fit() is enough for Isolation Forest as it is unsupervised
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(df)

# 3. Save the Trained Model using pickle.dump
# Ensure the directory exists
os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True) 

with open(MODEL_FILE, 'wb') as f:
    pickle.dump(model, f)

# 4. Verification Check
file_size = os.path.getsize(MODEL_FILE)
print(f"Model saved successfully to {MODEL_FILE}")
print(f"Model file size: {file_size} bytes")