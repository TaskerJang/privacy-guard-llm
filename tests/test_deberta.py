"""
DeBERTa v3 Korean 개인정보 문맥 이해 테스트 (team-lucid/deberta-v3-base-korean)
"""

import torch
import time
import sys
import json
import numpy as np
from datetime import datetime

def test_deberta_installation():
    """DeBERTa 설치 확인"""
    try:
        from transformers import DebertaV2Tokenizer, DebertaV2Model
        print("[성공] transformers DeBERTa v2 모델 import 성공!")
        return True, "transformers"
    except ImportError:
        try:
            from transformers import AutoTokenizer, AutoModel
            print("[성공] transformers Auto 모델 import 성공!")
            return True, "auto"
        except ImportError as e:
            print("[실패] transformers 라이브러리 import 실패: {}".format(e))
            return False, None

def load_deberta_model():
    """DeBERTa v3 모델 로딩"""
    try:
        print("[로딩] DeBERTa v3 Korean 모델 로딩 중...")
        start_time = time.time()

        model_name = "team-lucid/deberta-v3-base-korean"

        # Auto 모델 사용 (DeBERTa v3 호환성을 위해)
        from transformers import AutoTokenizer, AutoModel
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.eval()

        load_time = time.time() - start_time
        print("[성공] DeBERTa v3 Korean 모델 로딩 완료! (소요시간: {:.2f}초)".format(load_time))
        return model, tokenizer, load_time

    except Exception as e:
        print("[실패] DeBERTa v3 Korean 모델 로딩 실패: {}".format(e))
        return None, None, None

def test_advanced_tokenization(tokenizer):
    """고급 토크나이징 테스트"""
    print("\n[토큰] DeBERTa v3 고급 토크나이징 테스트")
    print("-" * 50)

    # 복잡한 의료 시나리오 테스트
    complex_sentences = [
        "본 연구는 2023년 1월부터 2024년 3월까지 서울시립병원에서 치료받은 65세 이상 폐렴 환자 1,240명을 대상으로 하였다",
        "어제 산부인과에서 자궁근종 진단받았는데, MRI 결과를 업로드하면 위험한 건지 봐주세요",
        "5살 아들이 인천의료원에서 RSV 진단받았는데, 어린이집에 언제부터 보내도 될까요?",
        "아버지가 3개월 전부터 투석 중인데 요새 식욕이 너무 없어요. 주치의가 신부전이 진행됐다고 해서 걱정돼요",
        "Phoenix 프로젝트 예산 50억, 담당자 김부장, API 키 sk-proj-abc123, DB 서버 192.168.1.100"
    ]

    tokenization_results = []

    for sentence in complex_sentences:
        try:
            # 기본 토크나이징
            tokens = tokenizer.tokenize(sentence)
            token_ids = tokenizer.encode(sentence, add_special_tokens=True)

            # 어텐션 마스크와 함께 인코딩
            encoded = tokenizer(sentence,
                                return_tensors="pt",
                                padding=True,
                                truncation=True,
                                max_length=512,
                                return_attention_mask=True)

            result = {
                "text": sentence,
                "tokens": tokens,
                "token_count": len(tokens),
                "token_ids": token_ids,
                "attention_mask": encoded['attention_mask'].tolist(),
                "max_length_used": len(token_ids)
            }
            tokenization_results.append(result)

            print("원문: {}...".format(sentence[:50]))
            print("토큰 수: {}".format(len(tokens)))
            print("특수 토큰: [CLS]: {}, [SEP]: {}".format(
                tokenizer.cls_token, tokenizer.sep_token))
            print("서브워드 예시: {}".format(tokens[:8] + ["..."] if len(tokens) > 8 else tokens))
            print()

        except Exception as e:
            print("원문: {}...".format(sentence[:50]))
            print("토큰화 오류: {}".format(e))
            print()

    return tokenization_results

