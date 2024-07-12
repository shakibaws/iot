import subprocess
import time
import os

# Funzione per aprire uno script in un nuovo terminale
def run_script(script_path):
    command = f'osascript -e \'tell application "Terminal" to do script "python3 {script_path}"\''
    subprocess.run(command, shell=True)

current_path = os.path.dirname(os.path.abspath(__file__))

# Path ai file da eseguire
catalog_expose_scripts = [
        os.path.join(current_path, "catalog_expose/resource_service.py"),
        os.path.join(current_path, "catalog_expose/service_service.py")
]

other_scripts = [
    os.path.join(current_path, "image_recognition/main.py"),
    os.path.join(current_path, "recommendation_service/main.py"),
    os.path.join(current_path, "vase_control/main.py"),
    os.path.join(current_path, "watering_service/main.py")
]

# Esegui i catalog expose scripts
for script in catalog_expose_scripts:
    run_script(script)

# Attendi qualche secondo
time.sleep(5)

# Esegui gli altri scripts
for script in other_scripts:
    run_script(script)
