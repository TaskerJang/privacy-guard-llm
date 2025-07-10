# Privacy Guard for LLM

기존 비식별화 도구가 놓치는 문맥적/조합적 개인정보를 감지하는 Public LLM 필터링 시스템

## 🎯 프로젝트 목표

- **문맥 이해**: 같은 정보라도 상황에 따른 위험도 차등 판단
- **조합 위험도**: 개별로는 안전하지만 조합하면 위험한 정보 감지
- **도메인 특화**: 의료, 기업, 기술 분야별 민감정보 패턴 학습
- **실시간 필터링**: ChatGPT, Claude 등 Public LLM 사용 시 사전 차단

## 🏗️ 프로젝트 구조

```
privacy_guard_project/
├── envs/                           # 모델별 가상환경
│   ├── bert_env/                  # BERT 테스트 환경
│   ├── roberta_env/               # RoBERTa 테스트 환경
│   ├── kobert_env/                # KoBERT 테스트 환경 (한국어 특화)
│   ├── koelectra_env/             # KoELECTRA 테스트 환경
│   ├── existing_tools_env/        # 기존 도구 비교 환경
│   ├── kogpt_env/                 # KoGPT 테스트 환경 (생성형)
│   ├── kcelectra_env/             # 🆕 KcELECTRA 테스트 환경 (한국어 개선)
│   └── deberta_env/               # 🆕 DeBERTa v3 테스트 환경 (최신)
│  
├── tests/                         # 모델별 테스트 스크립트
│   ├── common_test_cases.py       # 공통 테스트 케이스
│   ├── test_bert.py              # BERT 테스트
│   ├── test_roberta.py           # RoBERTa 테스트
│   ├── test_kobert.py            # KoBERT 개인정보 감지 테스트
│   ├── test_koelectra.py         # KoELECTRA 테스트
│   ├── test_existing.py          # 기존 도구 성능 비교
│   ├── test_kogpt.py             # KoGPT 생성형 모델 테스트
│   ├── test_kcelectra.py         # 🆕 KcELECTRA 한국어 특화 테스트
│   └── test_deberta.py           # 🆕 DeBERTa v3 고급 문맥 이해 테스트
│   
├── requirements/                  # 환경별 requirements.txt
│   ├── bert_requirements.txt
│   ├── roberta_requirements.txt
│   ├── kobert_requirements.txt
│   ├── koelectra_requirements.txt
│   ├── existing_requirements.txt
│   ├── kogpt_requirements.txt
│   ├── kcelectra_requirements.txt # 🆕 KcELECTRA 의존성
│   └── deberta_requirements.txt   # 🆕 DeBERTa v3 의존성
│   
├── results/                       # 테스트 결과 저장
├── src/                          # 메인 소스 코드 (개발 예정)
└── docs/                         # 문서
```

## 🚀 Quick Start

### 1. 환경 설정

```cmd
# 프로젝트 구조 생성
create_project_structure.bat

# 기본 5개 모델 환경 설치
setup_environments.bat

# 한국어 특화 4개 모델 추가 설치 (🆕 업데이트)
setup_korean_models.bat
```

### 2. 🆕 새로운 모델 테스트

```cmd
# KcELECTRA 테스트 (한국어 특화 개선)
cd envs\kcelectra_env
call Scripts\activate.bat
python ..\..\tests\test_kcelectra.py

# DeBERTa v3 테스트 (최신 아키텍처)
cd envs\deberta_env
call Scripts\activate.bat  
python ..\..\tests\test_deberta.py
```

### 3. 기존 모델 테스트

```cmd
# 기본 KoBERT 테스트
cd envs\kobert_env
call Scripts\activate.bat
python ..\..\tests\test_kobert.py

# 생성형 KoGPT 테스트
cd envs\kogpt_env
call Scripts\activate.bat  
python ..\..\tests\test_kogpt.py
```

## 🧪 테스트 케이스

### 기본 개인정보
- "김철수, 010-1234-5678, kim@example.com"

### 조합형 위험정보
- "35세 남성 의사이고 강남구에 거주"
- "환자 김철수가 어제 수술받았음"

### 🆕 의료 특화 문맥 테스트 (신규 모델용)
- **조합 위험**: "김XX(47세 여성)은 2023년 10월 13일 분당서울대병원에서 위염 진단"
- **응급 상황**: "지난주 119 부르고 성남시 OO아파트 앞에서 실신해서 응급실"
- **연구 데이터**: "2023년 1월부터 서울시립병원에서 치료받은 65세 이상 폐렴 환자 1,240명"

### 문맥적 위험정보 (한국어 특화)
- "김철수 환자분" vs "김철수 교수님" (역할 구분)
- "박영희가 말씀하신 대로" vs "박영희 님께서" (존댓말 맥락)
- "그 분이 30대 후반이시고" (간접 표현)

### 도메인 특화 민감정보
- **의료**: "혈당 350, 케톤산증, 40대 남성"
- **기업**: "Phoenix 프로젝트 예산 50억"
- **기술**: "API 키 sk-abc123, DB 192.168.1.100"

## 📊 모델 성능 비교 (🆕 9개 모델)

### 📈 최신 추가 모델들 (Phase 2 완료 ✅)
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

## 🆕 신규 모델 특징

### **KcELECTRA** (beomi/KcELECTRA-base)
- ✅ KoELECTRA 개선 버전
- ✅ 한국어 의료 텍스트 특화 최적화
- ✅ 조합형 개인정보 위험도 계산
- ✅ 빠른 처리 속도 + 높은 정확도

