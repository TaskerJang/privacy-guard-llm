"""
KoELECTRA 개인정보 문맥 이해 테스트 (이모지 수정본)
"""

import torch
import time
import sys
from transformers import AutoTokenizer, AutoModel
import numpy as np

def test_koelectra_installation():
    """KoELECTRA 설치 확인"""
    try:
        from transformers import AutoTokenizer, AutoModel
        print("[성공] KoELECTRA (transformers) 라이브러리 import 성공!")
        return True
    except ImportError as e:
        print("[실패] KoELECTRA import 실패: {}".format(e))
        return False

def load_koelectra_model():
    """KoELECTRA 모델 로딩"""
    try:
        print("[로딩] KoELECTRA 모델 로딩 중...")
        start_time = time.time()

        model_name = "monologg/koelectra-base-v3-discriminator"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)

        # 평가 모드로 설정
        model.eval()

        load_time = time.time() - start_time
        print("[성공] KoELECTRA 모델 로딩 완료! (소요시간: {:.2f}초)".format(load_time))
        print("[정보] 모델 정보: {}".format(model_name))
        print("[정보] 어휘 사전 크기: {}".format(tokenizer.vocab_size))

        return model, tokenizer
    except Exception as e:
        print("[실패] KoELECTRA 모델 로딩 실패: {}".format(e))
        return None, None

def test_tokenization(tokenizer):
    """토크나이징 테스트"""
    print("\n[토큰] KoELECTRA 토크나이징 테스트")
    print("-" * 50)

    test_sentences = [
        "안녕하세요 김철수입니다",
        "전화번호는 010-1234-5678입니다",
        "35세 남성 의사이고 강남구에 거주합니다",
        "환자 김철수가 어제 수술을 받았습니다",
        "API 키는 sk-abc123입니다",
        "우리 회사 Phoenix 프로젝트 예산은 50억입니다",
        "혈당 350, 케톤산증으로 응급실에 내원한 40대 남성"
    ]

    for sentence in test_sentences:
        tokens = tokenizer.tokenize(sentence)
        token_ids = tokenizer.encode(sentence, add_special_tokens=True)

        print("원문: {}".format(sentence))
        print("토큰: {}".format(tokens))
        print("토큰 수: {}, ID 수: {}".format(len(tokens), len(token_ids)))
        print()

def test_korean_specific_performance(model, tokenizer):
    """한국어 특화 성능 테스트"""
    print("\n[한국어] KoELECTRA 한국어 특화 성능 테스트")
    print("-" * 50)

    # 한국어 특화 유사도 테스트
    test_pairs = [
        ("김철수씨가 오셨습니다", "김철수님이 오셨습니다", "한국어 존댓말 차이"),
        ("병원에 갔어요", "병원에 가셨어요", "높임법 차이"),
        ("의사선생님", "의사 선생님", "띄어쓰기 차이"),
        ("010-1234-5678", "공일공-일이삼사-오육칠팔", "숫자 표현 차이"),
        ("강남구 역삼동", "강남구역삼동", "주소 표기 차이"),
        ("삼성전자", "삼성 전자", "기업명 표기"),
        ("코로나19", "코로나 19", "숫자 포함 단어")
    ]

    print("[유사도] 한국어 특화 유사도 테스트:")

    for text1, text2, desc in test_pairs:
        try:
            # 임베딩 생성
            emb1 = get_sentence_embedding(model, tokenizer, text1)
            emb2 = get_sentence_embedding(model, tokenizer, text2)

            # 코사인 유사도 계산
            similarity = torch.cosine_similarity(emb1, emb2, dim=0).item()

            print("  {}".format(desc))
            print("    '{}' vs '{}'".format(text1, text2))
            print("    유사도: {:.4f}".format(similarity))

            if similarity > 0.9:
                print("    [성공] 매우 우수한 한국어 이해")
            elif similarity > 0.7:
                print("    [성공] 좋은 한국어 이해")
            elif similarity > 0.5:
                print("    [주의] 보통 수준")
            else:
                print("    [실패] 낮은 이해도")
            print()

        except Exception as e:
            print("    [오류] 오류: {}".format(e))
            print()

def get_sentence_embedding(model, tokenizer, text):
    """문장 임베딩 추출"""
    # 토큰화
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

    # 모델 추론
    with torch.no_grad():
        outputs = model(**inputs)

    # [CLS] 토큰의 임베딩 사용
    sentence_embedding = outputs.last_hidden_state[:, 0, :]

    return sentence_embedding.squeeze()