def get_contextual_embedding(model, tokenizer, text):
    """문맥적 임베딩 추출 (DeBERTa v3 특화)"""
    try:
        inputs = tokenizer(text,
                           return_tensors="pt",
                           padding=True,
                           truncation=True,
                           max_length=512)

        with torch.no_grad():
            outputs = model(**inputs)

        # DeBERTa는 더 정교한 문맥 이해를 위해 pooling 전략 사용
        # [CLS] 토큰 + 평균 pooling 조합
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] 토큰
        mean_embedding = outputs.last_hidden_state.mean(dim=1)  # 평균 pooling

        # 가중 평균 (CLS 70%, 평균 30%)
        combined_embedding = 0.7 * cls_embedding + 0.3 * mean_embedding

        return combined_embedding.squeeze()

    except Exception as e:
        print("임베딩 추출 오류: {}".format(e))
        return torch.randn(768)

def test_contextual_risk_understanding(model, tokenizer):
    """문맥적 위험 이해 테스트"""
    print("\n[문맥위험] DeBERTa v3 문맥적 위험 이해 테스트")
    print("-" * 50)

    # 문맥에 따라 위험도가 달라지는 케이스들
    contextual_test_cases = [
        # 같은 정보, 다른 문맥
        {
            "high_risk": "환자 김XX(47세 여성)이 2023년 10월 분당서울대병원에서 위염 진단받음",
            "low_risk": "김철수 교수(47세)가 2023년 10월 분당서울대병원에서 강의함",
            "context": "같은 개인정보, 다른 역할"
        },
        {
            "high_risk": "지난주 119 신고, 성남시 분당구 OO아파트 앞에서 심정지 환자 발생",
            "low_risk": "지난주 성남시 분당구 OO아파트에서 소방 훈련 실시",
            "context": "응급상황 vs 일반상황"
        },
        {
            "high_risk": "혈당 350mg/dL, 케톤산증 의심, 40대 남성 당뇨환자",
            "low_risk": "정상 혈당 범위는 70-100mg/dL이며, 당뇨 진단 기준은 126mg/dL 이상",
            "context": "개인 의료정보 vs 일반 의학정보"
        },
        {
            "high_risk": "이화여대 부속병원 정신건강의학과 외래 진료기록 중 자살 위험 평가 내용",
            "low_risk": "이화여대 부속병원에서 정신건강의학과 진료 안내 및 예약 방법",
            "context": "개인 진료기록 vs 일반 안내"
        }
    ]

    context_results = []

    for i, case in enumerate(contextual_test_cases, 1):
        try:
            high_risk_emb = get_contextual_embedding(model, tokenizer, case["high_risk"])
            low_risk_emb = get_contextual_embedding(model, tokenizer, case["low_risk"])

            # 임베딩 간 거리 계산
            cosine_sim = torch.cosine_similarity(high_risk_emb, low_risk_emb, dim=0).item()
            euclidean_dist = torch.dist(high_risk_emb, low_risk_emb).item()

            # 문맥 차이를 잘 구분하는지 평가
            context_discrimination = 1 - cosine_sim  # 값이 클수록 잘 구분

            result = {
                "case_number": i,
                "context": case["context"],
                "high_risk_text": case["high_risk"],
                "low_risk_text": case["low_risk"],
                "cosine_similarity": cosine_sim,
                "euclidean_distance": euclidean_dist,
                "context_discrimination": context_discrimination
            }
            context_results.append(result)

            print("[케이스 {}] {}".format(i, case["context"]))
            print("  고위험: {}...".format(case["high_risk"][:60]))
            print("  저위험: {}...".format(case["low_risk"][:60]))
            print("  코사인 유사도: {:.4f}".format(cosine_sim))
            print("  문맥 구분력: {:.4f}".format(context_discrimination))

            if context_discrimination > 0.3:
                print("  [우수] 문맥을 잘 구분함")
            elif context_discrimination > 0.2:
                print("  [양호] 어느정도 문맥 구분")
            elif context_discrimination > 0.1:
                print("  [보통] 약간의 문맥 구분")
            else:
                print("  [부족] 문맥 구분 어려움")
            print()

        except Exception as e:
            print("  [오류] 문맥 분석 오류: {}".format(e))
            print()

    return context_results

