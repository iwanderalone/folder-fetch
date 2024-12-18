import os
import shutil
import time
import sys
from datetime import datetime, timedelta
from pytz import utc
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Пути к папкам и темплейту
base_path = "C:\\Volumes\\viory\\plan-b\\Files"
ingest_path = "C:\\Volumes\\viory\\plan-b\\Ingest"
template_path = os.path.join(base_path, "_TEMPLATE", "Project")
project_file = os.path.join(template_path, "RENAME ME.prproj")
log_base_path = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(log_base_path, "script_log.txt")

def log_message(message):
    print(message)
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{datetime.now(utc).strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def delete_old_files():
    log_message("Checking for old files to delete...")
    now = time.time()
    cutoff = now - (14 * 86400)  # 2 недели назад
    deleted_files = []

    for path in [base_path, ingest_path]:
        for root, dirs, files in os.walk(path):
            if "_TEMPLATE" in dirs:
                dirs.remove("_TEMPLATE")
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    log_message(f"Deleted {file_path}")

    if not deleted_files:
        log_message("No files were deleted.")
    else:
        log_message("Deleted the following files: " + ', '.join(deleted_files))

def ensure_path_exists(path):
    while True:
        if os.path.exists(path):
            return
        log_message(f"Waiting for connection to access {path}...")
        time.sleep(10)

def create_date_folder(date_str):
    log_message(f"Creating date folders for {date_str}...")
    date_folder_files = os.path.join(base_path, date_str)
    date_folder_ingest = os.path.join(ingest_path, date_str)

    ensure_path_exists(base_path)
    ensure_path_exists(ingest_path)

    if not os.path.exists(date_folder_files):
        os.makedirs(date_folder_files)
        log_message(f"Created folder {date_folder_files}")
    
    if not os.path.exists(date_folder_ingest):
        os.makedirs(date_folder_ingest)
        log_message(f"Created folder {date_folder_ingest}")
    
    return date_folder_files, date_folder_ingest

class FolderMonitorHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            log_message(f"New folder created: {event.src_path}")
            create_subfolders(event.src_path)

def monitor_folder(folder):
    log_message(f"Monitoring folder: {folder}")
    event_handler = FolderMonitorHandler()
    observer = Observer()
    observer.schedule(event_handler, path=folder, recursive=False)  # избегаем создания папок в подпапках
    observer.start()
    return observer

def create_subfolders(folder):
    subfolders = ["Approved PKG", "Project", "Source"]
    for subfolder in subfolders:
        subfolder_path = os.path.join(folder, subfolder)
        os.makedirs(subfolder_path, exist_ok=True)
    shutil.copy(project_file, os.path.join(folder, "Project"))
    log_message(f"Created subfolders and copied project file in {folder}")

def check_and_create_folders(date_str):
    date_folder_files, date_folder_ingest = create_date_folder(date_str)
    monitor_folder(date_folder_files)
    monitor_folder(date_folder_ingest)

def main_loop():
    observers = []
    created_tomorrow_folders = False
    try:
        while True:
            log_message("Starting main loop iteration...")
            delete_old_files()

            now = datetime.now(utc)
            today_date = now.strftime("%d-%m-%Y")

            if not created_tomorrow_folders:
                check_and_create_folders(today_date)

            if now.hour == 20 and now.minute == 0:  # 8 вечера GMT (UTC), 12 ночи по Абу-Даби
                tomorrow_date = (now + timedelta(days=1)).strftime("%d-%m-%Y")
                check_and_create_folders(tomorrow_date)
                created_tomorrow_folders = True
                log_message(f"Created new folders for tomorrow's date: {tomorrow_date}")

            time.sleep(60) 

    
            if now.strftime("%d-%m-%Y") != today_date:
                created_tomorrow_folders = False
    except Exception as e:
        log_message(f"Error in main loop: {e}")
        log_message("Attempting to continue operation...")
    finally:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()

log_message("Script started.")
main_loop()