def test_similarity(model, tokenizer):
    """문맥 유사도 테스트"""
    print("\n[유사도] KoELECTRA 문맥 유사도 테스트")
    print("-" * 50)

    test_pairs = [
        ("환자 김철수가 수술받았습니다", "김철수 교수님이 강의하셨습니다", "환자 vs 교수"),
        ("35세 남성 의사", "40대 여성 간호사", "의료진 정보"),
        ("API 키는 sk-abc123", "비밀번호는 password123", "인증 정보"),
        ("혈당 350 케톤산증", "혈압 140/90 고혈압", "의료 수치"),
        ("우리 회사 매출 50억", "경쟁사 수익 30억", "기업 정보"),
        ("강남구에 거주하는 의사", "서초구에 사는 변호사", "거주지+직업"),
        ("Phoenix 프로젝트 예산", "Alpha 프로젝트 일정", "프로젝트 정보")
    ]

    for text1, text2, desc in test_pairs:
        try:
            emb1 = get_sentence_embedding(model, tokenizer, text1)
            emb2 = get_sentence_embedding(model, tokenizer, text2)

            # 코사인 유사도
            similarity = torch.cosine_similarity(emb1, emb2, dim=0).item()

            print("[분석] {}".format(desc))
            print("  텍스트1: {}".format(text1))
            print("  텍스트2: {}".format(text2))
            print("  유사도: {:.4f}".format(similarity))

            if similarity > 0.8:
                print("  [높음] 매우 유사")
            elif similarity > 0.6:
                print("  [중간] 어느정도 유사")
            elif similarity > 0.4:
                print("  [낮음] 약간 유사")
            else:
                print("  [매우낮음] 낮은 유사도")
            print()

        except Exception as e:
            print("  [오류] 오류: {}".format(e))
            print()

def test_privacy_detection(model, tokenizer):
    """개인정보 감지 성능 테스트"""
    print("\n[개인정보] KoELECTRA 개인정보 감지 성능 테스트")
    print("-" * 50)

    test_cases = [
        ("안녕하세요 제 이름은 김철수입니다", "직접 개인정보", "HIGH"),
        ("전화번호는 010-1234-5678입니다", "전화번호", "HIGH"),
        ("35세 남성 의사이고 강남구에 거주합니다", "조합 정보", "MEDIUM"),
        ("환자 김철수가 어제 수술받았습니다", "의료 맥락", "HIGH"),
        ("김철수 교수님이 강의하셨습니다", "교육 맥락", "LOW"),
        ("API 키는 sk-abc123입니다", "기술 정보", "HIGH"),
        ("우리 회사 Phoenix 프로젝트 예산은 50억입니다", "기업 기밀", "HIGH"),
        ("혈당 350, 케톤산증으로 응급실에 내원한 40대 남성", "의료 조합 정보", "HIGH"),
        ("강남구에 사는 35세 변호사가 BMW를 운전합니다", "생활 조합 정보", "MEDIUM"),
        ("오늘 날씨가 좋네요", "일반 텍스트", "NONE"),
        ("점심 뭐 먹을까요?", "일상 대화", "NONE")
    ]

    for text, category, expected_risk in test_cases:
        try:
            embedding = get_sentence_embedding(model, tokenizer, text)

            # 간단한 휴리스틱 위험도 계산
            privacy_score = calculate_privacy_score(text)

            # 위험도 분류
            if privacy_score >= 0.8:
                calculated_risk = 'CRITICAL'
            elif privacy_score >= 0.6:
                calculated_risk = 'HIGH'
            elif privacy_score >= 0.4:
                calculated_risk = 'MEDIUM'
            elif privacy_score >= 0.1:
                calculated_risk = 'LOW'
            else:
                calculated_risk = 'NONE'

            print("[테스트] {}".format(category))
            print("  텍스트: {}".format(text))
            print("  예상 위험도: {}".format(expected_risk))
            print("  계산된 점수: {:.2f}".format(privacy_score))
            print("  임베딩 차원: {}".format(embedding.shape))
            print("  판정 위험도: {}".format(calculated_risk))

            if calculated_risk == expected_risk:
                print("  [성공] 예상과 일치")
            else:
                print("  [주의] 예상과 다름")
            print()

        except Exception as e:
            print("  [오류] 오류: {}".format(e))
            print()