### **DeBERTa v3 Korean** (team-lucid/deberta-v3-base-korean)
- ✅ 최신 DeBERTa v3 아키텍처
- ✅ 복잡한 문맥 이해 (문맥적 위험도 차별화)
- ✅ 준식별자 조합 패턴 인식
- ✅ 재식별 위험 고급 분석

## 🎨 기존 솔루션 vs 우리 접근법

### 기존 도구들 (Presidio, spaCy 등)
- ✅ 개별 개체 인식 우수
- ❌ 조합 위험도 판단 부족
- ❌ 문맥적 민감도 차이 미고려
- ❌ 도메인별 특화 부족
- ❌ 한국어 문맥 이해 제한적

### 🆕 우리 시스템의 강점
- ✅ **9개 모델 통합**: 기본 5개 + 한국어 특화 4개 모델
- ✅ **문맥적 위험도**: 같은 정보, 다른 상황에서 위험도 차별화
- ✅ **조합 패턴 인식**: 준식별자들의 위험한 조합 자동 탐지
- ✅ **의료 도메인 특화**: 실제 병원에서 사용 가능한 수준

## 🧪 모델별 개별 테스트 가이드

### 🆕 신규 모델 테스트

#### 1. KcELECTRA 테스트 (한국어 특화)
```cmd
cd envs\kcelectra_env
call Scripts\activate.bat
python ..\..\tests\test_kcelectra.py
call Scripts\deactivate.bat
cd ..\..
```

#### 2. DeBERTa v3 테스트 (최신 아키텍처)
```cmd
cd envs\deberta_env
call Scripts\activate.bat
python ..\..\tests\test_deberta.py
call Scripts\deactivate.bat
cd ..\..
```

### 기존 모델 테스트 ✅

#### 3. KoBERT 테스트
```cmd
cd envs\kobert_env
call Scripts\activate.bat
python ..\..\tests\test_kobert.py
call Scripts\deactivate.bat
cd ..\..
```

#### 4. BERT 테스트
```cmd
cd envs\bert_env
call Scripts\activate.bat
python ..\..\tests\test_bert.py
call Scripts\deactivate.bat
cd ..\..
```

#### 5. RoBERTa 테스트
```cmd
cd envs\roberta_env
call Scripts\activate.bat
python ..\..\tests\test_roberta.py
call Scripts\deactivate.bat
cd ..\..
```

#### 6. KoELECTRA 테스트
```cmd
cd envs\koelectra_env
call Scripts\activate.bat
python ..\..\tests\test_koelectra.py
call Scripts\deactivate.bat
cd ..\..
```

#### 7. 기존 도구들 테스트
```cmd
cd envs\existing_tools_env
call Scripts\activate.bat
python ..\..\tests\test_existing.py
call Scripts\deactivate.bat
cd ..\..
```

#### 8. KoGPT 테스트 (생성형 이해도)
```cmd
cd envs\kogpt_env
call Scripts\activate.bat
python ..\..\tests\test_kogpt.py
call Scripts\deactivate.bat
cd ..\..
```

### 통합 분석
```cmd
# 기본 7개 모델 비교
python compare_basic.py

# 한국어 특화 4개 모델 비교  
python compare_korean.py

# 🆕 전체 9개 모델 종합 비교
python compare_all.py
```

### 결과 확인
```cmd
# 기본 모델 결과
type results\kobert_results.txt
type results\bert_results.txt
type results\roberta_results.txt
type results\koelectra_results.txt
type results\existing_results.txt
type results\kogpt_results.txt

# 🆕 신규 모델 결과
type results\kcelectra_results.json
type results\deberta_results.json
```

## 🆕 새로운 모델 추가 가이드
1. `envs/` 에 새 가상환경 생성
2. `requirements/` 에 requirements 파일 추가
3. `tests/` 에 테스트 스크립트 작성
4. `run_all_tests.bat` 에 테스트 추가
5. README.md 의 모델 비교표에 추가

## 📝 License

Apache License 2.0 - 자세한 내용은 [LICENSE](LICENSE) 파일 참고

## 🏆 핵심 차별화 포인트

- **🆕 9개 모델 통합**: 기본 5개 + 한국어 특화 4개 모델로 포괄적 분석
- **🆕 최신 아키텍처**: DeBERTa v3로 복잡한 문맥 이해
- **🆕 한국어 개선**: KcELECTRA로 한국어 특화 성능 향상
- **생성형 모델 활용**: KoGPT로 위험도 설명 생성 가능
- **문맥 유사성 분석**: 역할 구분 및 간접 표현 감지
- **한국어 문법 특성**: 조사, 높임법, 존댓말 맥락 반영
- **실시간 필터링**: Public LLM 사용 시 사전 차단 시스템

## 🎯 추천 모델 조합

### **🥇 최고 성능 조합** (권장)
```
1단계: KcELECTRA (빠른 1차 한국어 필터링)
2단계: DeBERTa v3 (복잡한 문맥 이해)  
3단계: KoBERT (개체명 정확 인식)
4단계: KoGPT (설명 생성 및 최종 판단)
```

### **⚡ 빠른 처리 조합**
```
KcELECTRA + KoELECTRA (속도 중심)
```

### **🎯 정확도 중심 조합**
```
DeBERTa v3 + KoBERT (정확도 중심)
```