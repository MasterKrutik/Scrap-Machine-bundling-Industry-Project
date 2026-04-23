import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from models.database import execute_query

def generate_dashboard_graphs():
    print("Fetching data from the database...")
    
    sensor_query = """
        SELECT s.Machine_ID as machine_id,
               ROUND(AVG(CASE WHEN s.Sensor_Type = 'Temperature' THEN sd.Value END), 1) AS avg_temp,
               ROUND(AVG(CASE WHEN s.Sensor_Type = 'Vibration' THEN sd.Value END), 1) AS avg_vib,
               ROUND(AVG(CASE WHEN s.Sensor_Type = 'Pressure' THEN sd.Value END), 1) AS avg_pressure,
               ROUND(AVG(CASE WHEN s.Sensor_Type = 'Motor Current' THEN sd.Value END), 1) AS avg_current,
               ROUND(AVG(CASE WHEN s.Sensor_Type = 'Oil Level' THEN sd.Value END), 1) AS avg_oil
        FROM sensor_data sd
        JOIN sensors s ON sd.Sensor_ID = s.Sensor_ID
        GROUP BY s.Machine_ID
    """
    sensor_data = execute_query(sensor_query)

    fault_query = """
        SELECT Machine_ID as machine_id, COUNT(*) AS high_faults
        FROM alerts
        GROUP BY Machine_ID
    """
    fault_data = execute_query(fault_query)
    fault_map = {f["machine_id"]: f["high_faults"] for f in fault_data}

    if len(sensor_data) < 2:
        print("Not enough data to generate graphs.")
        return

    X = []
    y = []
    for s in sensor_data:
        features = [
            float(s["avg_temp"] or 0),
            float(s["avg_vib"] or 0),
            float(s["avg_pressure"] or 0),
            float(s["avg_current"] or 0),
            float(s["avg_oil"] or 0)
        ]
        X.append(features)
        label = 1 if fault_map.get(s["machine_id"], 0) > 2 else 0
        y.append(label)

    X = np.array(X)
    y = np.array(y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(random_state=42)
    model.fit(X_scaled, y)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    public_dir = os.path.abspath(os.path.join(base_dir, '..', '..', 'frontend', 'public'))
    os.makedirs(public_dir, exist_ok=True)

    # List of our features to loop through
    features_list = ["temperature", "vibration", "pressure", "motor_current", "oil_level"]
    feature_display_names = ["Temperature", "Vibration", "Pressure", "Motor Current", "Oil Level"]

    # Loop through all 5 features and generate graphs for each
    for feature_index in range(5):
        feature_name = features_list[feature_index]
        display_name = feature_display_names[feature_index]
        print(f"Generating graphs for {display_name}...")

        # --- GRAPH 1: MLE Logistic Curve ---
        X_feature = X_scaled[:, feature_index]
        X_range = np.linspace(X_feature.min() - 1, X_feature.max() + 1, 300).reshape(-1, 1)
        
        # Fill other features with 0 (mean) to isolate this specific feature's curve
        X_mock = np.zeros((300, 5))
        X_mock[:, feature_index] = X_range.ravel()
        y_prob = model.predict_proba(X_mock)[:, 1]

        plt.figure(figsize=(8, 5))
        plt.scatter(X_feature, y, color='blue', label='Actual Data (0=Healthy, 1=Fail)', alpha=0.6, edgecolors='black')
        plt.plot(X_range, y_prob, color='red', linewidth=3, label='MLE Fitted Probability Curve')
        plt.title(f"MLE Curve Fitting vs. {display_name}")
        plt.xlabel(f"Standardized {display_name}")
        plt.ylabel("Probability of Failure")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(os.path.join(public_dir, f'mle_curve_{feature_name}.png'), bbox_inches='tight', dpi=150)
        plt.close()

        # --- GRAPH 2: Distributions ---
        plt.figure(figsize=(8, 5))
        has_healthy = len(X_scaled[y == 0]) > 0
        has_failing = len(X_scaled[y == 1]) > 0

        if has_healthy:
            sns.kdeplot(X_scaled[y == 0][:, feature_index], label="Healthy Machines", fill=True, color="green", alpha=0.5)
        if has_failing:
            sns.kdeplot(X_scaled[y == 1][:, feature_index], label="Failing Machines", fill=True, color="red", alpha=0.5)

        plt.title(f"Sample Distribution: {display_name}")
        plt.xlabel(f"Standardized {display_name}")
        plt.ylabel("Density")
        if has_healthy or has_failing:
            plt.legend()
        
        plt.savefig(os.path.join(public_dir, f'distribution_{feature_name}.png'), bbox_inches='tight', dpi=150)
        plt.close()
    # ... (Keep all your previous loop code above this) ...

        # 🌟 NEW MULTIVARIATE GRAPHS 🌟

        # --- GRAPH 3: Feature Weights (Coefficients) ---
        print("Generating Feature Weights chart...")
        plt.figure(figsize=(8, 5))
        # model.coef_[0] contains the actual mathematical weights
        weights = model.coef_[0] 
        
        # Sort features by their absolute weight for a cleaner graph
        sorted_indices = np.argsort(np.abs(weights))
        sorted_weights = weights[sorted_indices]
        sorted_names = [feature_display_names[i] for i in sorted_indices]
        
        colors = ['red' if w < 0 else 'green' for w in sorted_weights]
        
        plt.barh(sorted_names, sorted_weights, color=colors, edgecolor='black', alpha=0.7)
        plt.title("Logistic Regression Weights (Feature Importance)")
        plt.xlabel("Impact on Failure Probability (Negative = Drops cause failure)")
        plt.grid(True, axis='x', alpha=0.3)
        plt.axvline(x=0, color='black', linestyle='--')
        
        plt.savefig(os.path.join(public_dir, 'feature_weights.png'), bbox_inches='tight', dpi=150)
        plt.close()

        # --- GRAPH 4: 2D Decision Boundary (Top 2 Features) ---
        print("Generating 2D Contour Decision Boundary...")
        # Let's use Vibration (index 1) and Motor Current (index 3)
        vib_idx, curr_idx = 1, 3
        
        # Create a grid of values covering the range of both features
        x_min, x_max = X_scaled[:, vib_idx].min() - 1, X_scaled[:, vib_idx].max() + 1
        y_min, y_max = X_scaled[:, curr_idx].min() - 1, X_scaled[:, curr_idx].max() + 1
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 100), np.linspace(y_min, y_max, 100))
        
        # We need a 5-column array to feed to predict_proba. 
        # We fill Vibration and Current with our grid, and the rest with 0 (average)
        grid_features = np.zeros((xx.ravel().shape[0], 5))
        grid_features[:, vib_idx] = xx.ravel()
        grid_features[:, curr_idx] = yy.ravel()
        
        # Predict the probability for every point on the grid
        Z = model.predict_proba(grid_features)[:, 1]
        Z = Z.reshape(xx.shape)
        
        plt.figure(figsize=(8, 6))
        # Draw the contour background (Red = Fail, Blue = Safe)
        contour = plt.contourf(xx, yy, Z, alpha=0.4, cmap='coolwarm', levels=10)
        plt.colorbar(contour, label="Probability of Failure")
        
        # Plot the actual machine data points on top
        plt.scatter(X_scaled[y==0, vib_idx], X_scaled[y==0, curr_idx], color='blue', label='Healthy', edgecolors='k', alpha=0.8)
        plt.scatter(X_scaled[y==1, vib_idx], X_scaled[y==1, curr_idx], color='red', label='Failing', edgecolors='k', alpha=0.8)
        
        plt.title("Decision Boundary: Vibration vs. Motor Current")
        plt.xlabel("Standardized Vibration")
        plt.ylabel("Standardized Motor Current")
        plt.legend()
        
        plt.savefig(os.path.join(public_dir, 'decision_boundary.png'), bbox_inches='tight', dpi=150)
        plt.close()    
    print(f"Success! 10 Graphs saved directly to: {public_dir}")

if __name__ == "__main__":
    generate_dashboard_graphs()