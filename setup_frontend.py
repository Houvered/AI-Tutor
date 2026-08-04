import os
import shutil
import subprocess
import urllib.request
import zipfile

NODE_URL = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip"
ZIP_PATH = "node_temp.zip"
DEST_DIR = "node_bin"

def setup_node_and_build():
    project_root = os.path.abspath(os.path.dirname(__file__))
    node_dir = os.path.join(project_root, DEST_DIR)

    if not os.path.exists(node_dir):
        print("[1/3] Downloading portable Node.js v20.18.0...")
        urllib.request.urlretrieve(NODE_URL, ZIP_PATH)
        
        print("[2/3] Extracting Node.js package...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall("node_extract")
        
        extracted_folder = os.path.join("node_extract", os.listdir("node_extract")[0])
        shutil.move(extracted_folder, node_dir)
        
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
        if os.path.exists("node_extract"):
            shutil.rmtree("node_extract")
        print("Node.js portable extracted successfully!")
    else:
        print("Node.js portable directory already exists.")

    env = os.environ.copy()
    env["PATH"] = node_dir + os.path.pathsep + env["PATH"]

    frontend_dir = os.path.join(project_root, "frontend")

    npm_cmd = os.path.join(node_dir, "npm.cmd")

    print("[3/3] Installing frontend dependencies (npm install)...")
    subprocess.run([npm_cmd, "install"], cwd=frontend_dir, env=env, shell=True, check=True)

    print("Building React Web UI (npm run build)...")
    subprocess.run([npm_cmd, "run", "build"], cwd=frontend_dir, env=env, shell=True, check=True)

    print("\nSUCCESS! Web UI build completed in frontend/dist.")

if __name__ == "__main__":
    setup_node_and_build()
