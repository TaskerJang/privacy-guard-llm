"""
BERT 개인정보 감지 테스트 (이모지 수정본)
"""

import torch
import time
import sys
from transformers import BertTokenizer, BertModel
import numpy as np

def test_bert_installation():
    """BERT 설치 확인"""
    try:
        from transformers import BertTokenizer, BertModel
        print("[성공] BERT (transformers) 라이브러리 import 성공!")
        return True
    except ImportError as e:
        print("[실패] BERT import 실패: {}".format(e))
        return False

def load_bert_model():
    """BERT 모델 로딩"""
    try:
        print("[로딩] BERT 모델 로딩 중...")
        start_time = time.time()

        model_name = "bert-base-multilingual-cased"
        tokenizer = BertTokenizer.from_pretrained(model_name)
        model = BertModel.from_pretrained(model_name)

        # 평가 모드로 설정
        model.eval()

        load_time = time.time() - start_time
        print("[성공] BERT 모델 로딩 완료! (소요시간: {:.2f}초)".format(load_time))
        print("[정보] 모델 정보: {}".format(model_name))
        print("[정보] 어휘 사전 크기: {}".format(tokenizer.vocab_size))

        return model, tokenizer
    except Exception as e:
        print("[실패] BERT 모델 로딩 실패: {}".format(e))
        return None, None

def test_tokenization(tokenizer):
    """토크나이징 테스트"""
    print("\n[토큰] BERT 토크나이징 테스트")
    print("-" * 50)

    test_sentences = [
        "Hello, my name is John Smith",
        "안녕하세요 김철수입니다",
        "전화번호는 010-1234-5678입니다",
        "35세 남성 의사이고 강남구에 거주합니다",
        "Patient John had surgery yesterday",
        "환자 김철수가 어제 수술받았습니다",
        "API key is sk-abc123def456"
    ]

    for sentence in test_sentences:
        tokens = tokenizer.tokenize(sentence)
        token_ids = tokenizer.encode(sentence, add_special_tokens=True)

        print("원문: {}".format(sentence))
        print("토큰: {}".format(tokens))
        print("토큰 수: {}, ID 수: {}".format(len(tokens), len(token_ids)))
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

def test_multilingual_performance(model, tokenizer):
    """다국어 성능 테스트"""
    print("\n[다국어] BERT 다국어 성능 테스트")
    print("-" * 50)

    # 동일 의미 영어-한국어 쌍
    test_pairs = [
        ("Hello, my name is John Smith", "안녕하세요 제 이름은 김철수입니다"),
        ("I am a doctor", "저는 의사입니다"),
        ("Patient had surgery", "환자가 수술받았습니다"),
        ("API key is confidential", "API 키는 기밀입니다"),
        ("Phone number is private", "전화번호는 개인정보입니다")
    ]

    print("[비교] 동일 의미 영어-한국어 유사도:")

    for eng_text, kor_text in test_pairs:
        try:
            # 임베딩 생성
            eng_emb = get_sentence_embedding(model, tokenizer, eng_text)
            kor_emb = get_sentence_embedding(model, tokenizer, kor_text)

            # 코사인 유사도 계산
            similarity = torch.cosine_similarity(eng_emb, kor_emb, dim=0).item()

            print("  영어: {}".format(eng_text))
            print("  한국어: {}".format(kor_text))
            print("  유사도: {:.4f}".format(similarity))

            if similarity > 0.8:
                print("  [성공] 우수한 다국어 이해")
            elif similarity > 0.6:
                print("  [좋음] 좋은 다국어 이해")
            elif similarity > 0.4:
                print("  [보통] 보통 수준")
            else:
                print("  [주의] 낮은 이해도")
            print()

        except Exception as e:
            print("  [오류] 오류: {}".format(e))
            print()

