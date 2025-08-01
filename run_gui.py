# run_gui.py
"""
LocalMind GUI 실행 스크립트
"""

import subprocess
import sys
import os

def check_requirements():
    """필요한 패키지 확인"""
    try:
        import streamlit
        import sqlite3
        import pandas
        print("✅ 필요한 패키지가 모두 설치되어 있습니다.")
        return True
    except ImportError as e:
        print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
        print("다음 명령어로 패키지를 설치해주세요:")
        print("pip install -r requirements.txt")
        return False

def run_gui():
    """GUI 실행"""
    if not check_requirements():
        return
    
    print("🚀 LocalMind GUI를 시작합니다...")
    print("브라우저에서 http://localhost:8501 로 접속하세요.")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "gui_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 LocalMind GUI를 종료합니다.")
    except Exception as e:
        print(f"❌ GUI 실행 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    run_gui()