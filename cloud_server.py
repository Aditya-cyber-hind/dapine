from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import csv
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

PIPELINES_DIR = "cloud_data/pipelines"
UPLOADS_DIR = "cloud_data/uploads"

for d in [PIPELINES_DIR, UPLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

@app.route('/')
def home():
    return jsonify({
        "name": "Dapine Cloud API",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/upload - Upload CSV/Excel file",
            "POST /api/run - Run Dapine pipeline",
            "GET /api/pipelines - List saved pipelines",
        ]
    })

@app.route('/dashboard')
def dashboard():
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloud_dashboard.html')
    return send_file(dashboard_path)

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    filename = file.filename
    filepath = os.path.join(UPLOADS_DIR, filename)
    file.save(filepath)
    
    rows = []
    if filename.endswith('.csv'):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = [dict(row) for row in reader]
    
    return jsonify({
        "filename": filename,
        "rows": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "preview": rows[:5]
    })

@app.route('/api/run', methods=['POST'])
def run_pipeline():
    data = request.json
    code = data.get('code', '')
    filename = data.get('filename', '')
    
    if not code or not filename:
        return jsonify({"error": "Code and filename required"}), 400
    
    # Use the uploaded file path
    uploaded_path = os.path.join(UPLOADS_DIR, filename)
    
    # Replace the filename in code with the full path
    code = code.replace(f'"{filename}"', f'"{uploaded_path}"')
    code = code.replace(f"'{filename}'", f"'{uploaded_path}'")
    
    # Wrap in pipeline if needed
    if not code.strip().startswith('pipeline'):
        code = f'pipeline _cloud_run() {{\n{code}\n}}'
    
    pipeline_id = str(uuid.uuid4())[:8]
    pipeline_file = os.path.join(PIPELINES_DIR, f"{pipeline_id}.dap")
    with open(pipeline_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    import subprocess
    result = subprocess.run(
        ['python', 'dapine.py', pipeline_file],
        capture_output=True, text=True, timeout=30
    )
    
    return jsonify({
        "pipeline_id": pipeline_id,
        "status": "completed",
        "stdout": result.stdout[-1000:],
        "stderr": result.stderr[:300],
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌍 Dapine Cloud starting on port {port}")
    app.run(host='0.0.0.0', port=port)