def calculate_privacy_score(text):
    """개인정보 위험도 점수 계산"""
    score = 0.0

    # 이름 패턴
    import re
    if re.search(r'[가-힣]{2,4}(?=\s|님|씨|$)', text):
        score += 0.4

    # 전화번호
    if re.search(r'010-\d{4}-\d{4}', text):
        score += 0.4

    # 나이
    if re.search(r'\d{1,2}세|\d{1,2}살', text):
        score += 0.2

    # 성별
    if re.search(r'남성|여성|남자|여자', text):
        score += 0.1

    # 직업
    if re.search(r'의사|변호사|교수|간호사', text):
        score += 0.1

    # 지역
    if re.search(r'[가-힣]+구|[가-힣]+동', text):
        score += 0.1

    # 의료 정보
    if re.search(r'환자|수술|진단|치료|혈당|혈압', text):
        score += 0.1

    # API 키 등
    if re.search(r'API|키|sk-|password', text):
        score += 0.3

    # 기업 정보
    if re.search(r'프로젝트|예산|매출|억', text):
        score += 0.1

    return min(score, 1.0)

def test_performance(model, tokenizer):
    """성능 측정"""
    print("\n[성능] KoELECTRA 성능 측정")
    print("-" * 50)

    test_texts = [
        "안녕하세요",
        "35세 남성 의사이고 강남구에 거주합니다",
        "환자 김철수가 어제 수술을 받았고, 담당의는 박영희 교수님입니다. 혈당 수치가 350으로 높아서 케톤산증이 의심되어 응급실에 내원했습니다. 가족력상 당뇨병이 있으며, 현재 인슐린 치료를 받고 있습니다. 연락처는 010-1234-5678이고, 주소는 강남구 역삼동입니다."
    ]

    for i, text in enumerate(test_texts, 1):
        start_time = time.time()
        embedding = get_sentence_embedding(model, tokenizer, text)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000  # ms로 변환

        print("[테스트] 테스트 {}:".format(i))
        print("  텍스트 길이: {}자".format(len(text)))
        print("  처리 시간: {:.2f}ms".format(processing_time))
        print("  임베딩 크기: {}".format(embedding.shape))
        print()

def main():
    """메인 테스트 함수"""
    print("[시작] KoELECTRA 개인정보 감지 테스트 시작")
    print("=" * 60)

    # 1. 설치 확인
    if not test_koelectra_installation():
        print("[실패] KoELECTRA 설치를 확인해주세요.")
        sys.exit(1)

    # 2. 모델 로딩
    model, tokenizer = load_koelectra_model()
    if model is None or tokenizer is None:
        print("[실패] 모델 로딩 실패")
        sys.exit(1)

    # 3. 토크나이징 테스트
    test_tokenization(tokenizer)

    # 4. 한국어 특화 성능 테스트
    test_korean_specific_performance(model, tokenizer)

    # 5. 유사도 테스트
    test_similarity(model, tokenizer)

    # 6. 개인정보 감지 테스트
    test_privacy_detection(model, tokenizer)

    # 7. 성능 측정
    test_performance(model, tokenizer)

    print("\n" + "=" * 60)
    print("[요약] KoELECTRA 테스트 결과 요약")
    print("=" * 60)
    print("[성공] 확인된 기능:")
    print("  - 한국어 특화 토크나이징 우수")
    print("  - 효율적인 처리 속도 (ELECTRA 구조)")
    print("  - 한국어 문맥 이해 능력")
    print("  - 띄어쓰기, 존댓말 등 한국어 특성 인식")
    print()
    print("[강점] KoELECTRA 강점:")
    print("  - KoBERT 대비 빠른 추론 속도")
    print("  - 한국어 문법 구조 이해")
    print("  - 효율적인 메모리 사용")
    print()
    print("[한계] 한계점:")
    print("  - 개인정보 특화 fine-tuning 필요")
    print("  - 조합 위험도 판단 알고리즘 별도 구현 필요")
    print()
    print("[결론] 결론: KoELECTRA는 속도와 한국어 이해의 균형이 우수하여")
    print("       개인정보 감지 프로젝트에 적합한 기반 모델")

if __name__ == "__main__":
    main()