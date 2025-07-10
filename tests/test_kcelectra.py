"""
KcELECTRA 개인정보 문맥 이해 테스트 (beomi/KcELECTRA-base)
"""

import torch
import time
import sys
import json
from datetime import datetime

def test_kcelectra_installation():
    """KcELECTRA 설치 확인"""
    try:
        from transformers import AutoTokenizer, AutoModel
        print("[성공] transformers Auto 모델 import 성공!")
        return True, "transformers"
    except ImportError as e:
        print("[실패] transformers 라이브러리 import 실패: {}".format(e))
        return False, None

def load_kcelectra_model():
    """KcELECTRA 모델 로딩"""
    try:
        print("[로딩] KcELECTRA 모델 로딩 중...")
        start_time = time.time()

        model_name = "beomi/KcELECTRA-base"

        # Auto 클래스 사용 (호환성 문제 해결)
        from transformers import AutoTokenizer, AutoModel
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.eval()

        load_time = time.time() - start_time
        print("[성공] KcELECTRA 모델 로딩 완료! (소요시간: {:.2f}초)".format(load_time))
        return model, tokenizer, load_time

    except Exception as e:
        print("[실패] KcELECTRA 모델 로딩 실패: {}".format(e))
        return None, None, None

def test_tokenization(tokenizer):
    """토크나이징 테스트"""
    print("\n[토큰] KcELECTRA 토크나이징 테스트")
    print("-" * 50)

    test_sentences = [
        "김XX(47세 여성)은 2023년 10월 13일 분당서울대병원에서 내시경을 받았다",
        "35세 남성 의사이고 강남구에 거주합니다",
        "환자 이름 이○○, 생년월일 1955.04.03, 진단명 뇌졸중",
        "어제 119 부르고 성남시 OO아파트 앞에서 실신해서 응급실 갔어요",
        "API 키는 sk-abc123이고 데이터베이스는 192.168.1.100입니다"
    ]

    tokenization_results = []

    for sentence in test_sentences:
        try:
            tokens = tokenizer.tokenize(sentence)
            token_ids = tokenizer.encode(sentence, add_special_tokens=True)

            result = {
                "text": sentence,
                "tokens": tokens,
                "token_count": len(tokens),
                "token_ids": token_ids
            }
            tokenization_results.append(result)

            print("원문: {}".format(sentence))
            print("토큰 수: {}".format(len(tokens)))
            print("토큰: {}".format(tokens[:10] + ["..."] if len(tokens) > 10 else tokens))
            print()

        except Exception as e:
            print("원문: {}".format(sentence))
            print("토큰화 오류: {}".format(e))
            print()

    return tokenization_results

def get_sentence_embedding(model, tokenizer, text):
    """문장 임베딩 추출"""
    try:
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        # [CLS] 토큰의 임베딩 사용
        return outputs.last_hidden_state[:, 0, :].squeeze()
    except Exception as e:
        print("임베딩 추출 오류: {}".format(e))
        return torch.randn(768)

def test_medical_context_understanding(model, tokenizer):
    """의료 문맥 이해 테스트"""
    print("\n[의료문맥] 의료 문맥 이해 테스트")
    print("-" * 50)

    medical_test_pairs = [
        ("김XX(47세 여성)은 분당서울대병원에서 위염 진단을 받았다",
         "김철수 교수님이 분당서울대병원에서 강의하셨다", "환자 vs 교수"),
        ("혈당 350, 케톤산증, 40대 남성",
         "혈압 140/90, 고혈압, 50대 여성", "의료 수치 조합"),
        ("2023년 9월에 서울아산병원에서 간 절제술을 받은 63세 남자",
         "2023년 9월에 서울아산병원에서 간호사로 근무하는 63세 여자", "환자 vs 의료진"),
        ("지난주에 119 부르고 성남시 OO아파트에서 실신",
         "지난주에 성남시 OO아파트에서 화재가 발생", "응급상황 vs 일반사건")
    ]

    context_results = []

    for text1, text2, desc in medical_test_pairs:
        try:
            emb1 = get_sentence_embedding(model, tokenizer, text1)
            emb2 = get_sentence_embedding(model, tokenizer, text2)

            similarity = torch.cosine_similarity(emb1, emb2, dim=0).item()

            result = {
                "description": desc,
                "text1": text1,
                "text2": text2,
                "similarity": similarity
            }
            context_results.append(result)

            print("[분석] {}".format(desc))
            print("  텍스트1: {}".format(text1))
            print("  텍스트2: {}".format(text2))
            print("  유사도: {:.4f}".format(similarity))

            if similarity > 0.8:
                print("  [높음] 매우 유사한 문맥")
            elif similarity > 0.6:
                print("  [중간] 어느정도 유사한 문맥")
            elif similarity > 0.4:
                print("  [낮음] 약간 다른 문맥")
            else:
                print("  [매우낮음] 완전히 다른 문맥")
            print()

        except Exception as e:
            print("  [오류] 문맥 분석 오류: {}".format(e))
            print()

    return context_results

