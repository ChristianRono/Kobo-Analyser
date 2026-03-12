import subprocess
import time
import webview
import sys
import os
import requests
import socket
import signal

def find_free_port(start=8501, end=9000):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found")

def wait_for_server(url, timeout=30):
    start = time.time()
    while True:
        try:
            requests.get(url)
            break
        except requests.exceptions.ConnectionError:
            if time.time() - start > timeout:
                raise RuntimeError(f"Streamlit server failed to start at {url}")
            time.sleep(0.5)

if __name__ == "__main__":
    # Path to Streamlit app
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_path, "kobo_dashboard.py")
    if not os.path.exists(app_path):
        raise FileNotFoundError(f"Streamlit app not found at {app_path}")

    port = find_free_port()
    url = f"http://localhost:{port}"

    # Start Streamlit as a subprocess
    st_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", app_path,
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

    try:
        # Wait for server to be ready
        wait_for_server(url)

        # Open embedded browser window
        window = webview.create_window("Dashboard", url, width=1200, height=800)
        webview.start()
    finally:
        # Ensure Streamlit process is terminated when window closes
        if st_process.poll() is None:  # still running
            st_process.send_signal(signal.SIGTERM)
            st_process.wait()