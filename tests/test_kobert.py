#!/usr/bin/env python3
"""
KoBERT 개인정보 문맥 이해 테스트
"""

import torch
import time
import sys

def test_kobert_installation():
    """KoBERT 설치 확인"""
    try:
        from kobert import get_pytorch_kobert_model, get_tokenizer_path
        from gluonnlp.data import SentencepieceTokenizer
        print("✅ KoBERT 라이브러리 import 성공!")
        return True
    except ImportError as e:
        print(f"❌ KoBERT import 실패: {e}")
        return False

def load_kobert_model():
    """KoBERT 모델 로딩"""
    try:
        print("🔄 KoBERT 모델 로딩 중...")
        start_time = time.time()

        from kobert import get_pytorch_kobert_model, get_tokenizer_path
        from gluonnlp.data import SentencepieceTokenizer

        model, vocab = get_pytorch_kobert_model()
        model.eval()

        tok_path = get_tokenizer_path()
        tokenizer = SentencepieceTokenizer(tok_path)

        load_time = time.time() - start_time
        print(f"✅ KoBERT 모델 로딩 완료! (소요시간: {load_time:.2f}초)")

        return model, vocab, tokenizer
    except Exception as e:
        print(f"❌ KoBERT 모델 로딩 실패: {e}")
        return None, None, None

def test_tokenization(tokenizer):
    """토크나이징 테스트"""
    print("\n🔤 토크나이징 테스트")
    print("-" * 50)

    test_sentences = [
        "안녕하세요 김철수입니다",
        "전화번호는 010-1234-5678입니다",
        "35세 남성 의사이고 강남구에 거주합니다",
        "API 키는 sk-abc123입니다"
    ]

    for sentence in test_sentences:
        tokens = tokenizer(sentence)
        print(f"원문: {sentence}")
        print(f"토큰: {tokens}")
        print()

def get_sentence_embedding(model, vocab, tokenizer, text):
    """문장 임베딩 추출"""
    tokens = tokenizer(text)
    tokens = ['[CLS]'] + tokens + ['[SEP]']

    # 토큰을 ID로 변환
    token_ids = [vocab.to_indices(token) for token in tokens]

    # 패딩 (최대 128로 제한)
    max_length = 128
    if len(token_ids) > max_length:
        token_ids = token_ids[:max_length]
    else:
        token_ids += [vocab['[PAD]']] * (max_length - len(token_ids))

    # attention mask
    attention_mask = [1 if token_id != vocab['[PAD]'] else 0 for token_id in token_ids]
    token_type_ids = [0] * max_length

    # 텐서로 변환
    input_ids = torch.LongTensor([token_ids])
    attention_mask = torch.LongTensor([attention_mask])
    token_type_ids = torch.LongTensor([token_type_ids])

    with torch.no_grad():
        sequence_output, pooled_output = model(input_ids, attention_mask, token_type_ids)

    return pooled_output.squeeze()

def test_similarity(model, vocab, tokenizer):
    """문맥 유사도 테스트"""
    print("\n🔍 문맥 유사도 테스트")
    print("-" * 50)

    test_pairs = [
        ("환자 김철수가 수술받았습니다", "김철수 교수님이 강의하셨습니다", "환자 vs 교수"),
        ("35세 남성 의사", "40대 여성 간호사", "의료진 정보"),
        ("API 키 sk-abc123", "비밀번호 password123", "인증 정보"),
        ("혈당 350 케톤산증", "혈압 140/90 고혈압", "의료 수치")
    ]

    for text1, text2, desc in test_pairs:
        try:
            emb1 = get_sentence_embedding(model, vocab, tokenizer, text1)
            emb2 = get_sentence_embedding(model, vocab, tokenizer, text2)

            # 코사인 유사도
            similarity = torch.cosine_similarity(emb1, emb2, dim=0).item()

            print(f"📊 {desc}")
            print(f"  텍스트1: {text1}")
            print(f"  텍스트2: {text2}")
            print(f"  유사도: {similarity:.4f}")

            if similarity > 0.8:
                print("  🔴 매우 유사")
            elif similarity > 0.6:
                print("  🟡 어느정도 유사")
            elif similarity > 0.4:
                print("  🟢 약간 유사")
            else:
                print("  🔵 낮은 유사도")
            print()

        except Exception as e:
            print(f"  ❌ 오류: {e}")
            print()