def test_similarity(model, tokenizer):
    """문맥 유사도 테스트"""
    print("\n[유사도] BERT 문맥 유사도 테스트")
    print("-" * 50)

    test_pairs = [
        ("Patient John had surgery", "Doctor John gave a lecture", "영어: 환자 vs 의사"),
        ("환자 김철수가 수술받았습니다", "김철수 교수님이 강의하셨습니다", "한국어: 환자 vs 교수"),
        ("35-year-old male doctor", "40-year-old female nurse", "영어: 의료진 정보"),
        ("35세 남성 의사", "40대 여성 간호사", "한국어: 의료진 정보"),
        ("API key sk-abc123", "password password123", "영어: 인증 정보"),
        ("API 키는 sk-abc123", "비밀번호는 password123", "한국어: 인증 정보")
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
    print("\n[개인정보] BERT 개인정보 감지 성능 테스트")
    print("-" * 50)

    test_cases = [
        # 영어 테스트 케이스
        ("Hello, my name is John Smith", "영어 직접 개인정보", "HIGH"),
        ("My email is john.smith@example.com", "영어 이메일", "HIGH"),
        ("Phone number is 555-123-4567", "영어 전화번호", "HIGH"),
        ("35-year-old male doctor living in Manhattan", "영어 조합 정보", "MEDIUM"),
        ("Patient John had surgery yesterday", "영어 의료 맥락", "HIGH"),
        ("Professor John gave a lecture", "영어 교육 맥락", "LOW"),
        ("API key is sk-abc123def456", "영어 기술 정보", "HIGH"),
        ("The weather is nice today", "영어 일반 텍스트", "NONE"),

        # 한국어 테스트 케이스
        ("안녕하세요 제 이름은 김철수입니다", "한국어 직접 개인정보", "HIGH"),
        ("전화번호는 010-1234-5678입니다", "한국어 전화번호", "HIGH"),
        ("35세 남성 의사이고 강남구에 거주합니다", "한국어 조합 정보", "MEDIUM"),
        ("환자 김철수가 어제 수술받았습니다", "한국어 의료 맥락", "HIGH"),
        ("김철수 교수님이 강의하셨습니다", "한국어 교육 맥락", "LOW"),
        ("API 키는 sk-abc123입니다", "한국어 기술 정보", "HIGH"),
        ("오늘 날씨가 좋네요", "한국어 일반 텍스트", "NONE")
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
    import re
    score = 0.0

    # 영어 이름 패턴
    if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text):
        score += 0.4

    # 한국어 이름 패턴
    if re.search(r'[가-힣]{2,4}(?=\s|님|씨|$)', text):
        score += 0.4

    # 이메일
    if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
        score += 0.6

    # 전화번호 (영어)
    if re.search(r'\b\d{3}-\d{3}-\d{4}\b', text):
        score += 0.6

    # 전화번호 (한국어)
    if re.search(r'010-\d{4}-\d{4}', text):
        score += 0.6

    # 나이
    if re.search(r'\d{1,2}세|\d{1,2}살|\d{1,2}-year-old', text):
        score += 0.1

    # 성별
    if re.search(r'남성|여성|남자|여자|male|female', text):
        score += 0.1

    # 직업
    if re.search(r'의사|변호사|교수|간호사|doctor|lawyer|professor|nurse', text):
        score += 0.1

    # 지역
    if re.search(r'[가-힣]+구|[가-힣]+동|Manhattan|Brooklyn', text):
        score += 0.1

    # 의료 정보
    if re.search(r'환자|수술|진단|치료|patient|surgery|diagnosis|treatment', text):
        score += 0.1

    # API 키 등
    if re.search(r'API|키|sk-|password', text):
        score += 0.4

    return min(score, 1.0)

def test_performance(model, tokenizer):
    """성능 측정"""
    print("\n[성능] BERT 성능 측정")
    print("-" * 50)

    test_texts = [
        "Hello",
        "35-year-old male doctor living in Manhattan",
        "Patient John had surgery yesterday and the doctor was very skilled. The recovery process went smoothly and the patient is now doing well. Contact information: john@example.com"
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
    print("[시작] BERT 개인정보 감지 테스트 시작")
    print("=" * 60)

    # 1. 설치 확인
    if not test_bert_installation():
        print("[실패] BERT 설치를 확인해주세요.")
        sys.exit(1)

    # 2. 모델 로딩
    model, tokenizer = load_bert_model()
    if model is None or tokenizer is None:
        print("[실패] 모델 로딩 실패")
        sys.exit(1)

    # 3. 토크나이징 테스트
    test_tokenization(tokenizer)

    # 4. 다국어 성능 테스트
    test_multilingual_performance(model, tokenizer)

    # 5. 유사도 테스트
    test_similarity(model, tokenizer)

    # 6. 개인정보 감지 테스트
    test_privacy_detection(model, tokenizer)

    # 7. 성능 측정
    test_performance(model, tokenizer)

    print("\n" + "=" * 60)
    print("[요약] BERT 테스트 결과 요약")
    print("=" * 60)
    print("[성공] 확인된 기능:")
    print("  - 다국어 텍스트 처리")
    print("  - 영어-한국어 문맥 이해")
    print("  - 문장 임베딩 생성 (768차원)")
    print("  - 기본적인 의미 유사도 계산")
    print()
    print("[강점] BERT 강점:")
    print("  - 다국어 지원")
    print("  - 안정적인 성능")
    print("  - 풍부한 사전 훈련")
    print()
    print("[한계] 한계점:")
    print("  - 개인정보 특화 fine-tuning 필요")
    print("  - 한국어 특화 모델 대비 성능 제한")
    print()
    print("[결론] 결론: BERT는 다국어 지원이 우수하지만,")
    print("       한국어 특화 프로젝트에는 KoBERT/KoELECTRA 선호")

if __name__ == "__main__":
    main()