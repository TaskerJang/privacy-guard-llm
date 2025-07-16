# scripts/start_demo.py
import os
import sys
import subprocess
import time
import webbrowser
import requests
from pathlib import Path

def check_dependencies():
    """의존성 체크"""
    print("🔍 의존성 체크 중...")

    try:
        import flask
        import flask_cors
        print("✅ Flask 설치됨")
    except ImportError:
        print("❌ Flask 미설치 - pip install flask flask-cors 실행 필요")
        return False

    # masking_module 체크
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))

    try:
        from masking_module import CompleteMedicalDeidentificationPipeline
        print("✅ masking_module 로드 가능")
        return True
    except ImportError as e:
        print(f"❌ masking_module 로드 실패: {e}")
        print("💡 상위 디렉토리에 masking_module.py가 있는지 확인하세요")
        return False

def start_server():
    """서버 시작"""
    print("🚀 Privacy Guard 서버 시작 중...")

    server_path = Path(__file__).parent.parent / "server" / "app.py"

    # 서버 실행 (백그라운드)
    process = subprocess.Popen([
        sys.executable, str(server_path)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 서버 시작 대기
    print("⏳ 서버 시작 대기 중...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ 서버 시작 완료!")
                return process
        except:
            pass

        time.sleep(1)
        print(f"   {i+1}/10초 대기...")

    print("❌ 서버 시작 실패")
    return None

def open_demo_page():
    """데모 페이지 열기"""
    demo_path = Path(__file__).parent.parent / "extension" / "demo-page.html"
    demo_url = f"file://{demo_path.absolute()}"

    print(f"🌐 데모 페이지 열기: {demo_url}")
    webbrowser.open(demo_url)

def show_instructions():
    """사용 안내"""
    print("\n" + "="*60)
    print("🎬 Privacy Guard LLM 시연 준비 완료!")
    print("="*60)
    print("📋 다음 단계를 따라하세요:")
    print()
    print("1. 🔧 크롬 익스텐션 설치:")
    print("   - Chrome 주소창에 chrome://extensions/ 입력")
    print("   - '개발자 모드' 활성화")
    print("   - '압축해제된 확장 프로그램을 로드합니다' 클릭")
    print("   - extension/ 폴더 선택")
    print()
    print("2. 🛡️ 익스텐션 사용:")
    print("   - 브라우저 상단의 Privacy Guard 아이콘 클릭")
    print("   - '보호 기능' 토글 ON")
    print("   - '스캔' 버튼 클릭")
    print()
    print("3. 🎯 실제 Python 모델 사용 중!")
    print("   - KoELECTRA + LoRA 파이프라인")
    print("   - 4단계 비식별화 프로세스")
    print("   - 서버 API: http://localhost:8000")
    print()
    print("4. 🎥 시연 포인트:")
    print("   - 실시간 개인정보 마스킹")
    print("   - 의료 도메인 특화 성능")
    print("   - Python ↔ JavaScript 하이브리드")
    print("="*60)

def main():
    """메인 실행"""
    print("🏥🔒 Privacy Guard LLM 시연 시작!")
    print("="*60)

    # 1. 의존성 체크
    if not check_dependencies():
        print("\n❌ 의존성 문제로 시연을 시작할 수 없습니다.")
        return

    # 2. 서버 시작
    server_process = start_server()
    if not server_process:
        print("\n❌ 서버 시작 실패로 시연을 시작할 수 없습니다.")
        return

    # 3. 데모 페이지 열기
    time.sleep(2)
    open_demo_page()

    # 4. 사용 안내
    show_instructions()

    # 5. 서버 대기
    try:
        print("\n💡 서버가 실행 중입니다. Ctrl+C로 종료하세요.")
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 서버 종료 중...")
        server_process.terminate()
        print("✅ 시연 종료!")

if __name__ == "__main__":
    main()