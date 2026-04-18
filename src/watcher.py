import time
import os
import shutil
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load the keys from your .env file
load_dotenv()

WATCH_DIR = "./test_repo"
API_URL = "http://localhost:8000/ingest"
API_KEY = os.getenv("BACKEND_API_KEY", "REDACTED")

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_triggered = 0

    def on_modified(self, event):
        # We only care about Python files changing (ignore folders and hidden files)
        if event.is_directory or not event.src_path.endswith('.py'):
            return

        # DEBOUNCE LOGIC: 
        # Code editors often fire multiple 'save' events in a fraction of a second.
        # This prevents us from spamming our own API.
        current_time = time.time()
        if current_time - self.last_triggered < 2:
            return
        self.last_triggered = current_time

        print(f"\n[Watcher] 📝 Detected change in: {event.src_path}")
        self.trigger_ingestion()

    def trigger_ingestion(self):
        print("[Watcher] 📦 Zipping repository...")
        shutil.make_archive("auto_upload", 'zip', WATCH_DIR)
        
        print("[Watcher] 🚀 Sending to API...")
        with open("auto_upload.zip", "rb") as f:
            headers = {"X-API-Key": API_KEY}
            files = {"file": ("auto_upload.zip", f, "application/zip")}
            
            try:
                response = requests.post(API_URL, headers=headers, files=files)
                if response.status_code == 200:
                    print("[Watcher] ✅ API accepted the update!")
                elif response.status_code == 429:
                    print("[Watcher] 🚦 Rate limited! Too many saves per minute.")
                elif response.status_code == 403:
                    print("[Watcher] 🛑 Forbidden! Check your API Key.")
                else:
                    print(f"[Watcher] ⚠️ Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"[Watcher] ❌ Failed to connect to API: {e}")
        
        # Cleanup the temp zip file so your folder stays clean
        if os.path.exists("auto_upload.zip"):
            os.remove("auto_upload.zip")

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        print(f"Directory '{WATCH_DIR}' not found. Please create it first.")
        exit()
        
    event_handler = CodeChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=True)
    observer.start()
    
    print(f"👀 Watcher started. Monitoring '{WATCH_DIR}' for live code changes...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nWatcher stopped gracefully.")
    observer.join()