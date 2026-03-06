import threading
import time
import webview
import streamlit.web.cli as stcli
import sys
import os
import requests
import socket

def find_free_port(start=8501, end=9000):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found")

def run_streamlit(port):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_path, "kobo_dashboard.py")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    stcli.main()

def wait_for_server(url, timeout=15):
    start = time.time()
    while True:
        try:
            requests.get(url)
            break
        except:
            if time.time() - start > timeout:
                break
            time.sleep(0.5)

if __name__ == "__main__":
    port = find_free_port()
    server_url = f"http://localhost:{port}"

    # Start Streamlit in background thread
    thread = threading.Thread(target=run_streamlit, args=(port,))
    thread.daemon = True
    thread.start()

    wait_for_server(server_url)

    # Open embedded browser window
    window = webview.create_window("Dashboard", server_url, width=1200, height=800)
    webview.start()