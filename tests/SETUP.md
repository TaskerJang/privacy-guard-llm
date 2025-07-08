# Privacy Guard LLM - 설치 및 실행 가이드

## 🚀 빠른 시작 (Quick Start)

### 1. 환경 설정

```bash
# 1. 리포지토리 클론
git clone https://github.com/TaskerJang/privacy-guard-llm.git
cd privacy-guard-llm

# 2. 가상환경 생성 (권장)
python -m venv envs/prompt_classifier_env
envs\prompt_classifier_env\Scripts\activate

# 3. 의존성 설치
pip install -r requirements/prompt_classifier_requirements.txt
```

### 2. API 키 설정

`.env` 파일을 생성하고 API 키를 설정합니다:

```bash
# .env 파일 생성
cp .env.example .env

# 사용할 API 키 설정 (하나 이상 필요)
OPENAI_API_KEY=sk-proj-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here
COHERE_API_KEY=your-cohere-api-key-here
```

### 3. 실행

```bash
# 빠른 테스트 (샘플 케이스 5개)
python tests/run_prompt_classifier.py --mode sample

# 정밀 비교 (GPT-4.1, Claude-4, Gemini-2.5-Pro)
python tests/run_prompt_classifier.py --mode precision

# 전체 테스트
python tests/run_prompt_classifier.py --mode all --max-cost 10.0
```

## 📋 상세 설정 가이드

### API 키 발급 방법

#### 1. OpenAI API 키
- https://platform.openai.com/api-keys 접속
- "Create new secret key" 클릭
- 생성된 키를 `.env` 파일에 저장

#### 2. Anthropic API 키
- https://console.anthropic.com/ 접속
- "Get API Keys" 메뉴에서 키 생성
- 생성된 키를 `.env` 파일에 저장

#### 3. Google API 키
- https://console.cloud.google.com/ 접속
- "APIs & Services" → "Credentials" 메뉴
- "Create Credentials" → "API key" 선택
- Gemini API 활성화 후 키 사용

#### 4. Cohere API 키
- https://dashboard.cohere.ai/ 접속
- "API Keys" 메뉴에서 키 생성
- 생성된 키를 `.env` 파일에 저장

### 실행 모드 옵션

```bash
# 모든 옵션 보기
python tests/run_prompt_classifier.py --help

# 실행 모드
--mode sample      # 샘플 테스트 (5개 케이스)
--mode precision   # 정밀 비교 (고성능 모델)
--mode speed       # 속도 테스트 (빠른 모델)
--mode cost        # 비용 효율 (저렴한 모델)
--mode all         # 전체 모델 테스트

# 비용 설정
--max-cost 5.0     # 최대 비용 한도 (달러)

# 결과 저장
--no-save          # 결과 저장 안함
```

## 🔧 고급 설정

### 1. 로깅 설정

```bash
# 환경 변수로 로그 레벨 설정
export LOG_LEVEL=DEBUG
export LOG_FILE=logs/debug.log

# 또는 .env 파일에 추가
LOG_LEVEL=INFO
LOG_FILE=logs/privacy_guard.log
```

### 2. 성능 최적화

```bash
# 동시 요청 수 제한
MAX_CONCURRENT_REQUESTS=3

# 요청 타임아웃 설정
REQUEST_TIMEOUT=30

# 재시도 횟수
RETRY_ATTEMPTS=3
```

### 3. 테스트 케이스 커스터마이징

`tests/test_cases.py` 파일을 편집하여 새로운 테스트 케이스를 추가할 수 있습니다:

```python
# 새로운 테스트 케이스 추가
new_case = {
    'text': '당신의 테스트 텍스트',
    'expected_risk': 'HIGH',
    'domain': 'medical',
    'description': '테스트 케이스 설명'
}
```

## 📊 결과 분석

### 결과 파일 위치
- `results/final_[mode]_[timestamp].json` - 원시 결과 데이터
- `results/report_[mode]_[timestamp].md` - 분석 보고서
- `logs/` - 실행 로그

### 결과 해석

#### 성능 지표
- **정확도**: 올바른 예측 비율
- **처리시간**: 평균 응답 시간
- **비용**: 실제 발생 비용
- **오류율**: API 호출 실패율

#### 모델 선택 기준
- **정확도 우선**: 최고 정확도 모델
- **속도 우선**: 가장 빠른 모델
- **비용 효율**: 정확도 대비 비용이 낮은 모델

## 🐛 문제 해결

### 일반적인 오류

#### 1. API 키 오류
```bash
# 오류: "API key not found"
# 해결: .env 파일에 올바른 API 키 설정 확인

# API 키 테스트
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

#### 2. 모듈 import 오류
```bash
# 오류: "ModuleNotFoundError"
# 해결: 의존성 재설치

pip install -r requirements/prompt_classifier_requirements.txt
```

#### 3. 비용 한도 초과
```bash
# 오류: "비용 한도 초과"
# 해결: 비용 한도 증가 또는 샘플 모드 사용

python tests/run_prompt_classifier.py --mode sample --max-cost 1.0
```

#### 4. API 응답 오류
```bash
# 오류: "API 호출 실패"
# 해결: 네트워크 연결 확인 및 API 키 권한 확인

# 연결 테스트
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

### 성능 최적화 팁

1. **적절한 모델 선택**
    - 빠른 테스트: `--mode speed`
    - 정확한 분석: `--mode precision`
    - 비용 절약: `--mode cost`

2. **배치 처리**
    - 대량 테스트시 샘플로 먼저 확인
    - 비용 한도를 점진적으로 증가

3. **결과 모니터링**
    - 실시간 비용 추적
    - 중간 결과 저장 활용

## 🔄 업데이트 및 유지보수

### 정기 업데이트
```bash
# 최신 코드 가져오기
git pull origin main

# 의존성 업데이트
pip install -r requirements/prompt_classifier_requirements.txt --upgrade

# 새로운 모델 추가 확인
python tests/llm_configs.py
```

### 백업 및 복원
```bash
# 결과 백업
cp -r results/ backup/results_$(date +%Y%m%d)/

# 설정 백업
cp .env backup/env_$(date +%Y%m%d).txt
```

## 📞 지원 및 문의

- **GitHub Issues**: https://github.com/TaskerJang/privacy-guard-llm/issues
- **문서**: README.md 및 코드 내 주석 참고
- **실험 결과 공유**: `results/` 폴더의 보고서 참고

---

## 🎯 다음 단계

1. **기본 실행**: `--mode sample`로 빠른 테스트
2. **성능 비교**: `--mode precision`로 상세 분석
3. **실제 적용**: 최고 성능 모델 선택
4. **시스템 통합**: API 클라이언트 코드 활용
5. **모니터링**: 실시간 성능 추적 시스템 구축

성공적인 실험을 위해 단계별로 진행하시기 바랍니다! 🚀