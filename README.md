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
│   └── existing_tools_env/        # 기존 도구 비교 환경
├── tests/                         # 모델별 테스트 스크립트
│   ├── test_kobert.py            # KoBERT 개인정보 감지 테스트
│   ├── test_bert.py              # BERT 테스트
│   ├── test_roberta.py           # RoBERTa 테스트
│   ├── test_koelectra.py         # KoELECTRA 테스트
│   └── test_existing.py          # 기존 도구 성능 비교
├── results/                       # 테스트 결과 저장
├── requirements/                  # 환경별 requirements.txt
├── src/                          # 메인 소스 코드 (개발 예정)
└── docs/                         # 문서
```

## 🚀 Quick Start

### 1. 환경 설정

```cmd
# 프로젝트 구조 생성
create_project_structure.bat

# 모든 가상환경 자동 설치
setup_environments.bat
```

### 2. 개별 모델 테스트

```cmd
# KoBERT 테스트
cd envs\kobert_env
call Scripts\activate.bat
python ..\..\tests\test_kobert.py
```

### 3. 전체 모델 비교

```cmd
# 모든 모델 자동 테스트
run_all_tests.bat
```

## 🧪 테스트 케이스

### 기본 개인정보
- "김철수, 010-1234-5678, kim@example.com"

### 조합형 위험정보
- "35세 남성 의사이고 강남구에 거주"
- "환자 김철수가 어제 수술받았음"

### 도메인 특화 민감정보
- **의료**: "혈당 350, 케톤산증, 40대 남성"
- **기업**: "Phoenix 프로젝트 예산 50억"
- **기술**: "API 키 sk-abc123, DB 192.168.1.100"

## 📊 모델 성능 비교

| 모델 | 한국어 지원 | 문맥 이해 | 처리 속도 | 메모리 사용량 |
|------|-------------|-----------|-----------|-------------|
| KoBERT | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| BERT | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| RoBERTa | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| KoELECTRA | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

*(테스트 진행 중)*

## 🎨 기존 솔루션 vs 우리 접근법

### 기존 도구들 (Presidio, spaCy 등)
- ✅ 개별 개체 인식 우수
- ❌ 조합 위험도 판단 부족
- ❌ 문맥적 민감도 차이 미고려
- ❌ 도메인별 특화 부족

### 우리 솔루션
- ✅ 문맥 기반 위험도 판단
- ✅ 조합 정보 위험성 계산
- ✅ 도메인별 민감정보 패턴
- ✅ 실시간 브라우저 확장프로그램

## 🔮 로드맵

### Phase 1 (현재): 모델 분석
- [x] 프로젝트 구조 설정
- [x] 가상환경별 모델 테스트 환경 구축
- [ ] KoBERT 성능 분석
- [ ] 기존 도구들과 성능 비교

### Phase 2: 핵심 알고리즘 개발
- [ ] 조합 위험도 계산 알고리즘
- [ ] 도메인별 민감정보 패턴 학습
- [ ] 문맥적 위험도 가중치 시스템

### Phase 3: 프로토타입 구현
- [ ] Chrome 확장프로그램 개발
- [ ] ChatGPT/Claude 연동
- [ ] 실시간 필터링 시스템

## 🤝 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

Apache License 2.0 - 자세한 내용은 [LICENSE](LICENSE) 파일 참고

## 📞 Contact

Project Link: [https://github.com/TaskerJang/privacy-guard-llm](https://github.com/TaskerJang/privacy-guard-llm)

---


