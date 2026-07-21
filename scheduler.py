import time
import threading
import schedule

class Scheduler:
    def __init__(self):
        self.jobs = []
        self.running = False
    
    def add(self, interval, unit, pipeline_func):
        """Schedule a pipeline. unit: seconds, minutes, hours, daily"""
        if unit == "seconds":
            schedule.every(interval).seconds.do(pipeline_func)
        elif unit == "minutes":
            schedule.every(interval).minutes.do(pipeline_func)
        elif unit == "hours":
            schedule.every(interval).hours.do(pipeline_func)
        elif unit == "daily":
            schedule.every().day.at(interval).do(pipeline_func)
        
        if not self.running:
            self.running = True
            threading.Thread(target=self._run, daemon=True).start()
    
    def _run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)