# Privacy Guard for LLM 🏥🔒

**AI 기반 의료 텍스트 비식별화 및 문맥적 개인정보 감지 시스템**

기존 비식별화 도구가 놓치는 문맥적/조합적 개인정보를 감지하고, 의료 데이터를 안전하게 보호하면서도 연구·분석에 활용할 수 있도록 돕는 지능형 마스킹 시스템입니다.

---

## 🆕 새로운 기능: 완전한 의료 텍스트 비식별화 파이프라인

### 🌟 주요 특징

- **🤖 학습된 NER 모델**: KoELECTRA 기반 한국어 의료 개체명 인식 + LoRA 파인튜닝 지원
- **📊 Copula 위험도 분석**: 통계적 모델을 통한 정교한 조합 위험도 계산
- **🔍 문맥적 분석**: 텍스트 전체 맥락을 고려한 지능형 위험도 조정
- **🎭 적응형 마스킹**: 위험도 기반 선택적 마스킹 실행
- **📈 상세한 분석 로그**: 마스킹 과정의 완전한 추적성

### 🏗️ 4단계 파이프라인 구조

```
📝 텍스트 입력
    ↓
🔍 1단계: 학습된 NER 모델
    ↓ (개체명 인식)
📊 2단계: Copula 위험도 분석
    ↓ (통계적 위험도 계산)
🔄 3단계: 문맥적 위험 분석
    ↓ (조합/키워드 기반 조정)
🎭 4단계: 마스킹 실행
    ↓
✅ 비식별화된 텍스트 출력
```

---

## 🎯 프로젝트 목표

- **문맥 이해**: 같은 정보라도 상황에 따른 위험도 차등 판단
- **조합 위험도**: 개별로는 안전하지만 조합하면 위험한 정보 감지
- **도메인 특화**: 의료, 기업, 기술 분야별 민감정보 패턴 학습
- **실시간 필터링**: ChatGPT, Claude 등 Public LLM 사용 시 사전 차단

---

## 🚀 Quick Start

### 1. 새로운 파이프라인 사용법

```python
from masking_module import CompleteMedicalDeidentificationPipeline

# 파이프라인 초기화
pipeline = CompleteMedicalDeidentificationPipeline(
    model_path="ner-koelectra-lora-merged",  # 학습된 모델 경로
    threshold=50,  # 마스킹 임계값
    use_contextual_analysis=True
)

# 텍스트 처리
text = "김철수씨가 2023년 10월에 서울대병원에서 간암 진단을 받았습니다."
result = pipeline.process(text)

# 결과 확인
print(f"원문: {result.original_text}")
print(f"마스킹: {result.masked_text}")
print(f"통계: {result.masked_entities}/{result.total_entities} 개체 마스킹")
```

## 🏗️ 프로젝트 구조

```
privacy_guard_project/
├── masking_module.py              # 🆕 완전한 비식별화 파이프라인
├── masking_module.ipynb           # 🆕 파이프라인 노트북 버전
├── fine_tuning_test.ipynb         # 🆕 모델 파인튜닝 테스트
├── Privacy_test_ipynb.ipynb       # 프라이버시 모델 테스트
├── compare_all.py                 # 전체 모델 성능 비교
├── run_all_tests.bat             # 전체 테스트 실행
│
├── envs/                          # 모델별 가상환경
│   ├── bert_env/                 # BERT 테스트 환경
│   ├── roberta_env/              # RoBERTa 테스트 환경
│   ├── kobert_env/               # KoBERT 테스트 환경 (한국어 특화)
│   ├── koelectra_env/            # KoELECTRA 테스트 환경
│   ├── existing_tools_env/       # 기존 도구 비교 환경
│   ├── kogpt_env/                # KoGPT 테스트 환경 (생성형)
│   ├── kcelectra_env/            # KcELECTRA 테스트 환경 (한국어 개선)
│   └── deberta_env/              # DeBERTa v3 테스트 환경 (최신)
│  
├── tests/                         # 모델별 테스트 스크립트
│   ├── common_test_cases.py      # 공통 테스트 케이스
│   ├── llm_api_client.py         # LLM API 클라이언트
│   ├── prompt_templates.py       # 프롬프트 템플릿
│   ├── result_analyzer.py        # 결과 분석기
│   ├── test_*.py                 # 각 모델별 테스트 스크립트
│   └── results/                  # 테스트 결과 저장
│   
├── requirements/                  # 환경별 requirements.txt
└── docs/                         # 문서
```

