# server/api_routes.py
from flask import request, jsonify
import time
import logging

def create_api_routes(app):
    """API 라우트 생성"""

    @app.route('/api/mask', methods=['POST'])
    def mask_text():
        """텍스트 마스킹 API"""
        try:
            # 요청 데이터 검증
            if not request.is_json:
                return jsonify({'success': False, 'error': 'JSON 형식이 아닙니다'}), 400

            data = request.get_json()

            if 'text' not in data:
                return jsonify({'success': False, 'error': 'text 필드가 필요합니다'}), 400

            text = data['text']
            if not text or len(text.strip()) == 0:
                return jsonify({'success': False, 'error': '텍스트가 비어있습니다'}), 400

            # 설정 파라미터
            settings = {
                'threshold': data.get('threshold', 50),
                'mode': data.get('mode', 'medical'),
                'use_contextual_analysis': data.get('use_contextual_analysis', True)
            }

            # 처리 시간 측정
            start_time = time.time()

            # 모델로 처리
            result = app.model_manager.process_text(text, settings)

            processing_time = time.time() - start_time

            if result['success']:
                # 성공 응답
                response = {
                    'success': True,
                    'masked_text': result['masked_text'],
                    'original_text': result['original_text'],
                    'stats': {
                        'total_entities': result['total_entities'],
                        'masked_entities': result['masked_entities'],
                        'processing_time': round(processing_time, 3),
                        'avg_risk': result['stats']['avg_risk']
                    },
                    'masking_log': result['masking_log'],
                    'model_info': {
                        'name': 'KoELECTRA + LoRA',
                        'pipeline_stages': 4,
                        'threshold': settings['threshold']
                    }
                }

                app.logger.info(f"✅ 마스킹 완료: {result['masked_entities']}/{result['total_entities']} (소요시간: {processing_time:.3f}s)")
                return jsonify(response)

            else:
                # 실패 시 fallback 안내
                return jsonify({
                    'success': False,
                    'error': result['error'],
                    'fallback': result.get('fallback', False),
                    'message': '서버 모델 사용 불가 - JavaScript 버전으로 fallback 권장'
                }), 500

        except Exception as e:
            app.logger.error(f"❌ API 오류: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'fallback': True
            }), 500

    @app.route('/api/models', methods=['GET'])
    def get_models():
        """모델 정보 조회"""
        model_status = app.model_manager.get_model_status()
        return jsonify({
            'models': [model_status],
            'current_model': model_status['name'] if model_status['loaded'] else None,
            'total_models': 1
        })

    @app.route('/api/settings', methods=['GET', 'POST'])
    def handle_settings():
        """설정 관리"""
        if request.method == 'GET':
            # 현재 설정 조회
            return jsonify({
                'current_settings': app.model_manager.get_model_status(),
                'available_settings': {
                    'threshold': {'min': 10, 'max': 100, 'default': 50},
                    'modes': ['medical', 'general', 'strict'],
                    'contextual_analysis': {'type': 'boolean', 'default': True}
                }
            })

        elif request.method == 'POST':
            # 설정 업데이트
            data = request.get_json()
            success = app.model_manager.update_settings(data)

            return jsonify({
                'success': success,
                'updated_settings': app.model_manager.get_model_status()
            })

    @app.route('/api/test', methods=['POST'])
    def test_pipeline():
        """파이프라인 테스트용 API"""
        test_cases = [
            "김철수씨가 2023년 10월에 서울대병원에서 간암 진단을 받았습니다.",
            "박영희(010-1234-5678)는 삼성서울병원에서 수술을 받았다.",
            "환자는 내일 검사를 받을 예정입니다."
        ]

        results = []
        for text in test_cases:
            result = app.model_manager.process_text(text)
            results.append({
                'input': text,
                'output': result.get('masked_text', '처리 실패'),
                'success': result['success']
            })

        return jsonify({
            'test_results': results,
            'model_status': app.model_manager.get_model_status()
        })