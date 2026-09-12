import psutil
from scheduler import load_config, should_block

def scan_and_kill():
    config = load_config()
    tracked_apps = config.keys()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name']
            if proc_name:
                for target in tracked_apps:
                    if target.lower() == proc_name.lower() and should_block(target):
                        proc.kill()
                        print(f"Violator terminated: {proc_name}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass