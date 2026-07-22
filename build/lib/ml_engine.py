import json
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, precision_score, recall_score
import numpy as np

class MLEngine:
    def __init__(self):
        self.models = {}
    
    def get_model(self, model_type):
        models = {
            "linear_regression": LinearRegression(),
            "logistic_regression": LogisticRegression(max_iter=1000),
            "decision_tree": DecisionTreeRegressor(),
            "decision_tree_classifier": DecisionTreeClassifier(),
            "random_forest": RandomForestRegressor(n_estimators=100),
            "random_forest_classifier": RandomForestClassifier(n_estimators=100),
        }
        return models.get(model_type, LinearRegression())
    
    def train(self, df, target_col, model_type, model_name, test_size=0.2):
        feature_cols = []
        for col in df.schema:
            if col != target_col:
                vals = [r.get(col) for r in df.rows]
                numeric_vals = []
                for v in vals:
                    try:
                        numeric_vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
                if len(numeric_vals) == len(vals):
                    feature_cols.append(col)
        
        if not feature_cols:
            self.models[model_name] = {
                "model": None,
                "feature_cols": [],
                "model_type": model_type,
                "metrics": {"error": "No numeric features found"}
            }
            return {
                "model_name": model_name,
                "features": [],
                "target": target_col,
                "model_type": model_type,
                "train_rows": len(df.rows),
                "test_rows": 0,
                "metrics": {"error": "Need numeric feature columns"}
            }
        
        X = np.array([[float(r.get(c, 0)) for c in feature_cols] for r in df.rows])
        y = np.array([float(r.get(target_col, 0)) for r in df.rows])
        
        if len(X) < 2:
            self.models[model_name] = {
                "model": None,
                "feature_cols": feature_cols,
                "model_type": model_type,
                "metrics": {"error": "Not enough data"}
            }
            return {
                "model_name": model_name,
                "features": feature_cols,
                "target": target_col,
                "model_type": model_type,
                "train_rows": len(X),
                "test_rows": 0,
                "metrics": {"error": "Need at least 2 rows"}
            }
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
        model = self.get_model(model_type)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        metrics = {}
        if model_type in ("logistic_regression", "decision_tree_classifier", "random_forest_classifier"):
            metrics["accuracy"] = float(accuracy_score(y_test, y_pred.round()))
        else:
            metrics["mse"] = float(mean_squared_error(y_test, y_pred))
            metrics["r2"] = float(r2_score(y_test, y_pred))
            metrics["rmse"] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        
        self.models[model_name] = {
            "model": model,
            "feature_cols": feature_cols,
            "model_type": model_type,
            "metrics": metrics
        }
        
        return {
            "model_name": model_name,
            "features": feature_cols,
            "target": target_col,
            "model_type": model_type,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "metrics": metrics
        }
    
    def predict(self, df, model_name, output_col="prediction"):
        if model_name not in self.models:
            return None, {"error": f"Model '{model_name}' not found"}
        
        model_info = self.models[model_name]
        
        if model_info["model"] is None:
            new_rows = [dict(row) for row in df.rows]
            for row in new_rows:
                row[output_col] = 0
            return new_rows, df.schema + [output_col]
        
        model = model_info["model"]
        feature_cols = model_info["feature_cols"]
        
        X = np.array([[float(r.get(c, 0)) for c in feature_cols] for r in df.rows])
        predictions = model.predict(X)
        
        new_rows = []
        for i, row in enumerate(df.rows):
            new_row = dict(row)
            new_row[output_col] = float(predictions[i])
            new_rows.append(new_row)
        
        return new_rows, df.schema + [output_col]