# server/model_manager.py
import os
import sys
import logging
from typing import Optional, Dict, Any

# 상위 디렉토리의 masking_module import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from masking_module import CompleteMedicalDeidentificationPipeline
except ImportError as e:
    logging.error(f"masking_module import 실패: {e}")
    CompleteMedicalDeidentificationPipeline = None

class ModelManager:
    """모델 로딩 및 관리 클래스"""

    def __init__(self):
        # 로컬 모델 경로 설정 (상대 경로)
        self.model_path = "../ner-koelectra-lora-merged"

        self.pipeline = None
        self.model_info = {
            'name': 'KoELECTRA + LoRA (Local)',
            'version': '1.0.0',
            'loaded': False,
            'error': None
        }

        # 모델 자동 로드 시도
        self.load_model()

    def load_model(self, model_path: str = None, threshold: int = 50) -> bool:
        """모델 로드"""
        try:
            if CompleteMedicalDeidentificationPipeline is None:
                raise ImportError("masking_module을 import할 수 없습니다")

            logging.info("🔄 Privacy Guard 파이프라인 로딩 중...")

            # 실제 로컬 모델 경로 사용
            if model_path is None:
                model_path = self.model_path  # 로컬 경로 사용

            # 절대 경로로 변환
            abs_model_path = os.path.abspath(model_path)
            logging.info(f"🔍 모델 경로 확인: {abs_model_path}")

            # 경로 존재 확인
            if not os.path.exists(abs_model_path):
                logging.warning(f"⚠️ 모델 경로 없음: {abs_model_path}")
                logging.info("🔄 더미 모델로 대체합니다...")
                model_path = "dummy"
                abs_model_path = "dummy"
            else:
                logging.info(f"✅ 모델 경로 확인됨: {abs_model_path}")
                # 필수 파일 확인
                required_files = ['config.json']
                for file in required_files:
                    file_path = os.path.join(abs_model_path, file)
                    if not os.path.exists(file_path):
                        logging.warning(f"⚠️ 필수 파일 없음: {file_path}")
                        model_path = "dummy"
                        abs_model_path = "dummy"
                        break

            self.pipeline = CompleteMedicalDeidentificationPipeline(
                model_path=model_path,
                threshold=threshold,
                use_contextual_analysis=True
            )

            self.model_info.update({
                'loaded': True,
                'error': None,
                'model_path': abs_model_path,
                'threshold': threshold,
                'model_type': 'local' if model_path != 'dummy' else 'dummy'
            })

            logging.info("✅ 모델 로드 완료!")
            return True

        except Exception as e:
            error_msg = f"모델 로드 실패: {str(e)}"
            logging.error(error_msg)

            self.model_info.update({
                'loaded': False,
                'error': error_msg
            })

            return False

    def process_text(self, text: str, settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """텍스트 처리"""
        if not self.is_model_loaded():
            return {
                'success': False,
                'error': 'Model not loaded',
                'fallback': True
            }

        try:
            # 설정 업데이트 (임계값 등)
            if settings:
                if 'threshold' in settings:
                    self.pipeline.masking_executor.threshold = settings['threshold']

            # 실제 처리
            result = self.pipeline.process(text, verbose=False)

            return {
                'success': True,
                'masked_text': result.masked_text,
                'original_text': result.original_text,
                'total_entities': result.total_entities,
                'masked_entities': result.masked_entities,
                'masking_log': [
                    {
                        'token': log['token'],
                        'entity': log.get('entity', 'UNKNOWN'),
                        'risk_weight': log.get('risk_weight', 0),
                        'masked_as': log.get('masked_as', '[MASKED]'),
                        'reason': log.get('reason', '')
                    }
                    for log in result.masking_log
                ],
                'stats': {
                    'processing_time': 0.1,  # 실제 측정하려면 time 모듈 사용
                    'avg_risk': sum(log.get('risk_weight', 0) for log in result.masking_log) / len(result.masking_log) if result.masking_log else 0
                }
            }

        except Exception as e:
            logging.error(f"텍스트 처리 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': True
            }

    def is_model_loaded(self) -> bool:
        """모델 로드 상태 확인"""
        return self.pipeline is not None and self.model_info['loaded']

    def get_model_status(self) -> Dict[str, Any]:
        """모델 상태 정보 반환"""
        return self.model_info.copy()

    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """설정 업데이트"""
        try:
            if self.pipeline and 'threshold' in settings:
                self.pipeline.masking_executor.threshold = settings['threshold']
                self.model_info['threshold'] = settings['threshold']

            return True
        except Exception as e:
            logging.error(f"설정 업데이트 실패: {e}")
            return False