from flask import Flask, jsonify, send_file
import json
import os

app = Flask(__name__)

# Store latest results
latest_data = {"tables": {}, "charts": [], "logs": []}

def update_dashboard(runtime):
    """Update dashboard with current runtime state."""
    tables = {}
    for name, df in runtime.dataframes.items():
        tables[name] = {
            "rows": len(df.rows),
            "columns": df.schema,
            "preview": df.rows[:5]
        }
    latest_data["tables"] = tables
    latest_data["lineage"] = runtime.lineage_log[-10:]

@app.route('/')
def dashboard():
    return jsonify(latest_data)

@app.route('/view')
def view():
    html = """<!DOCTYPE html><html><head><title>Dapine Live Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0}
h1{color:#e94560}h2{color:#58a6ff}table{width:100%;border-collapse:collapse}
th,td{padding:8px;text-align:left;border-bottom:1px solid #30363d}
th{color:#58a6ff}.badge{background:#238636;padding:3px 10px;border-radius:12px;font-size:12px}</style></head>
<body><h1>📊 Dapine Live Dashboard</h1><div id="content">Loading...</div>
<script>async function refresh(){let r=await fetch('/');let d=await r.json();
let h='';for(let[t,i]of Object.entries(d.tables)){h+=`<div class="card"><h2>📊 ${t} <span class="badge">${i.rows} rows</span></h2>
<table><tr>${i.columns.map(c=>`<th>${c}</th>`).join('')}</tr>${i.preview.map(r=>`<tr>${i.columns.map(c=>`<td>${r[c]||''}</td>`).join('')}</tr>`).join('')}</table></div>`;}
if(d.lineage){h+='<div class="card"><h2>📋 Lineage</h2>'+d.lineage.map(l=>`<div>${l}</div>`).join('')+'</div>';}
document.getElementById('content').innerHTML=h||'No data yet. Run a pipeline!';}
refresh();setInterval(refresh,3000);</script></body></html>"""
    return html

def start_dashboard(port=8080):
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False), daemon=True).start()
    print(f"📊 Live dashboard at http://localhost:{port}/view")