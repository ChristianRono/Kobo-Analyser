import threading
import time
import webview
import streamlit.web.cli as stcli
import sys
import os
import requests

def run_streamlit():
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_path, "app.py")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]

    stcli.main()

def wait_for_server(url="http://localhost:8501", timeout=15):
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
    thread = threading.Thread(target=run_streamlit)
    thread.daemon = True
    thread.start()

    wait_for_server()  # Wait until Streamlit is ready

    window = webview.create_window("Dashboard", "http://localhost:8501", width=1200, height=800)
    webview.start()

    # When window closes, the Streamlit thread exits because daemon=True