# SmartFraud: Enterprise Fraud Detection System

A complete, production-ready fraud detection dashboard built with Streamlit. This application uses Machine Learning (Random Forest, XGBoost, etc.) to detect fraudulent credit card transactions, featuring user authentication, exploratory data analysis, model training, and bulk prediction capabilities.

## Features

- **User Authentication:** Secure login and registration with bcrypt password hashing.
- **Role-Based Access Control:** Differentiated access for Admin and Analyst roles.
- **Exploratory Data Analysis (EDA):** Interactive dataset uploading and visualization of transaction distributions and imbalances.
- **Machine Learning Engine:** Train multiple models (Logistic Regression, Decision Tree, Random Forest, XGBoost) with SMOTE balancing.
- **Live Predictor:** Run predictions on single transactions or bulk batch processing via CSV upload.
- **Reporting & Logging:** Exportable activity logs, flagged transactions, and model performance metrics.
- **Bonsai UI:** Custom modern, green-accented aesthetic overriding default Streamlit styles.

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repository-url>
   cd FraudDetectionSystem
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Default Credentials

A default admin account is created automatically upon first run:
- **Username:** `admin`
- **Password:** `admin123`

## Dataset

This system is designed to process the [Kaggle Credit Card Fraud Detection Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud). Download the `creditcard.csv` file and upload it through the **Dataset** page in the application.

## Technologies Used
- **Frontend/Backend:** Python, Streamlit
- **Machine Learning:** scikit-learn, xgboost, imbalanced-learn
- **Visualizations:** Plotly
- **Database:** SQLite3
- **Security:** bcrypt

## License
MIT
