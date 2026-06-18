# Food Demand Prediction Dashboard – Deployment Guide

This guide describes how to push your project to GitHub and deploy it to a production server (such as Render or Hugging Face Spaces).

---

## 🛠️ Step 1: Initialize Git and Push to GitHub

1. **Open your Terminal/PowerShell** in the project directory:
   `c:\Users\sahil\OneDrive\Desktop\food demand FRont end\24. Food Demand\24. Food Demand\FoodDemandSupply\FoodDemandSupply`

2. **Initialize the local Git repository**:
   ```bash
   git init
   ```

3. **Verify the files to be tracked**:
   Run `git status` to see what files are staged. The `.gitignore` file we added will automatically exclude temporary caches (`__pycache__/`), virtual environments, and temporary files.

4. **Stage and commit your files**:
   ```bash
   git add .
   git commit -m "Initial commit: Responsive ML Food Demand & Supply dashboard"
   ```

5. **Create a new repository on GitHub**:
   - Go to [github.com](https://github.com) and click **New Repository**.
   - Set the name (e.g., `food-demand-prediction-dashboard`).
   - Do **NOT** initialize with a README, `.gitignore`, or license (since we already have them).
   - Click **Create repository**.

6. **Link your local repository and push**:
   Copy the commands from GitHub's instruction page under *"or push an existing repository from the command line"*:
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
   git push -u origin main
   ```

---

## 🚀 Step 2: Deploying to Production

Here are the two best free/low-cost platforms for deploying this Python ML Flask application:

### Option A: Deploy on Render (Recommended & Easiest)
Render is a cloud hosting provider that easily pulls code from GitHub and deploys it automatically.

1. Create a free account on [Render](https://render.com).
2. Click **New** (top-right) and select **Web Service**.
3. Connect your GitHub account and select your repository (`food-demand-prediction-dashboard`).
4. Set the following configuration settings:
   - **Name**: `food-demand-prediction` (or any name you prefer)
   - **Environment**: `Python3`
   - **Region**: Select the region closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app` (Render automatically detects this from your `Procfile`)
5. Click **Deploy Web Service**. Render will build the environment, install the dependencies, and deploy your site to a public URL (e.g., `https://food-demand-prediction.onrender.com`).

---

### Option B: Deploy on Hugging Face Spaces (Great for ML/Data apps)
Hugging Face Spaces is a popular hosting service for machine learning models and web apps.

1. Go to [Hugging Face](https://huggingface.co) and create an account.
2. Click your profile icon and select **New Space**.
3. Configure the Space settings:
   - **Space Name**: `food-demand-prediction`
   - **SDK**: Select **Docker** (or **Gradio/Streamlit**, but since this is a custom Flask app, **Docker** is the cleanest way).
4. Since we are using Docker, you can create a simple `Dockerfile` in the root of your project:
   ```dockerfile
   FROM python:3.10-slim
   WORKDIR /app
   COPY . /app
   RUN pip install -r requirements.txt
   EXPOSE 7860
   CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
   ```
5. Commit and push the `Dockerfile` to your Space repo, and Hugging Face will build and run the Flask application container automatically!

---

## 📂 Configuration Files Included

We have created the following files to ensure smooth production deployment:
* [requirements.txt](file:///c:/Users/sahil/OneDrive/Desktop/food%20demand%20FRont%20end/24.%20Food%20Demand/24.%20Food%20Demand/FoodDemandSupply/FoodDemandSupply/requirements.txt): Declares production web packages with explicit locked versions for `numpy` and `tensorflow` to avoid library conflicts.
* [Procfile](file:///c:/Users/sahil/OneDrive/Desktop/food%20demand%20FRont%20end/24.%20Food%20Demand/24.%20Food%20Demand/FoodDemandSupply/FoodDemandSupply/Procfile): Tells hosting providers how to run the web server in production (`gunicorn app:app`).
* [.gitignore](file:///c:/Users/sahil/OneDrive/Desktop/food%20demand%20FRont%20end/24.%20Food%20Demand/24.%20Food%20Demand/FoodDemandSupply/FoodDemandSupply/.gitignore): Excludes build folders, virtual environments, and python caches so they do not bloat your GitHub repository.
