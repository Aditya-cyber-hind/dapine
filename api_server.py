from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading

class DapineAPI:
    def __init__(self, runtime, port=8080):
        self.runtime = runtime
        self.port = port
    
    def start(self):
        runtime = self.runtime
        
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/tables":
                    tables = {k: {"rows": len(v.rows), "cols": v.schema} for k, v in runtime.dataframes.items()}
                    self._json(tables)
                elif self.path == "/lineage":
                    self._json(runtime.lineage_log)
                else:
                    self._json({"message": "Dapine API", "endpoints": ["/tables", "/lineage"]})
            
            def do_POST(self):
                if self.path == "/run":
                    content_length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(content_length))
                    self._json({"status": "received", "code": body.get("code", "")})
            
            def _json(self, data):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data, default=str).encode())
            
            def log_message(self, format, *args):
                pass
        
        server = HTTPServer(('localhost', self.port), Handler)
        print(f"🌐 Dapine API running at http://localhost:{self.port}")
        print(f"   GET  /tables  - List all tables")
        print(f"   GET  /lineage - Show lineage")
        print(f"   POST /run     - Execute code")
        threading.Thread(target=server.serve_forever, daemon=True).start()