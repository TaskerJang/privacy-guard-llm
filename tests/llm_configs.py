"""
LLM 설정 파일 - 2025년 7월 최신 모델
다양한 LLM 제공자의 최신 모델 설정을 관리
"""

import os
import logging
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class RiskLevel(Enum):
    """위험도 레벨 정의"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class LLMConfig:
    """LLM 설정 클래스"""
    name: str
    provider: str
    model_id: str
    api_key: str
    temperature: float = 0.1
    max_tokens: int = 1000
    cost_per_1k_tokens: float = 0.003
    available: bool = True
    description: str = ""

class LLMConfigManager:
    """LLM 설정 관리자"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.configs = self._setup_all_configs()

    def _setup_all_configs(self) -> Dict[str, LLMConfig]:
        """모든 LLM 설정 초기화"""
        configs = {}

        # OpenAI 모델들 추가
        configs.update(self._setup_openai_configs())

        # Anthropic 모델들 추가
        configs.update(self._setup_anthropic_configs())

        # Google 모델들 추가
        configs.update(self._setup_google_configs())

        # Cohere 모델들 추가
        configs.update(self._setup_cohere_configs())

        # 사용 가능한 모델만 필터링
        available_configs = {k: v for k, v in configs.items() if v.available}

        self.logger.info(f"총 {len(available_configs)}개 LLM 모델 사용 가능")
        return available_configs

    def _setup_openai_configs(self) -> Dict[str, LLMConfig]:
        """OpenAI 모델 설정"""
        configs = {}

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.warning("OpenAI API 키가 설정되지 않았습니다.")
            return configs

        try:
            import openai

            configs.update({
                'gpt-4.1': LLMConfig(
                    name='GPT-4.1',
                    provider='openai',
                    model_id='gpt-4.1',
                    api_key=api_key,
                    cost_per_1k_tokens=0.006,
                    max_tokens=2000,
                    description='최신 OpenAI 모델, 100만 토큰 문맥 처리'
                ),
                'gpt-4o': LLMConfig(
                    name='GPT-4o',
                    provider='openai',
                    model_id='gpt-4o',
                    api_key=api_key,
                    cost_per_1k_tokens=0.005,
                    description='강력한 범용 모델'
                ),
                'gpt-4o-mini': LLMConfig(
                    name='GPT-4o-Mini',
                    provider='openai',
                    model_id='gpt-4o-mini',
                    api_key=api_key,
                    cost_per_1k_tokens=0.00015,
                    description='빠르고 저렴한 경량 모델'
                )
            })

            self.logger.info(f"OpenAI 모델 {len(configs)}개 설정 완료")

        except ImportError:
            self.logger.warning("OpenAI 라이브러리가 설치되지 않았습니다.")

        return configs

    def _setup_anthropic_configs(self) -> Dict[str, LLMConfig]:
        """Anthropic 모델 설정"""
        configs = {}

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            self.logger.warning("Anthropic API 키가 설정되지 않았습니다.")
            return configs

        try:
            import anthropic

            configs.update({
                'claude-opus-4': LLMConfig(
                    name='Claude-Opus-4',
                    provider='anthropic',
                    model_id='claude-opus-4-20250514',
                    api_key=api_key,
                    cost_per_1k_tokens=0.02,
                    max_tokens=2000,
                    description='최고 성능 Claude 모델, 코딩·추론 특화'
                ),
                'claude-sonnet-4': LLMConfig(
                    name='Claude-Sonnet-4',
                    provider='anthropic',
                    model_id='claude-sonnet-4-20250514',
                    api_key=api_key,
                    cost_per_1k_tokens=0.004,
                    description='균형잡힌 성능의 Claude 모델'
                ),
                'claude-3-5-sonnet': LLMConfig(
                    name='Claude-3.5-Sonnet',
                    provider='anthropic',
                    model_id='claude-3-5-sonnet-20241022',
                    api_key=api_key,
                    cost_per_1k_tokens=0.003,
                    description='이전 세대 고성능 모델'
                )
            })

            self.logger.info(f"Anthropic 모델 {len(configs)}개 설정 완료")

        except ImportError:
            self.logger.warning("Anthropic 라이브러리가 설치되지 않았습니다.")

        return configs

    def _setup_google_configs(self) -> Dict[str, LLMConfig]:
        """Google 모델 설정"""
        configs = {}

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            self.logger.warning("Google API 키가 설정되지 않았습니다.")
            return configs

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            configs.update({
                'gemini-2.5-pro': LLMConfig(
                    name='Gemini-2.5-Pro',
                    provider='google',
                    model_id='gemini-2.5-pro',
                    api_key=api_key,
                    cost_per_1k_tokens=0.004,
                    max_tokens=2000,
                    description='고난도 추론 특화 모델'
                ),
                'gemini-2.5-flash': LLMConfig(
                    name='Gemini-2.5-Flash',
                    provider='google',
                    model_id='gemini-2.5-flash',
                    api_key=api_key,
                    cost_per_1k_tokens=0.0004,
                    description='고속 처리 특화 모델'
                ),
                'gemini-2.5-flash-lite': LLMConfig(
                    name='Gemini-2.5-Flash-Lite',
                    provider='google',
                    model_id='gemini-2.5-flash-lite',
                    api_key=api_key,
                    cost_per_1k_tokens=0.0002,
                    description='고속 분류 특화 경량 모델'
                )
            })

            self.logger.info(f"Google 모델 {len(configs)}개 설정 완료")

        except ImportError:
            self.logger.warning("Google GenerativeAI 라이브러리가 설치되지 않았습니다.")

        return configs

    def _setup_cohere_configs(self) -> Dict[str, LLMConfig]:
        """Cohere 모델 설정"""
        configs = {}

        api_key = os.getenv('COHERE_API_KEY')
        if not api_key:
            self.logger.warning("Cohere API 키가 설정되지 않았습니다.")
            return configs

        try:
            import cohere

            configs.update({
                'command-xlarge': LLMConfig(
                    name='Command-XLarge',
                    provider='cohere',
                    model_id='command-xlarge',
                    api_key=api_key,
                    cost_per_1k_tokens=0.003,
                    description='분류 작업 특화 모델'
                ),
                'command-r-plus': LLMConfig(
                    name='Command-R-Plus',
                    provider='cohere',
                    model_id='command-r-plus',
                    api_key=api_key,
                    cost_per_1k_tokens=0.0025,
                    description='지시 지향 성능 특화 모델'
                )
            })

            self.logger.info(f"Cohere 모델 {len(configs)}개 설정 완료")

        except ImportError:
            self.logger.warning("Cohere 라이브러리가 설치되지 않았습니다.")

        return configs

    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 반환"""
        return list(self.configs.keys())

    def get_config(self, model_name: str) -> LLMConfig:
        """특정 모델의 설정 반환"""
        if model_name not in self.configs:
            raise ValueError(f"모델 '{model_name}'을 찾을 수 없습니다.")
        return self.configs[model_name]

    def get_precision_group(self) -> List[str]:
        """정밀 비교용 모델 그룹"""
        precision_models = ['gpt-4.1', 'claude-opus-4', 'gemini-2.5-pro']
        return [model for model in precision_models if model in self.configs]

    def get_speed_group(self) -> List[str]:
        """속도 테스트용 모델 그룹"""
        speed_models = ['gemini-2.5-flash-lite', 'claude-sonnet-4', 'gpt-4o-mini']
        return [model for model in speed_models if model in self.configs]

    def get_cost_efficient_group(self) -> List[str]:
        """비용 효율적 모델 그룹"""
        cost_models = ['gpt-4o-mini', 'gemini-2.5-flash-lite', 'command-r-plus']
        return [model for model in cost_models if model in self.configs]

    def print_summary(self):
        """설정 요약 출력"""
        print("🤖 LLM 모델 설정 요약")
        print("=" * 60)

        if not self.configs:
            print("❌ 사용 가능한 모델이 없습니다.")
            print("API 키를 설정하고 필요한 라이브러리를 설치하세요.")
            return

        providers = {}
        for config in self.configs.values():
            if config.provider not in providers:
                providers[config.provider] = []
            providers[config.provider].append(config)

        for provider, models in providers.items():
            print(f"\n🔧 {provider.upper()}:")
            for model in models:
                print(f"   • {model.name} (${model.cost_per_1k_tokens:.4f}/1K토큰)")
                print(f"     {model.description}")

        print(f"\n📊 실험 그룹:")
        print(f"   🎯 정밀 비교: {self.get_precision_group()}")
        print(f"   ⚡ 속도 테스트: {self.get_speed_group()}")
        print(f"   💰 비용 효율: {self.get_cost_efficient_group()}")

if __name__ == "__main__":
    # 설정 테스트
    manager = LLMConfigManager()
    manager.print_summary()