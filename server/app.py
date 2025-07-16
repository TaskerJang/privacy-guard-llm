# server/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging
from datetime import datetime

# 상위 디렉토리의 masking_module import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_manager import ModelManager
from api_routes import create_api_routes

def create_app():
    app = Flask(__name__)
    CORS(app)  # 크롬 익스텐션에서 접근 허용

    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    app.logger.info('🚀 Privacy Guard LLM Server 시작')

    # 모델 매니저 초기화
    model_manager = ModelManager()
    app.model_manager = model_manager

    # API 라우트 등록
    create_api_routes(app)

    # 서버 상태 체크
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'model_loaded': app.model_manager.is_model_loaded(),
            'version': '1.0.0'
        })

    # 서버 정보
    @app.route('/', methods=['GET'])
    def server_info():
        return jsonify({
            'name': 'Privacy Guard LLM API Server',
            'version': '1.0.0',
            'description': 'AI 기반 의료 텍스트 비식별화 서버',
            'endpoints': {
                'mask': '/api/mask',
                'health': '/health',
                'models': '/api/models',
                'settings': '/api/settings'
            },
            'model_status': app.model_manager.get_model_status()
        })

    return app

if __name__ == '__main__':
    app = create_app()

    print("=" * 60)
    print("🏥🔒 Privacy Guard LLM Server")
    print("=" * 60)
    print("📡 서버 주소: http://localhost:8000")
    print("🔍 헬스체크: http://localhost:8000/health")
    print("📚 API 문서: http://localhost:8000")
    print("🎬 시연 준비 완료!")
    print("=" * 60)

    app.run(host='localhost', port=8000, debug=True)