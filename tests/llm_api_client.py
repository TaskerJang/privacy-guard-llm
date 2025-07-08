"""
LLM API 클라이언트 - 다양한 LLM 제공자 통합 클라이언트
OpenAI, Anthropic, Google, Cohere API 호출 및 결과 처리
"""

import json
import time
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from llm_configs import LLMConfig, RiskLevel

# 각 LLM 라이브러리 import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

@dataclass
class APIResponse:
    """API 응답 결과"""
    success: bool
    content: str
    token_count: int
    processing_time: float
    cost: float
    error_message: str = ""
    raw_response: Any = None

class LLMAPIClient:
    """LLM API 통합 클라이언트"""

    def __init__(self, max_cost: float = 5.0):
        self.logger = logging.getLogger(__name__)
        self.total_cost = 0.0
        self.max_cost = max_cost
        self.request_count = 0

        # API 클라이언트 초기화
        self._setup_clients()

    def _setup_clients(self):
        """API 클라이언트 초기화"""
        self.clients = {}

        # OpenAI 클라이언트
        if OPENAI_AVAILABLE:
            self.clients['openai'] = None  # 나중에 API 키와 함께 초기화

        # Anthropic 클라이언트
        if ANTHROPIC_AVAILABLE:
            self.clients['anthropic'] = None

        # Google 클라이언트
        if GOOGLE_AVAILABLE:
            self.clients['google'] = None

        # Cohere 클라이언트
        if COHERE_AVAILABLE:
            self.clients['cohere'] = None

    def _get_client(self, provider: str, api_key: str):
        """제공자별 클라이언트 반환"""
        if provider == 'openai' and OPENAI_AVAILABLE:
            if self.clients['openai'] is None:
                self.clients['openai'] = OpenAI(api_key=api_key)
            return self.clients['openai']

        elif provider == 'anthropic' and ANTHROPIC_AVAILABLE:
            if self.clients['anthropic'] is None:
                self.clients['anthropic'] = anthropic.Anthropic(api_key=api_key)
            return self.clients['anthropic']

        elif provider == 'google' and GOOGLE_AVAILABLE:
            if self.clients['google'] is None:
                genai.configure(api_key=api_key)
            return genai

        elif provider == 'cohere' and COHERE_AVAILABLE:
            if self.clients['cohere'] is None:
                self.clients['cohere'] = cohere.Client(api_key=api_key)
            return self.clients['cohere']

        else:
            raise ValueError(f"지원하지 않는 제공자: {provider}")

    def _call_openai_api(self, config: LLMConfig, prompt: str) -> APIResponse:
        """OpenAI API 호출"""
        start_time = time.time()

        try:
            client = self._get_client('openai', config.api_key)

            response = client.chat.completions.create(
                model=config.model_id,
                messages=[
                    {"role": "system", "content": "당신은 개인정보 보호 전문가입니다. 정확한 JSON 형식으로 응답해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

            content = response.choices[0].message.content
            token_count = response.usage.total_tokens
            processing_time = time.time() - start_time
            cost = token_count * config.cost_per_1k_tokens / 1000

            return APIResponse(
                success=True,
                content=content,
                token_count=token_count,
                processing_time=processing_time,
                cost=cost,
                raw_response=response
            )

        except Exception as e:
            self.logger.error(f"OpenAI API 호출 실패: {e}")
            return APIResponse(
                success=False,
                content="",
                token_count=0,
                processing_time=time.time() - start_time,
                cost=0.0,
                error_message=str(e)
            )

    def _call_anthropic_api(self, config: LLMConfig, prompt: str) -> APIResponse:
        """Anthropic API 호출"""
        start_time = time.time()

        try:
            client = self._get_client('anthropic', config.api_key)

            response = client.messages.create(
                model=config.model_id,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            token_count = response.usage.input_tokens + response.usage.output_tokens
            processing_time = time.time() - start_time
            cost = token_count * config.cost_per_1k_tokens / 1000

            return APIResponse(
                success=True,
                content=content,
                token_count=token_count,
                processing_time=processing_time,
                cost=cost,
                raw_response=response
            )

        except Exception as e:
            self.logger.error(f"Anthropic API 호출 실패: {e}")
            return APIResponse(
                success=False,
                content="",
                token_count=0,
                processing_time=time.time() - start_time,
                cost=0.0,
                error_message=str(e)
            )

    def _call_google_api(self, config: LLMConfig, prompt: str) -> APIResponse:
        """Google API 호출"""
        start_time = time.time()

        try:
            genai_client = self._get_client('google', config.api_key)
            model = genai_client.GenerativeModel(config.model_id)

            response = model.generate_content(
                prompt,
                generation_config=genai_client.types.GenerationConfig(
                    temperature=config.temperature,
                    max_output_tokens=config.max_tokens,
                )
            )

            content = response.text
            # Google은 정확한 토큰 카운트를 제공하지 않을 수 있음
            token_count = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else len(content.split()) * 1.3
            processing_time = time.time() - start_time
            cost = token_count * config.cost_per_1k_tokens / 1000

            return APIResponse(
                success=True,
                content=content,
                token_count=int(token_count),
                processing_time=processing_time,
                cost=cost,
                raw_response=response
            )

        except Exception as e:
            self.logger.error(f"Google API 호출 실패: {e}")
            return APIResponse(
                success=False,
                content="",
                token_count=0,
                processing_time=time.time() - start_time,
                cost=0.0,
                error_message=str(e)
            )

    def _call_cohere_api(self, config: LLMConfig, prompt: str) -> APIResponse:
        """Cohere API 호출"""
        start_time = time.time()

        try:
            client = self._get_client('cohere', config.api_key)

            response = client.chat(
                model=config.model_id,
                message=prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

            content = response.text
            token_count = response.meta.tokens.input_tokens + response.meta.tokens.output_tokens if hasattr(response, 'meta') else len(content.split()) * 1.3
            processing_time = time.time() - start_time
            cost = token_count * config.cost_per_1k_tokens / 1000

            return APIResponse(
                success=True,
                content=content,
                token_count=int(token_count),
                processing_time=processing_time,
                cost=cost,
                raw_response=response
            )

        except Exception as e:
            self.logger.error(f"Cohere API 호출 실패: {e}")
            return APIResponse(
                success=False,
                content="",
                token_count=0,
                processing_time=time.time() - start_time,
                cost=0.0,
                error_message=str(e)
            )

    def call_api(self, config: LLMConfig, prompt: str) -> APIResponse:
        """통합 API 호출"""
        # 비용 체크
        estimated_cost = len(prompt.split()) * 1.3 * config.cost_per_1k_tokens / 1000
        if self.total_cost + estimated_cost > self.max_cost:
            return APIResponse(
                success=False,
                content="",
                token_count=0,
                processing_time=0.0,
                cost=0.0,
                error_message=f"비용 한도 초과: {self.total_cost + estimated_cost:.4f} > {self.max_cost:.4f}"
            )

        # 제공자별 API 호출
        if config.provider == 'openai':
            response = self._call_openai_api(config, prompt)
        elif config.provider == 'anthropic':
            response = self._call_anthropic_api(config, prompt)
        elif config.provider == 'google':
            response = self._call_google_api(config, prompt)
        elif config.provider == 'cohere':
            response = self._call_cohere_api(config, prompt)
        else:
            return APIResponse(
                success=False,
                content="",
                token_count=0,
                processing_time=0.0,
                cost=0.0,
                error_message=f"지원하지 않는 제공자: {config.provider}"
            )

        # 비용 업데이트
        if response.success:
            self.total_cost += response.cost
            self.request_count += 1

        return response

    def parse_response(self, response_content: str) -> Dict[str, Any]:
        """API 응답 파싱"""
        try:
            # JSON 부분 추출
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)

                # 필수 필드 확인
                required_fields = ['risk_score', 'risk_level', 'detected_entities', 'explanation', 'domain']
                for field in required_fields:
                    if field not in result:
                        result[field] = self._get_default_value(field)

                return result
            else:
                # JSON이 없는 경우 텍스트에서 추출 시도
                return self._extract_from_text(response_content)

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 파싱 실패: {e}")
            return self._extract_from_text(response_content)

    def _get_default_value(self, field: str) -> Any:
        """기본값 반환"""
        defaults = {
            'risk_score': 0,
            'risk_level': 'NONE',
            'detected_entities': [],
            'explanation': 'JSON 파싱 실패',
            'domain': 'unknown',
            'recommendations': []
        }
        return defaults.get(field, None)

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """텍스트에서 정보 추출 (JSON 파싱 실패시)"""
        result = {
            'risk_score': 0,
            'risk_level': 'NONE',
            'detected_entities': [],
            'explanation': text[:200] + "..." if len(text) > 200 else text,
            'domain': 'unknown',
            'recommendations': []
        }

        # 위험도 키워드 검색
        text_lower = text.lower()
        if 'critical' in text_lower or 'very high' in text_lower:
            result['risk_level'] = 'CRITICAL'
            result['risk_score'] = 95
        elif 'high' in text_lower:
            result['risk_level'] = 'HIGH'
            result['risk_score'] = 80
        elif 'medium' in text_lower or 'moderate' in text_lower:
            result['risk_level'] = 'MEDIUM'
            result['risk_score'] = 60
        elif 'low' in text_lower:
            result['risk_level'] = 'LOW'
            result['risk_score'] = 30

        return result

    def analyze_text(self, text: str, config: LLMConfig, prompt: str, expected_risk: str) -> Dict[str, Any]:
        """텍스트 분석 (통합 인터페이스)"""
        # API 호출
        api_response = self.call_api(config, prompt)

        if not api_response.success:
            return {
                'text': text,
                'model_name': config.name,
                'predicted_risk': 'NONE',
                'expected_risk': expected_risk,
                'risk_score': 0.0,
                'detected_entities': [],
                'explanation': api_response.error_message,
                'domain': 'unknown',
                'processing_time': api_response.processing_time,
                'token_count': api_response.token_count,
                'cost': api_response.cost,
                'correct': False,
                'error': True,
                'recommendations': []
            }

        # 응답 파싱
        parsed_result = self.parse_response(api_response.content)

        # 위험도 레벨 매핑
        risk_level_map = {
            'CRITICAL': RiskLevel.CRITICAL,
            'HIGH': RiskLevel.HIGH,
            'MEDIUM': RiskLevel.MEDIUM,
            'LOW': RiskLevel.LOW,
            'NONE': RiskLevel.NONE
        }

        predicted_risk = parsed_result['risk_level']
        is_correct = predicted_risk == expected_risk

        return {
            'text': text,
            'model_name': config.name,
            'predicted_risk': predicted_risk,
            'expected_risk': expected_risk,
            'risk_score': parsed_result['risk_score'] / 100.0,
            'detected_entities': parsed_result['detected_entities'],
            'explanation': parsed_result['explanation'],
            'domain': parsed_result['domain'],
            'processing_time': api_response.processing_time,
            'token_count': api_response.token_count,
            'cost': api_response.cost,
            'correct': is_correct,
            'error': False,
            'recommendations': parsed_result.get('recommendations', []),
            'raw_response': api_response.content
        }

    def get_cost_summary(self) -> Dict[str, Any]:
        """비용 요약 정보"""
        return {
            'total_cost': self.total_cost,
            'max_cost': self.max_cost,
            'remaining_budget': self.max_cost - self.total_cost,
            'request_count': self.request_count,
            'average_cost_per_request': self.total_cost / self.request_count if self.request_count > 0 else 0
        }

    def reset_cost_tracking(self):
        """비용 추적 리셋"""
        self.total_cost = 0.0
        self.request_count = 0
        self.logger.info("비용 추적이 리셋되었습니다.")

if __name__ == "__main__":
    # API 클라이언트 테스트
    from llm_configs import LLMConfigManager

    config_manager = LLMConfigManager()
    api_client = LLMAPIClient(max_cost=1.0)

    # 사용 가능한 모델 확인
    available_models = config_manager.get_available_models()
    if available_models:
        print(f"🤖 사용 가능한 모델: {available_models}")

        # 첫 번째 모델로 테스트
        model_name = available_models[0]
        config = config_manager.get_config(model_name)

        test_prompt = """
다음 텍스트의 개인정보 위험도를 분석해주세요:
"김철수(35세 남성)가 당뇨병 진단을 받았습니다."

JSON 형식으로 응답해주세요:
{
    "risk_score": 75,
    "risk_level": "HIGH",
    "detected_entities": ["이름", "나이", "성별", "질병"],
    "explanation": "개인정보와 의료정보 조합",
    "domain": "medical"
}
"""

        print(f"\n🧪 {model_name} 테스트 중...")
        result = api_client.analyze_text(
            text="김철수(35세 남성)가 당뇨병 진단을 받았습니다.",
            config=config,
            prompt=test_prompt,
            expected_risk="HIGH"
        )

        print(f"✅ 결과: {result}")
        print(f"💰 비용: ${result['cost']:.4f}")

    else:
        print("❌ 사용 가능한 모델이 없습니다.")