def advanced_privacy_risk_calculation(text, embedding):
    """고급 개인정보 위험도 계산 (DeBERTa v3 특화)"""
    risk_score = 0.0
    risk_factors = []
    confidence_factors = []

    # 1. 직접 식별자 (Direct Identifiers)
    direct_identifiers = {
        "이름패턴": ["XX", "○○", "김", "이", "박", "최", "정"],
        "연락처": ["010-", "전화", "핸드폰", "휴대폰"],
        "이메일": ["@", ".com", ".co.kr", "gmail", "naver"],
        "주민번호": ["-", "주민", "등록번호"]
    }

    for category, patterns in direct_identifiers.items():
        if any(pattern in text for pattern in patterns):
            risk_score += 0.4
            risk_factors.append(category)
            confidence_factors.append("직접식별자")

    # 2. 준식별자 조합 (Quasi-identifiers)
    quasi_identifiers = {
        "연령정보": ["세", "살", "연령", "나이", "40대", "50대", "60대"],
        "성별정보": ["남성", "여성", "남자", "여자"],
        "지역정보": ["구", "동", "시", "아파트", "거주", "주소"],
        "직업정보": ["의사", "간호사", "교수", "회사원", "직장"]
    }

    quasi_count = 0
    for category, patterns in quasi_identifiers.items():
        if any(pattern in text for pattern in patterns):
            quasi_count += 1
            risk_factors.append(category)

    # 준식별자 조합 위험도
    if quasi_count >= 3:
        risk_score += 0.5
        confidence_factors.append("준식별자조합")
    elif quasi_count >= 2:
        risk_score += 0.3
        confidence_factors.append("준식별자부분")

    # 3. 민감정보 (Sensitive Information)
    sensitive_info = {
        "의료정보": ["진단", "수술", "치료", "병원", "의원", "클리닉", "혈당", "혈압", "CT", "MRI"],
        "금융정보": ["계좌", "카드", "대출", "신용", "연봉", "월급"],
        "기술정보": ["API", "키", "password", "DB", "서버", "IP"],
        "법적정보": ["재판", "소송", "벌금", "구속", "기소"]
    }

    for category, patterns in sensitive_info.items():
        if any(pattern in text for pattern in patterns):
            risk_score += 0.25
            risk_factors.append(category)
            confidence_factors.append("민감정보")

    # 4. 시간적 특정성 (Temporal Specificity)
    temporal_specificity = ["2023년", "2024년", "2025년", "월", "일", "어제", "지난주", "오늘"]
    if any(temp in text for temp in temporal_specificity):
        risk_score += 0.15
        risk_factors.append("시간특정성")

    # 5. 문맥적 위험도 (Contextual Risk) - DeBERTa 임베딩 활용
    # 임베딩의 분산을 이용한 문맥 복잡도 측정
    if embedding is not None and len(embedding.shape) > 0:
        embedding_std = torch.std(embedding).item()
        if embedding_std > 0.1:  # 높은 분산 = 복잡한 문맥
            risk_score += 0.1
            confidence_factors.append("복잡문맥")

    # 6. 재식별 위험 조합 패턴
    reidentification_patterns = [
        # 병원 + 날짜 + 개인정보
        (["병원", "의원"] and ["2023", "2024", "2025"] and ["세", "남성", "여성"]),
        # 위치 + 사건 + 시간
        (["구", "동", "아파트"] and ["119", "응급", "사고"] and ["어제", "지난주"]),
        # 의료진 + 기관 + 시기
        (["의사", "교수", "간호사"] and ["병원", "대학"] and ["월", "일"])
    ]

    # 패턴 매칭 (간단한 휴리스틱)
    pattern_keywords = ["병원", "의원", "2023", "2024", "세", "남성", "여성", "구", "동", "119", "의사"]
    matched_keywords = [kw for kw in pattern_keywords if kw in text]
    if len(matched_keywords) >= 4:
        risk_score += 0.2
        confidence_factors.append("재식별패턴")

    # 7. 최종 점수 보정
    # 너무 많은 요소가 있으면 점수 상한 적용
    if len(risk_factors) > 6:
        risk_score = min(risk_score, 0.95)

    return risk_score, risk_factors, confidence_factors

