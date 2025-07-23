import subprocess
import sys
import os

def install_all_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_path], check=True)
    else:
        print("requirements.txt not found.")

install_all_requirements()
