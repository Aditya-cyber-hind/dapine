from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import csv
import io
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Storage
PIPELINES_DIR = "cloud_data/pipelines"
UPLOADS_DIR = "cloud_data/uploads"
RESULTS_DIR = "cloud_data/results"

for d in [PIPELINES_DIR, UPLOADS_DIR, RESULTS_DIR]:
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
            "GET /api/results/<id> - Get pipeline results",
        ]
    })

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    filename = file.filename
    
    filepath = os.path.join(UPLOADS_DIR, filename)
    file.save(filepath)
    
    # Read and return preview
    rows = []
    if filename.endswith('.csv'):
        with open(filepath, 'r') as f:
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
    
    # Save pipeline
    pipeline_id = str(uuid.uuid4())[:8]
    pipeline_file = os.path.join(PIPELINES_DIR, f"{pipeline_id}.dap")
    with open(pipeline_file, 'w') as f:
        f.write(code)
    
    # Execute via Dapine
    import subprocess
    result = subprocess.run(
        ['python', 'dapine.py', pipeline_file],
        capture_output=True, text=True, timeout=30
    )
    
    # Collect output files
    outputs = []
    for f in os.listdir('.'):
        if f.endswith(('.json', '.csv', '.html', '.md', '.xlsx')) and os.path.getmtime(f) > os.path.getmtime(pipeline_file) - 5:
            outputs.append(f)
    
    return jsonify({
        "pipeline_id": pipeline_id,
        "status": "completed",
        "stdout": result.stdout[-500:],
        "stderr": result.stderr[:200],
        "outputs": outputs
    })

@app.route('/api/pipelines', methods=['GET'])
def list_pipelines():
    pipelines = []
    for f in os.listdir(PIPELINES_DIR):
        if f.endswith('.dap'):
            path = os.path.join(PIPELINES_DIR, f)
            with open(path, 'r') as pf:
                code = pf.read()
            pipelines.append({
                "id": f.replace('.dap', ''),
                "code": code[:200],
                "created": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
            })
    return jsonify(sorted(pipelines, key=lambda x: x['created'], reverse=True))

@app.route('/api/results/<pipeline_id>', methods=['GET'])
def get_results(pipeline_id):
    # Find output files for this pipeline
    outputs = {}
    for f in os.listdir('.'):
        if f.endswith('.json') and os.path.exists(f):
            with open(f, 'r') as rf:
                try:
                    outputs[f] = json.load(rf)
                except:
                    pass
    
    return jsonify({"pipeline_id": pipeline_id, "outputs": outputs})
@app.route('/dashboard')
def dashboard():
    import os
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloud_dashboard.html')
    return send_file(dashboard_path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🌍 Dapine Cloud API starting on port {port}...\n")
    app.run(host='0.0.0.0', port=port, debug=False)