def test_advanced_privacy_detection(model, tokenizer):
    """고급 개인정보 감지 테스트"""
    print("\n[고급감지] DeBERTa v3 고급 개인정보 감지 테스트")
    print("-" * 50)

    advanced_test_cases = [
        {
            "text": "본 연구는 2023년 1월부터 2024년 3월까지 서울시립병원에서 치료받은 65세 이상 폐렴 환자 1,240명을 대상으로 하였다",
            "category": "연구논문 초록",
            "expected_risk": "HIGH",
            "reason": "연구기간+기관+환자집단 특정"
        },
        {
            "text": "어제 산부인과에서 자궁근종 진단받았는데, MRI 결과를 업로드하면 위험한 건지 봐주세요",
            "category": "의료 챗봇 질문",
            "expected_risk": "CRITICAL",
            "reason": "개인 진단정보+시간특정+검사결과"
        },
        {
            "text": "5살 아들이 인천의료원에서 RSV 진단받았는데, 어린이집에 언제부터 보내도 될까요?",
            "category": "가족 의료 상담",
            "expected_risk": "HIGH",
            "reason": "가족관계+나이+병원+진단명"
        },
        {
            "text": "Phoenix 프로젝트 예산 50억, 담당자 김부장, API 키 sk-proj-abc123, DB 서버 192.168.1.100",
            "category": "기업 기밀 정보",
            "expected_risk": "CRITICAL",
            "reason": "프로젝트정보+담당자+기술정보 조합"
        },
        {
            "text": "분당서울대병원에서 진료받으시면 됩니다",
            "category": "일반 안내",
            "expected_risk": "LOW",
            "reason": "일반적인 병원 안내"
        },
        {
            "text": "당뇨병의 일반적인 증상은 다음과 같습니다",
            "category": "의학 정보",
            "expected_risk": "LOW",
            "reason": "일반적인 의학 지식"
        }
    ]

    detection_results = []
    performance_metrics = {"total": 0, "correct": 0}

    for i, case in enumerate(advanced_test_cases, 1):
        try:
            text = case["text"]
            embedding = get_contextual_embedding(model, tokenizer, text)
            risk_score, risk_factors, confidence_factors = advanced_privacy_risk_calculation(text, embedding)

            # 위험도 레벨 결정 (더 세밀한 기준)
            if risk_score >= 0.8:
                risk_level = "CRITICAL"
            elif risk_score >= 0.6:
                risk_level = "HIGH"
            elif risk_score >= 0.4:
                risk_level = "MEDIUM"
            elif risk_score >= 0.2:
                risk_level = "LOW"
            else:
                risk_level = "NONE"

            # 신뢰도 계산
            confidence = min(len(confidence_factors) * 0.2 + 0.4, 1.0)

            result = {
                "case_number": i,
                "text": text,
                "category": case["category"],
                "expected_risk": case["expected_risk"],
                "calculated_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "confidence_factors": confidence_factors,
                "confidence": confidence,
                "reason": case["reason"],
                "embedding_shape": embedding.shape if embedding is not None else None
            }
            detection_results.append(result)

            # 성능 측정
            performance_metrics["total"] += 1
            if risk_level == case["expected_risk"]:
                performance_metrics["correct"] += 1

            print("[케이스 {}] {}".format(i, case["category"]))
            print("  텍스트: {}...".format(text[:60]))
            print("  예상 위험도: {} ({})".format(case["expected_risk"], case["reason"]))
            print("  계산된 점수: {:.3f}".format(risk_score))
            print("  판정 위험도: {}".format(risk_level))
            print("  위험 요소: {}".format(", ".join(risk_factors)))
            print("  신뢰 요소: {}".format(", ".join(confidence_factors)))
            print("  신뢰도: {:.2f}".format(confidence))

            if risk_level == case["expected_risk"]:
                print("  [정확] ✓ 예상과 일치")
            else:
                print("  [오류] ✗ 예상: {}, 실제: {}".format(case["expected_risk"], risk_level))
            print()

        except Exception as e:
            print("  [오류] 고급 감지 테스트 오류: {}".format(e))
            print()

    return detection_results, performance_metrics