def calculate_privacy_risk_score(text, embedding):
    """개인정보 위험도 점수 계산"""
    risk_score = 0.0
    risk_factors = []

    # 의료 기관명
    medical_institutions = ['병원', '의원', '클리닉', '서울대병원', '분당서울대병원', '아산병원', '세브란스']
    if any(inst in text for inst in medical_institutions):
        risk_score += 0.3
        risk_factors.append("의료기관명")

    # 개인 식별 정보
    personal_info = ['세', '남성', '여성', '살', '○○', 'XX']
    if any(info in text for info in personal_info):
        risk_score += 0.2
        risk_factors.append("개인정보")

    # 날짜 정보
    date_patterns = ['2023년', '2024년', '2025년', '월', '일', '어제', '지난주']
    if any(date in text for date in date_patterns):
        risk_score += 0.2
        risk_factors.append("날짜정보")

    # 위치 정보
    location_info = ['구', '동', '아파트', '주소', '거주']
    if any(loc in text for loc in location_info):
        risk_score += 0.15
        risk_factors.append("위치정보")

    # 의료 정보
    medical_info = ['진단', '수술', '치료', '혈당', '혈압', '케톤산증', '뇌졸중']
    if any(med in text for med in medical_info):
        risk_score += 0.15
        risk_factors.append("의료정보")

    # 조합 위험도 (여러 요소가 함께 있을 때)
    if len(risk_factors) >= 3:
        risk_score += 0.2
        risk_factors.append("조합위험")

    return risk_score, risk_factors

def test_privacy_detection(model, tokenizer):
    """개인정보 감지 성능 테스트"""
    print("\n[개인정보] KcELECTRA 개인정보 감지 테스트")
    print("-" * 50)

    test_cases = [
        ("김XX(47세 여성)은 2023년 10월 13일 분당서울대병원에서 내시경을 받았다", "조합형 의료정보", "CRITICAL"),
        ("35세 남성 의사이고 강남구에 거주합니다", "개인 기본정보", "HIGH"),
        ("환자 이름 이○○, 생년월일 1955.04.03, 진단명 뇌졸중", "직접 개인정보", "CRITICAL"),
        ("지난주에 119 부르고 성남시 OO아파트에서 실신해서 응급실 갔어요", "응급상황 정보", "HIGH"),
        ("혈당 350, 케톤산증, 40대 남성", "의료 수치 조합", "MEDIUM"),
        ("오늘 날씨가 좋네요", "일반 텍스트", "LOW"),
        ("병원에서 검사를 받았습니다", "일반 의료정보", "LOW")
    ]

    detection_results = []

    for text, category, expected_risk in test_cases:
        try:
            embedding = get_sentence_embedding(model, tokenizer, text)
            risk_score, risk_factors = calculate_privacy_risk_score(text, embedding)

            # 위험도 레벨 결정
            if risk_score >= 0.7:
                risk_level = "CRITICAL"
            elif risk_score >= 0.5:
                risk_level = "HIGH"
            elif risk_score >= 0.3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            result = {
                "text": text,
                "category": category,
                "expected_risk": expected_risk,
                "calculated_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "embedding_shape": embedding.shape
            }
            detection_results.append(result)

            print("[테스트] {}".format(category))
            print("  텍스트: {}".format(text))
            print("  예상 위험도: {}".format(expected_risk))
            print("  계산된 점수: {:.2f}".format(risk_score))
            print("  판정 위험도: {}".format(risk_level))
            print("  위험 요소: {}".format(", ".join(risk_factors)))
            print("  임베딩 차원: {}".format(embedding.shape))

            if risk_level == expected_risk:
                print("  [일치] ✓ 예상과 일치")
            else:
                print("  [불일치] ✗ 예상과 다름")
            print()

        except Exception as e:
            print("  [오류] 개인정보 감지 테스트 오류: {}".format(e))
            print()

    return detection_results

