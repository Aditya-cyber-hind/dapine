import os
import json
import csv
from datetime import datetime

class Incremental:
    """Incremental processing - only process new/changed data."""
    
    def __init__(self, state_dir="cloud_data/state"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
    
    def get_last_run(self, pipeline_name):
        """Get timestamp of last successful run."""
        state_file = os.path.join(self.state_dir, f"{pipeline_name}.json")
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return json.load(f)
        return {"last_run": None, "row_count": 0, "checksum": None}
    
    def save_run(self, pipeline_name, row_count, checksum=None):
        """Save run state."""
        state_file = os.path.join(self.state_dir, f"{pipeline_name}.json")
        with open(state_file, 'w') as f:
            json.dump({
                "last_run": datetime.now().isoformat(),
                "row_count": row_count,
                "checksum": checksum
            }, f)
    
    def get_new_rows(self, filepath, pipeline_name):
        """Get only new rows since last run."""
        state = self.get_last_run(pipeline_name)
        last_count = state.get("row_count", 0)
        
        # Read all rows
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_rows = [dict(row) for row in reader]
        
        total_rows = len(all_rows)
        new_rows = all_rows[last_count:]  # Only rows after last count
        
        return new_rows, total_rows, len(new_rows)
    
    def check_changed(self, filepath, pipeline_name):
        """Check if file has changed since last run."""
        state = self.get_last_run(pipeline_name)
        
        # Simple check: file modification time
        mtime = os.path.getmtime(filepath)
        last_run = state.get("last_run")
        
        if last_run is None:
            return True  # First run
        
        last_time = datetime.fromisoformat(last_run).timestamp()
        return mtime > last_time