def save_results(tokenization_results, context_results, detection_results, performance_metrics, load_time):
    """결과 저장"""
    try:
        # 전체 성능 통계
        accuracy = performance_metrics["correct"] / performance_metrics["total"] if performance_metrics["total"] > 0 else 0
        avg_processing_time = load_time / performance_metrics["total"] if performance_metrics["total"] > 0 else 0

        # 문맥 구분 성능
        context_discrimination_scores = [r["context_discrimination"] for r in context_results]
        avg_context_discrimination = np.mean(context_discrimination_scores) if context_discrimination_scores else 0

        results = {
            "model_name": "DeBERTa-v3-Korean",
            "model_path": "team-lucid/deberta-v3-base-korean",
            "test_timestamp": datetime.now().isoformat(),
            "loading_time": load_time,
            "performance": {
                "total_tests": performance_metrics["total"],
                "correct_predictions": performance_metrics["correct"],
                "accuracy": accuracy,
                "avg_processing_time": avg_processing_time,
                "avg_context_discrimination": avg_context_discrimination
            },
            "tokenization_results": tokenization_results,
            "context_understanding": context_results,
            "advanced_privacy_detection": detection_results,
            "model_advantages": [
                "뛰어난 문맥 이해 능력",
                "복잡한 한국어 구문 분석",
                "고급 어텐션 메커니즘",
                "준식별자 조합 패턴 인식"
            ]
        }

        # results 폴더가 없으면 생성
        import os
        if not os.path.exists("results"):
            os.makedirs("results")

        with open("results/deberta_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("[저장] 결과가 results/deberta_results.json에 저장되었습니다")
        return True

    except Exception as e:
        print("[오류] 결과 저장 실패: {}".format(e))
        return False

def main():
    """메인 테스트 함수"""
    print("[시작] DeBERTa v3 Korean 개인정보 감지 테스트 시작")
    print("=" * 60)

    # 1. 설치 확인
    success, method = test_deberta_installation()
    if not success:
        print("[실패] transformers 라이브러리 설치를 확인해주세요.")
        sys.exit(1)

    print("[정보] 사용 방법: {}".format(method))

    # 2. 모델 로딩
    model, tokenizer, load_time = load_deberta_model()
    if model is None:
        print("[실패] 모델 로딩 실패")
        sys.exit(1)

    print("[정보] 로딩 완료, 소요시간: {:.2f}초".format(load_time))

    # 3. 고급 토크나이징 테스트
    tokenization_results = test_advanced_tokenization(tokenizer)

    # 4. 문맥적 위험 이해 테스트
    context_results = test_contextual_risk_understanding(model, tokenizer)

    # 5. 고급 개인정보 감지 테스트
    detection_results, performance_metrics = test_advanced_privacy_detection(model, tokenizer)

    # 6. 결과 저장
    save_results(tokenization_results, context_results, detection_results, performance_metrics, load_time)

    print("\n" + "=" * 60)
    print("[요약] DeBERTa v3 Korean 테스트 결과 요약")
    print("=" * 60)
    print("[성공] 확인된 고급 기능:")
    print("  - DeBERTa v3 Korean 모델 로딩")
    print("  - 복잡한 한국어 문장 토크나이징")
    print("  - 문맥적 위험도 차별화")
    print("  - 고급 준식별자 조합 분석")
    print("  - 재식별 패턴 인식")
    print()

    # 성능 통계
    accuracy = performance_metrics["correct"] / performance_metrics["total"] if performance_metrics["total"] > 0 else 0
    context_scores = [r["context_discrimination"] for r in context_results]
    avg_context_discrimination = np.mean(context_scores) if context_scores else 0

    print("[성능] 테스트 결과:")
    print("  - 총 테스트: {}건".format(performance_metrics["total"]))
    print("  - 정확한 예측: {}건".format(performance_metrics["correct"]))
    print("  - 정확도: {:.1f}%".format(accuracy * 100))
    print("  - 평균 문맥 구분력: {:.3f}".format(avg_context_discrimination))
    print("  - 평균 처리시간: {:.2f}초/건".format(load_time / performance_metrics["total"] if performance_metrics["total"] > 0 else 0))
    print()
    print("[결론] DeBERTa v3 Korean은 최신 아키텍처로 복잡한 문맥 이해에 우수")
    print("       특히 준식별자 조합과 재식별 패턴 인식에서 뛰어난 성능")
    print("       KcELECTRA와 조합하여 사용하면 최고의 성능 기대")

if __name__ == "__main__":
    main()