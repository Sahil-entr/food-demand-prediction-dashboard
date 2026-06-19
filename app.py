"""
Food Demand & Supply Prediction – Flask Backend
=================================================
Wraps the Jupyter notebook ML pipeline into REST API endpoints.
"""

import os
import json
import traceback
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn import metrics

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "Dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model")

# Ensure required directories exist
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

_cache = {
    "dataset": None,
    "center": None,
    "merged": None,
    "X_train": None, "X_test": None,
    "y_train": None, "y_test": None,
    "sc1": None, "sc2": None,
    "le": None,
    "trained_models": {},
    "metrics_results": {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_data(force=False):
    """Load and merge the two CSV datasets, encode & scale."""
    if _cache["merged"] is not None and not force:
        return _cache["merged"]

    train_path = os.path.join(DATASET_DIR, "train.csv")
    center_path = os.path.join(DATASET_DIR, "fulfilment_center_info.csv")

    with open(train_path, 'rb') as f_train:
        dataset = pd.read_csv(f_train)
    dataset.fillna(0, inplace=True)

    with open(center_path, 'rb') as f_center:
        center = pd.read_csv(f_center)
    center.fillna(0, inplace=True)

    merged = dataset.merge(center, left_on="center_id", right_on="center_id", how="left")

    _cache["dataset"] = dataset
    _cache["center"] = center
    _cache["merged"] = merged
    return merged


def _prepare_train_test(force=False, quick_mode=False):
    """Encode, scale, split into train/test."""
    if _cache["X_train"] is not None and not force:
        return

    merged = _load_data(force)

    # Label-encode center_type
    le = LabelEncoder()
    merged["center_type"] = le.fit_transform(merged["center_type"].astype(str))
    _cache["le"] = le

    # Sample subset of dataset if in quick training mode
    if quick_mode and len(merged) > 20000:
        merged = merged.sample(n=20000, random_state=42).reset_index(drop=True)

    # Features & label
    features = merged.drop(["num_orders"], axis=1).values
    labels = merged["num_orders"].values.reshape(-1, 1)

    # Scale
    sc1 = MinMaxScaler()
    features = sc1.fit_transform(features)
    sc2 = MinMaxScaler()
    labels = sc2.fit_transform(labels)

    _cache["sc1"] = sc1
    _cache["sc2"] = sc2

    X_train, X_test, y_train, y_test = train_test_split(
        features, labels.ravel(), test_size=0.2, random_state=42
    )
    _cache["X_train"] = X_train
    _cache["X_test"] = X_test
    _cache["y_train"] = y_train
    _cache["y_test"] = y_test


def _calculate_metrics(algorithm, predict_raw, test_labels_raw):
    """Compute RMSLE, MSE, RMSE, MAE, MAPE and store."""
    predict_vals = predict_raw.reshape(-1, 1)
    predict_vals = _cache["sc2"].inverse_transform(predict_vals).ravel()
    test_vals = test_labels_raw.reshape(-1, 1)
    test_vals = _cache["sc2"].inverse_transform(test_vals).ravel()

    # Clip negatives for log-based metrics
    predict_vals = np.abs(predict_vals)
    test_vals = np.abs(test_vals)

    rmsle = float(np.sqrt(metrics.mean_squared_log_error(
        test_vals[:min(len(test_vals), 1000)],
        predict_vals[:min(len(predict_vals), 1000)]
    )))
    mse = float(mean_squared_error(test_vals, predict_vals))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(test_vals, predict_vals))
    mape = float(round(mean_absolute_percentage_error(
        test_vals[:30], predict_vals[:30]
    ), 3))

    result = {
        "algorithm": algorithm,
        "RMSLE": round(rmsle, 4),
        "MSE": round(mse, 2),
        "RMSE": round(rmse, 2),
        "MAE": round(mae, 2),
        "MAPE": round(mape, 4),
    }
    _cache["metrics_results"][algorithm] = result
    return result


# ---------------------------------------------------------------------------
# Routes – Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Routes – Dataset APIs
# ---------------------------------------------------------------------------

@app.route("/api/dataset/info")
def dataset_info():
    try:
        merged = _load_data()
        total_rows = len(merged)
        columns = list(merged.columns)
        
        # Verify required columns are present in the merged dataset
        required = ["num_orders", "center_id", "meal_id", "week"]
        missing = [col for col in required if col not in columns]
        if missing:
            raise KeyError(f"Missing required columns in dataset: {', '.join(missing)}")

        sample = merged.head(50).to_dict(orient="records")
        stats = {
            "total_orders": int(merged["num_orders"].sum()),
            "total_rows": total_rows,
            "unique_centers": int(merged["center_id"].nunique()),
            "unique_meals": int(merged["meal_id"].nunique()),
            "weeks": int(merged["week"].nunique()),
            "columns": columns,
        }
        return jsonify({"status": "ok", "stats": stats, "sample": sample})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Data Verification Failed: {str(e)}"}), 500


@app.route("/api/dataset/upload", methods=["POST"])
def dataset_upload():
    try:
        f = request.files.get("file")
        file_type = request.form.get("type", "train") # 'train', 'center', or 'test'
        if f is None:
            return jsonify({"status": "error", "message": "No file provided"}), 400
        
        # Mapping file types to standard expected names
        if file_type == "train":
            fname = "train.csv"
        elif file_type == "center":
            fname = "fulfilment_center_info.csv"
        elif file_type == "test":
            fname = "testData.csv"
        else:
            fname = f.filename

        dest = os.path.join(DATASET_DIR, fname)
        
        # Ensure directories exist
        os.makedirs(DATASET_DIR, exist_ok=True)
        
        # Validate file content in-memory first
        try:
            # Seek to start
            f.seek(0)
            # Read CSV in memory using pandas
            uploaded_df = pd.read_csv(f)
            
            # Reset seek position so we can write it later
            f.seek(0)

            # Perform validation based on file_type
            if file_type == "train":
                center_path = os.path.join(DATASET_DIR, "fulfilment_center_info.csv")
                if os.path.exists(center_path):
                    with open(center_path, 'rb') as f_center:
                        center = pd.read_csv(f_center)
                    # Verify they can be merged on center_id
                    merged = uploaded_df.merge(center, on="center_id", how="left")
                else:
                    merged = uploaded_df
                
                required = ["num_orders", "center_id", "meal_id", "week"]
                missing = [col for col in required if col not in merged.columns]
                if missing:
                    raise KeyError(f"Missing required columns in train dataset: {', '.join(missing)}")

            elif file_type == "center":
                train_path = os.path.join(DATASET_DIR, "train.csv")
                if os.path.exists(train_path):
                    with open(train_path, 'rb') as f_train:
                        dataset = pd.read_csv(f_train)
                    # Verify they can be merged on center_id
                    merged = dataset.merge(uploaded_df, on="center_id", how="left")
                else:
                    merged = uploaded_df
                
                # Check for center columns
                required_center = ["center_id", "center_type", "city_code", "region_code"]
                missing_center = [col for col in required_center if col not in uploaded_df.columns]
                if missing_center:
                    raise KeyError(f"Missing required columns in center dataset: {', '.join(missing_center)}")

            elif file_type == "test":
                required_test = ["center_id", "meal_id", "week"]
                missing_test = [col for col in required_test if col not in uploaded_df.columns]
                if missing_test:
                    raise KeyError(f"Missing required columns in test dataset: {', '.join(missing_test)}")

        except Exception as verify_err:
            raise Exception(f"Uploaded CSV format mismatch: {str(verify_err)}")

        # Verification succeeded! Save the file to dest using a retry loop to prevent WinError 32
        import time
        max_attempts = 10
        write_error = None

        for attempt in range(max_attempts):
            try:
                # Write to the destination file
                f.seek(0)
                with open(dest, "wb") as out_f:
                    while True:
                        chunk = f.read(1024 * 1024) # 1MB chunks
                        if not chunk:
                            break
                        out_f.write(chunk)
                write_error = None
                break
            except (PermissionError, OSError) as e:
                write_error = e
                time.sleep(0.2)

        if write_error is not None:
            raise Exception(f"Could not save file to disk (file is locked or in use by another process): {str(write_error)}")

        # Clear global state cache so everything reloads with the new data
        _cache["dataset"] = None
        _cache["center"] = None
        _cache["merged"] = None
        _cache["X_train"] = None
        _cache["X_test"] = None
        _cache["y_train"] = None
        _cache["y_test"] = None
        _cache["sc1"] = None
        _cache["sc2"] = None
        _cache["le"] = None
        _cache["trained_models"] = {}
        _cache["metrics_results"] = {}

        # Pre-load data to verify it is valid CSV
        _load_data(force=True)

        return jsonify({"status": "ok", "message": f"Successfully uploaded and processed {fname}!"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Routes – Charts APIs
# ---------------------------------------------------------------------------

@app.route("/api/charts/center-type-orders")
def chart_center_type():
    try:
        merged = _load_data()
        grouped = merged.groupby("center_type")["num_orders"].sum()
        return jsonify({
            "status": "ok",
            "labels": list(grouped.index),
            "values": [int(v) for v in grouped.values],
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/charts/region-orders")
def chart_region():
    try:
        merged = _load_data()
        grouped = merged.groupby("region_code")["num_orders"].sum().sort_values(ascending=False)
        return jsonify({
            "status": "ok",
            "labels": [str(l) for l in grouped.index],
            "values": [int(v) for v in grouped.values],
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/charts/top-centers")
def chart_top_centers():
    try:
        merged = _load_data()
        grouped = merged.groupby("center_id")["num_orders"].sum().nlargest(15)
        return jsonify({
            "status": "ok",
            "labels": [str(l) for l in grouped.index],
            "values": [int(v) for v in grouped.values],
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Routes – Train API
# ---------------------------------------------------------------------------

@app.route("/api/train", methods=["POST"])
def train_models():
    try:
        body = request.get_json(force=True)
        algorithms = body.get("algorithms", [])
        quick_mode = body.get("quick_mode", False)
        if not algorithms:
            algorithms = ["Random Forest", "Gradient Boosting", "LightGBM",
                          "CatBoost", "XGBoost", "LSTM", "Bi-LSTM", "CNN"]

        _prepare_train_test(force=True, quick_mode=quick_mode)
        X_train = _cache["X_train"]
        X_test = _cache["X_test"]
        y_train = _cache["y_train"]
        y_test = _cache["y_test"]

        results = []

        # In quick mode use fewer estimators to prevent gunicorn worker timeout
        n_est = 50 if quick_mode else 100

        for algo in algorithms:
            try:
                print(f"  [Training] Starting: {algo} (quick={quick_mode})", flush=True)

                if algo == "Random Forest":
                    from sklearn.ensemble import RandomForestRegressor
                    model = RandomForestRegressor(
                        n_estimators=n_est, random_state=42, n_jobs=-1
                    )
                    model.fit(X_train, y_train)
                    pred = model.predict(X_test)
                    _cache["trained_models"][algo] = model
                    results.append(_calculate_metrics(algo, pred, y_test))

                elif algo == "Gradient Boosting":
                    from sklearn.ensemble import GradientBoostingRegressor
                    model = GradientBoostingRegressor(
                        n_estimators=n_est, random_state=42
                    )
                    model.fit(X_train, y_train)
                    pred = model.predict(X_test)
                    _cache["trained_models"][algo] = model
                    results.append(_calculate_metrics(algo, pred, y_test))

                elif algo == "LightGBM":
                    import lightgbm as lgb
                    model = lgb.LGBMRegressor(
                        n_estimators=n_est, random_state=42, verbose=-1, n_jobs=-1
                    )
                    model.fit(X_train, y_train)
                    pred = model.predict(X_test)
                    _cache["trained_models"][algo] = model
                    results.append(_calculate_metrics(algo, pred, y_test))

                elif algo == "CatBoost":
                    import catboost as cb
                    model = cb.CatBoostRegressor(
                        iterations=n_est, random_seed=42, verbose=0, thread_count=-1
                    )
                    model.fit(X_train, y_train)
                    pred = model.predict(X_test)
                    _cache["trained_models"][algo] = model
                    results.append(_calculate_metrics(algo, pred, y_test))

                elif algo == "XGBoost":
                    import xgboost as xg
                    model = xg.XGBRegressor(
                        n_estimators=n_est, random_state=42, verbosity=0, nthread=-1
                    )
                    model.fit(X_train, y_train)
                    pred = model.predict(X_test)
                    _cache["trained_models"][algo] = model
                    results.append(_calculate_metrics(algo, pred, y_test))

                elif algo in ("LSTM", "Bi-LSTM", "CNN"):
                    result = _train_keras_model(algo, X_train, X_test, y_train, y_test, quick_mode)
                    results.append(result)

                print(f"  [Training] Done: {algo}", flush=True)

            except Exception as inner_e:
                traceback.print_exc()
                results.append({
                    "algorithm": algo,
                    "error": str(inner_e),
                })

        return jsonify({"status": "ok", "results": results})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


def _train_keras_model(algo, X_train, X_test, y_train, y_test, quick_mode=False):
    """Build & train a Keras model (LSTM / Bi-LSTM / CNN)."""
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM, Dropout, Flatten, Bidirectional
    from tensorflow.keras.layers import Conv1D, MaxPooling1D
    from tensorflow.keras.callbacks import ModelCheckpoint

    n_features = X_train.shape[1]

    # Reshape for sequence models
    X_train_seq = X_train.reshape(X_train.shape[0], 1, n_features)
    X_test_seq = X_test.reshape(X_test.shape[0], 1, n_features)

    if algo == "LSTM":
        model = Sequential([
            LSTM(128, input_shape=(1, n_features), return_sequences=True),
            Dropout(0.2),
            LSTM(64),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1),
        ])
        weight_file = os.path.join(MODEL_DIR, "lstm_weights.hdf5")

    elif algo == "Bi-LSTM":
        model = Sequential([
            Bidirectional(LSTM(128, return_sequences=True), input_shape=(1, n_features)),
            Dropout(0.2),
            Bidirectional(LSTM(64)),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1),
        ])
        weight_file = os.path.join(MODEL_DIR, "bilstm_weights.hdf5")

    elif algo == "CNN":
        model = Sequential([
            Conv1D(filters=64, kernel_size=1, activation='relu', input_shape=(1, n_features)),
            MaxPooling1D(pool_size=1),
            Flatten(),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(1),
        ])
        weight_file = os.path.join(MODEL_DIR, "cnn_weights.hdf5")

    model.compile(optimizer='adam', loss='mse')

    # Try loading pre-trained weights; if fail or quick mode, train fresh
    try:
        if quick_mode:
            raise Exception("Force quick mode training")
        model.load_weights(weight_file)
    except Exception:
        checkpoint = ModelCheckpoint(weight_file, monitor='loss', save_best_only=True, save_weights_only=True)
        epochs = 2 if quick_mode else 10
        model.fit(X_train_seq, y_train, epochs=epochs, batch_size=64,
                  validation_split=0.1, callbacks=[checkpoint], verbose=0)

    _cache["trained_models"][algo] = model

    pred = model.predict(X_test_seq, verbose=0).ravel()
    result = _calculate_metrics(algo, pred, y_test)
    return result


# ---------------------------------------------------------------------------
# Routes – Predict API
# ---------------------------------------------------------------------------

@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        body = request.get_json(force=True)
        algorithm = body.get("algorithm", "Random Forest")
        use_test_file = body.get("use_test_file", True)

        _prepare_train_test()

        if use_test_file:
            test_path = os.path.join(DATASET_DIR, "testData.csv")
            with open(test_path, 'rb') as f_test:
                test_df = pd.read_csv(f_test)
            test_df.fillna(0, inplace=True)

            # We need to add center info columns if not present
            center = _cache["center"]
            if "city_code" not in test_df.columns:
                test_df = test_df.merge(center, on="center_id", how="left")
                test_df.fillna(0, inplace=True)

            # Encode center_type
            le = _cache["le"]
            test_df["center_type"] = test_df["center_type"].apply(
                lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else 0
            )

            features = test_df.values
            sc1 = _cache["sc1"]
            features_scaled = sc1.transform(features)
        else:
            # Use manual input from body
            input_data = body.get("input_data", [])
            features_scaled = _cache["sc1"].transform(np.array(input_data))

        model = _cache["trained_models"].get(algorithm)
        if model is None:
            return jsonify({"status": "error",
                            "message": f"Model '{algorithm}' not trained yet. Train it first."}), 400

        # Keras models need reshape
        if algorithm in ("LSTM", "Bi-LSTM", "CNN"):
            features_input = features_scaled.reshape(features_scaled.shape[0], 1, features_scaled.shape[1])
            pred_scaled = model.predict(features_input, verbose=0).ravel()
        else:
            pred_scaled = model.predict(features_scaled)

        # Inverse-transform predictions
        pred_vals = _cache["sc2"].inverse_transform(pred_scaled.reshape(-1, 1)).ravel()

        predictions = []
        if use_test_file:
            test_path_raw = os.path.join(DATASET_DIR, "testData.csv")
            with open(test_path_raw, 'rb') as f_test_raw:
                raw_test = pd.read_csv(f_test_raw)
            for i, row in raw_test.iterrows():
                predictions.append({
                    "index": i,
                    "input": row.to_dict(),
                    "predicted_orders": round(float(np.abs(pred_vals[i])), 2),
                })
        else:
            for i, val in enumerate(pred_vals):
                predictions.append({
                    "index": i,
                    "predicted_orders": round(float(np.abs(val)), 2),
                })

        return jsonify({"status": "ok", "algorithm": algorithm, "predictions": predictions})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Routes – Metrics summary
# ---------------------------------------------------------------------------

@app.route("/api/metrics")
def get_metrics():
    return jsonify({
        "status": "ok",
        "results": list(_cache["metrics_results"].values()),
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(">> Starting Food Demand Prediction Server...")
    print("   Open http://localhost:5000 in your browser")
    app.run(debug=True, use_reloader=False, port=5000)