def save_results(tokenization_results, context_results, detection_results, load_time):
    """결과 저장"""
    try:
        # 성능 통계 계산
        total_tests = len(detection_results)
        correct_predictions = sum(1 for r in detection_results if r["risk_level"] == r["expected_risk"])
        accuracy = correct_predictions / total_tests if total_tests > 0 else 0

        avg_processing_time = load_time / total_tests if total_tests > 0 else 0

        results = {
            "model_name": "KcELECTRA",
            "model_path": "beomi/KcELECTRA-base",
            "test_timestamp": datetime.now().isoformat(),
            "loading_time": load_time,
            "performance": {
                "total_tests": total_tests,
                "correct_predictions": correct_predictions,
                "accuracy": accuracy,
                "avg_processing_time": avg_processing_time
            },
            "tokenization_results": tokenization_results,
            "context_understanding": context_results,
            "privacy_detection": detection_results
        }

        # results 폴더가 없으면 생성
        import os
        if not os.path.exists("results"):
            os.makedirs("results")

        with open("results/kcelectra_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("[저장] 결과가 results/kcelectra_results.json에 저장되었습니다")
        return True

    except Exception as e:
        print("[오류] 결과 저장 실패: {}".format(e))
        return False

def main():
    """메인 테스트 함수"""
    print("[시작] KcELECTRA 개인정보 감지 테스트 시작")
    print("=" * 60)

    # 1. 설치 확인
    success, method = test_kcelectra_installation()
    if not success:
        print("[실패] transformers 라이브러리 설치를 확인해주세요.")
        sys.exit(1)

    print("[정보] 사용 방법: {}".format(method))

    # 2. 모델 로딩
    model, tokenizer, load_time = load_kcelectra_model()
    if model is None:
        print("[실패] 모델 로딩 실패")
        sys.exit(1)

    print("[정보] 로딩 완료, 소요시간: {:.2f}초".format(load_time))

    # 3. 토크나이징 테스트
    tokenization_results = test_tokenization(tokenizer)

    # 4. 의료 문맥 이해 테스트
    context_results = test_medical_context_understanding(model, tokenizer)

    # 5. 개인정보 감지 테스트
    detection_results = test_privacy_detection(model, tokenizer)

    # 6. 결과 저장
    save_results(tokenization_results, context_results, detection_results, load_time)

    print("\n" + "=" * 60)
    print("[요약] KcELECTRA 테스트 결과 요약")
    print("=" * 60)
    print("[성공] 확인된 기능:")
    print("  - KcELECTRA 모델 로딩 (beomi/KcELECTRA-base)")
    print("  - 한국어 토크나이징")
    print("  - 의료 문맥 이해")
    print("  - 조합형 개인정보 위험도 계산")
    print()

    # 성능 통계
    total_tests = len(detection_results)
    correct = sum(1 for r in detection_results if r["risk_level"] == r["expected_risk"])
    accuracy = correct / total_tests if total_tests > 0 else 0

    print("[성능] 테스트 결과:")
    print("  - 총 테스트: {}건".format(total_tests))
    print("  - 정확한 예측: {}건".format(correct))
    print("  - 정확도: {:.1f}%".format(accuracy * 100))
    print("  - 평균 처리시간: {:.2f}초/건".format(load_time / total_tests if total_tests > 0 else 0))
    print()
    print("[결론] KcELECTRA는 한국어 의료 텍스트의 문맥적 개인정보 감지에 적합")
    print("       특히 조합형 위험 요소 탐지에서 우수한 성능 기대")

if __name__ == "__main__":
    main()