---

## 🆕 새로운 파이프라인 핵심 컴포넌트

### 1. TrainedNERModel
- **KoELECTRA 기반**: 한국어 의료 개체명 인식 특화
- **LoRA 지원**: Parameter-Efficient Fine-tuning
- **더미 모델**: 학습된 모델이 없어도 테스트 가능

### 2. CopulaRiskAnalyzer
- **통계적 모델링**: Gaussian Copula를 이용한 조합 위험도 계산
- **의료 특화 피처**: 병원, 질병, 날짜 간 상관관계 분석
- **희귀도 기반**: 드물수록 높은 위험도 부여

### 3. ContextualRiskAnalyzer
- **조합 패턴**: (개인명 + 병원 + 날짜) 등 고위험 조합 탐지
- **의료 키워드**: 진단, 수술, 응급 등 상황별 위험도 조정
- **문맥 가중치**: 최대 2.0배까지 위험도 증가

### 4. MaskingExecutor
- **임계값 기반**: 설정한 위험도 이상만 마스킹
- **타입별 마스킹**: [PERSON], [HOSPITAL], [DATE] 등 의미있는 마스킹
- **완전한 추적**: 마스킹 과정 상세 로그 제공

---

## 🧪 테스트 케이스 및 성능

### 의료 특화 테스트 케이스

```python
test_cases = [
    "김철수씨가 2023년 10월에 서울대병원에서 간암 진단을 받았습니다.",
    "박영희(010-1234-5678)는 삼성서울병원에서 수술을 받았다.",
    "환자는 내일 검사를 받을 예정입니다.",
    "이순신 교수는 연세의료원에서 백혈병 연구를 하고 있다."
]
```

### 예상 출력 결과

```
원문: 김철수씨가 2023년 10월에 서울대병원에서 간암 진단을 받았습니다.
마스킹: [PERSON]씨가 [DATE]에 [HOSPITAL]에서 [DISEASE] 진단을 받았습니다.
통계: 4/4 개체 마스킹

마스킹 상세 로그:
1. '김철수' → [PERSON] (위험도: 100)
2. '2023년 10월' → [DATE] (위험도: 78)
3. '서울대병원' → [HOSPITAL] (위험도: 65)
4. '간암' → [DISEASE] (위험도: 52)
```

---

## 📊 모델 성능 비교 (전체 9개 모델)

### 🆕 최신 추가 모델들 (Phase 2 완료 ✅)
| 모델 | 한국어 지원 | 문맥 이해 | 처리 속도 | 메모리 사용량 | 특화 분야 |
|------|-------------|-----------|-----------|-------------|--------------| 
| **🆕 KcELECTRA** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 한국어 개선 |
| **🆕 DeBERTa v3** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 최신 아키텍처 |

### 기본 모델들 (Phase 1 완료 ✅)
| 모델 | 한국어 지원 | 문맥 이해 | 처리 속도 | 메모리 사용량 | 특화 분야 |
|------|-------------|-----------|-----------|-------------|--------------| 
| **KoBERT** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 기본 NLU |
| **BERT** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 영어 베이스라인 |
| **RoBERTa** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 개선된 학습 |
| **KoELECTRA** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 효율성 |
| **기존도구** | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 규칙 기반 |
| **sk-KoGPT2** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | 생성형 (부적합) |

---

## 🎨 기존 솔루션 vs 우리 접근법

### 기존 도구들 (Presidio, spaCy 등)
- ✅ 개별 개체 인식 우수
- ❌ 조합 위험도 판단 부족
- ❌ 문맥적 민감도 차이 미고려
- ❌ 도메인별 특화 부족
- ❌ 한국어 문맥 이해 제한적

### 🆕 우리 시스템의 강점
- ✅ **완전한 파이프라인**: 4단계 체계적 비식별화 프로세스
- ✅ **학습된 모델 활용**: KoELECTRA + LoRA 파인튜닝 지원
- ✅ **통계적 위험 분석**: Copula 모델 기반 조합 위험도 계산
- ✅ **문맥적 위험도**: 같은 정보, 다른 상황에서 위험도 차별화
- ✅ **의료 도메인 특화**: 실제 병원에서 사용 가능한 수준
- ✅ **완전한 추적성**: 마스킹 과정 상세 로그 제공