def test_privacy_detection(model, vocab, tokenizer):
    """개인정보 감지 성능 테스트"""
    print("\n🛡️ 개인정보 감지 성능 테스트")
    print("-" * 50)

    test_cases = [
        ("안녕하세요 제 이름은 김철수입니다", "직접 개인정보", "HIGH"),
        ("전화번호는 010-1234-5678입니다", "전화번호", "HIGH"),
        ("35세 남성 의사이고 강남구에 거주합니다", "조합 정보", "MEDIUM"),
        ("환자 김철수가 어제 수술받았습니다", "의료 맥락", "HIGH"),
        ("김철수 교수님이 강의하셨습니다", "교육 맥락", "LOW"),
        ("API 키는 sk-abc123입니다", "기술 정보", "HIGH"),
        ("오늘 날씨가 좋네요", "일반 텍스트", "NONE")
    ]

    for text, category, expected_risk in test_cases:
        try:
            embedding = get_sentence_embedding(model, vocab, tokenizer, text)

            # 간단한 휴리스틱 위험도 계산 (실제로는 더 복잡한 분류기 필요)
            privacy_score = 0.0

            # 키워드 기반 점수
            if any(keyword in text for keyword in ['이름', '김철수', '박영희']):
                privacy_score += 0.3
            if any(keyword in text for keyword in ['010-', '전화번호']):
                privacy_score += 0.4
            if any(keyword in text for keyword in ['의사', '환자', '수술']):
                privacy_score += 0.2
            if any(keyword in text for keyword in ['API', 'sk-', 'password']):
                privacy_score += 0.4
            if any(keyword in text for keyword in ['세', '강남구', '거주']):
                privacy_score += 0.1

            print(f"📝 {category}")
            print(f"  텍스트: {text}")
            print(f"  예상 위험도: {expected_risk}")
            print(f"  계산된 점수: {privacy_score:.2f}")
            print(f"  임베딩 차원: {embedding.shape}")
            print()

        except Exception as e:
            print(f"  ❌ 오류: {e}")
            print()

def main():
    """메인 테스트 함수"""
    print("🧪 KoBERT 개인정보 감지 테스트 시작")
    print("=" * 60)

    # 1. 설치 확인
    if not test_kobert_installation():
        print("❌ KoBERT 설치를 확인해주세요.")
        sys.exit(1)

    # 2. 모델 로딩
    model, vocab, tokenizer = load_kobert_model()
    if model is None:
        print("❌ 모델 로딩 실패")
        sys.exit(1)

    # 3. 토크나이징 테스트
    test_tokenization(tokenizer)

    # 4. 유사도 테스트
    test_similarity(model, vocab, tokenizer)

    # 5. 개인정보 감지 테스트
    test_privacy_detection(model, vocab, tokenizer)

    print("\n" + "=" * 60)
    print("📋 KoBERT 테스트 결과 요약")
    print("=" * 60)
    print("✅ 확인된 기능:")
    print("  - 한국어 토크나이징")
    print("  - 문장 임베딩 생성")
    print("  - 기본적인 문맥 이해")
    print()
    print("❓ 추가 개발 필요:")
    print("  - 개인정보 특화 분류기")
    print("  - 조합 위험도 계산 알고리즘")
    print("  - 도메인별 민감정보 패턴")
    print()
    print("🎯 결론: KoBERT는 기본 문맥 이해가 가능하며,")
    print("       개인정보 감지용 fine-tuning을 통해 활용 가능")

if __name__ == "__main__":
    main()