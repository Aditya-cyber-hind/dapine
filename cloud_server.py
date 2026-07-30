from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import csv
import uuid
import re
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
        "version": "2.0.0",
        "endpoints": [
            "POST /api/upload - Upload CSV/Excel file",
            "POST /api/run - Run Dapine pipeline",
            "GET /api/pipelines - List saved pipelines",
            "GET /api/outputs/<filename> - Download output files (charts, reports)",
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
    
    uploaded_path = os.path.join(UPLOADS_DIR, filename)
    code = re.sub(r'["\']([^"\']*\.(csv|xlsx|json))["\']', f'"{uploaded_path}"', code)
    
    if not code.strip().startswith('pipeline'):
        code = f'pipeline _cloud_run() {{\n{code}\n}}'
    
    pipeline_id = str(uuid.uuid4())[:8]
    pipeline_file = os.path.join(PIPELINES_DIR, f"{pipeline_id}.dap")
    with open(pipeline_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    import subprocess
    result = subprocess.run(
        ['python', 'dapine.py', pipeline_file],
        capture_output=True, text=True, timeout=60
    )
    
    # Find output files generated
    outputs = []
    for f in os.listdir('.'):
        if f.endswith(('.html', '.json', '.csv', '.xlsx', '.md')):
            if os.path.getmtime(f) > os.path.getmtime(pipeline_file) - 10:
                outputs.append(f)
    
    return jsonify({
        "pipeline_id": pipeline_id,
        "status": "completed",
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[:500],
        "outputs": outputs,
        "chart_url": f"/api/outputs/{outputs[0]}" if outputs else None
    })

@app.route('/api/outputs/<filename>')
def get_output(filename):
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({"error": "File not found"}), 404

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌍 Dapine Cloud starting on port {port}")
    app.run(host='0.0.0.0', port=port)