---

## 🧪 사용법 가이드

### 1. 새로운 파이프라인 테스트

```python
# 1. 기본 사용법
from masking_module import CompleteMedicalDeidentificationPipeline

pipeline = CompleteMedicalDeidentificationPipeline()
result = pipeline.process("김철수씨가 서울대병원에서 진료받았습니다.")
pipeline.print_detailed_analysis(result)

# 2. 고급 설정
pipeline = CompleteMedicalDeidentificationPipeline(
    model_path="./your-trained-model",  # 학습된 모델 경로
    threshold=30,                       # 낮은 임계값 (더 많이 마스킹)
    use_contextual_analysis=True        # 문맥 분석 활성화
)

# 3. 배치 처리
texts = ["환자 정보 1", "환자 정보 2", "환자 정보 3"]
for text in texts:
    result = pipeline.process(text, verbose=False)
    print(f"{text} → {result.masked_text}")
```

### 2. 기존 모델별 개별 테스트

#### 🆕 신규 모델 테스트
```cmd
# KcELECTRA 테스트 (한국어 특화)
cd envs\kcelectra_env
call Scripts\activate.bat
python ..\..\tests\test_kcelectra.py

# DeBERTa v3 테스트 (최신 아키텍처)
cd envs\deberta_env
call Scripts\activate.bat
python ..\..\tests\test_deberta.py
```

#### 기존 모델 테스트 ✅
```cmd
# KoBERT 테스트
cd envs\kobert_env
call Scripts\activate.bat
python ..\..\tests\test_kobert.py

# 전체 모델 비교
python compare_all.py
```

---

## 🎯 추천 사용 시나리오

### **🥇 의료 기관용 (최고 성능)**
```python
pipeline = CompleteMedicalDeidentificationPipeline(
    model_path="ner-koelectra-medical-finetuned",
    threshold=30,  # 보수적 마스킹
    use_contextual_analysis=True
)
```

### **⚡ 실시간 처리용 (빠른 속도)**
```python
pipeline = CompleteMedicalDeidentificationPipeline(
    model_path="dummy",  # 더미 모델 사용
    threshold=70,  # 높은 임계값
    use_contextual_analysis=False
)
```

### **🎯 연구용 (정확도 중심)**
```python
pipeline = CompleteMedicalDeidentificationPipeline(
    model_path="ner-koelectra-research-optimized",
    threshold=40,
    use_contextual_analysis=True
)
```

---

## 🆕 새로운 모델 추가 가이드

1. `envs/` 에 새 가상환경 생성
2. `requirements/` 에 requirements 파일 추가
3. `tests/` 에 테스트 스크립트 작성
4. `run_all_tests.bat` 에 테스트 추가
5. README.md 의 모델 비교표에 추가

---

## 📝 개발 로드맵

### ✅ 완료된 기능
- [x] 기본 9개 모델 테스트 환경
- [x] 완전한 4단계 비식별화 파이프라인
- [x] KoELECTRA + LoRA 파인튜닝 지원
- [x] Copula 기반 위험도 분석
- [x] 문맥적 위험도 조정
- [x] 의료 도메인 특화 마스킹

---

## 🏆 핵심 차별화 포인트

- **🆕 완전한 파이프라인**: 4단계 체계적 의료 텍스트 비식별화
- **🆕 학습된 모델 통합**: KoELECTRA + LoRA 파인튜닝으로 의료 특화
- **🆕 통계적 위험 분석**: Copula 모델로 조합 위험도 정확 계산
- **🆕 문맥적 분석**: 의료 상황별 키워드와 조합 패턴 인식
- **9개 모델 통합**: 기본 5개 + 한국어 특화 4개 모델로 포괄적 분석
- **실시간 필터링**: Public LLM 사용 시 사전 차단 시스템
- **완전한 추적성**: 마스킹 과정 상세 로그 및 분석 결과

---
**Privacy Guard LLM**으로 안전하고 스마트한 의료 데이터 활용을 시작하세요! 🚀