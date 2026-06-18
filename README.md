# 🥣 Food Demand & Supply Prediction Wizard Dashboard

An ML-powered inventory demand forecasting dashboard designed for food supply chains. This application provides a modern, clean, and interactive single-page step-by-step wizard workflow that guides users through importing datasets, training machine learning models, comparing performance evaluation metrics, and forecasting target orders.

---

## 🎨 Design & Aesthetic Style
* **Premium Theme**: Soft light background palette featuring slate-grey layouts (`#f8fafc` & `#ffffff`), deep indigo accents (`#4f46e5`), and emerald success signals.
* **Micro-Animations**: Features hover scaling on grid cards, loading skeletons, responsive overlays, and fade-in transitions.
* **Responsive Layout**: Designed with a fluid grid structure that adapts seamlessly across all devices:
  * **Large Screens**: Expanded full-sidebar steps tracker.
  * **Tablets (601px - 1024px)**: Space-saving icon-only vertical stepper.
  * **Mobile (<=600px)**: Floating horizontal top tab navigation bar with flex-wrapped block forms.

---

## 🧭 Step-by-Step Wizard Workflow

### 1️⃣ Step 1: Feed Data
* **Drag-and-Drop Dropzones**: Custom drag-and-drop cards to upload the required files:
  1. `train.csv` (Historical transaction data)
  2. `fulfilment_center_info.csv` (Details about fulfillment centers)
  3. `testData.csv` (Future periods to forecast)
* **⚡ Preloaded Sample Data**: Option to load default dataset instantly.
* **Explorer Toolbar**: Includes an interactive KPI dashboard and a searchable, paginated tabular view of the first 50 merged database records.

### 2️⃣ Step 2: Train Models
* **Algorithm Selection**: Check or uncheck 8 different algorithms to train:
  * *Classical ML*: Random Forest, Gradient Boosting, LightGBM, CatBoost, XGBoost.
  * *Deep Learning*: LSTM, Bi-LSTM, CNN (1D).
* **⚡ Quick Training Mode**: (Enabled by default) Automatically samples a subset of the dataset and runs limited epochs for Keras models, letting all models complete training in seconds. Disable to train on the full dataset.

### 3️⃣ Step 3: Compare Models
* **Metrics Leaderboard**: Compare trained models side-by-side on five metrics: **RMSLE**, **MSE**, **RMSE**, **MAE**, and **MAPE**. The best score for each metric is highlighted in a green pill.
* **RMSE Comparison Chart**: Interactive Chart.js bar graph displaying error metrics.

### 4️⃣ Step 4: Visuals & Forecasts
* **Fulfillment Distribution**: Generates doughnut, bar, and horizontal bar charts on-demand to display center type volumes, regional splits, and top 15 highest-volume centers.
* **Demand Forecasting Engine**: select any trained model checkpoint to predict future orders from `testData.csv`, displaying a searchable table and an interactive bar graph.

---

## 🛠️ Technology Stack
* **Backend**: Python 3.10+, Flask, Pandas, NumPy, Scikit-Learn, LightGBM, XGBoost, CatBoost, TensorFlow (Keras), H5py.
* **Frontend**: HTML5 (Semantic), CSS3 (Flexbox/Grid), JavaScript (ES6+), Chart.js (CDN).
* **Deployment/WSGI**: Gunicorn.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10 or 3.11 installed.

### Installation
1. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/food-demand-prediction-dashboard.git
   cd food-demand-prediction-dashboard
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: The `requirements.txt` locks working versions of NumPy and TensorFlow to prevent version mismatches).*

3. Start the Flask server:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   **[http://localhost:5000](http://localhost:5000)**

---

## 📂 Project Structure
```bash
├── Dataset/                   # Directory containing CSV datasets
│   ├── train.csv              # Historical transaction data
│   ├── fulfilment_center_info.csv # Center details data
│   └── testData.csv           # Forecast target data
├── model/                     # Trained deep learning weight files
├── static/
│   ├── css/
│   │   └── style.css          # Vanilla CSS layout styles & responsive queries
│   └── js/
│       └── app.js             # API communications, navigation, & Chart.js logic
├── templates/
│   └── index.html             # HTML5 wizard dashboard layout template
├── app.py                     # Flask backend controllers & training server
├── Procfile                   # Process file for cloud web deployments
├── .gitignore                 # Files excluded from git tracking
├── requirements.txt           # Main web application dependencies
├── requirements_notebook.txt  # Jupyter Notebook legacy dependencies
└── deployment_guide.md        # Detailed guide for pushing to GitHub & Render
```

---

## ☁️ Deployment

This repository is pre-configured with a **`Procfile`** and a production-grade **`requirements.txt`** for cloud deployments (like Render or Heroku):
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `gunicorn app:app`

See **[deployment_guide.md](file:///c:/Users/sahil/OneDrive/Desktop/food%20demand%20FRont%20end/24.%20Food%20Demand/24.%20Food%20Demand/FoodDemandSupply/FoodDemandSupply/deployment_guide.md)** for detailed instructions.
