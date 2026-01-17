# ComfyUI/custom_nodes/ComfyUI-Internode/install.py
# VERSION 3.0.0
import sys
import subprocess
import os

def install():
    requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")
    
    if not os.path.exists(requirements_path):
        print(f"#### Internode Error: requirements.txt not found at {requirements_path}")
        return

    print(f"#### Internode: Installing dependencies from {requirements_path}...")
    
    try:
        # Using sys.executable ensures we install to the current python environment
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("#### Internode: Installation successful.")
    except subprocess.CalledProcessError as e:
        print(f"#### Internode: Installation failed with error: {e}")
    except Exception as e:
        print(f"#### Internode: An unexpected error occurred: {e}")

if __name__ == "__main__":
    install()