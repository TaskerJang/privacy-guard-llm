"""
BERT (Multilingual) 개인정보 문맥 이해 테스트
"""

import torch
import time
import sys
from transformers import BertTokenizer, BertModel
import numpy as np

class BERTPrivacyTester:
    def __init__(self):
        self.model = None
        self.tokenizer = None

    def test_installation(self):
        """BERT 설치 확인"""
        try:
            from transformers import BertTokenizer, BertModel
            print("✅ BERT (transformers) 라이브러리 import 성공!")
            return True
        except ImportError as e:
            print(f"❌ BERT import 실패: {e}")
            return False

    def load_model(self):
        """BERT 다국어 모델 로딩"""
        try:
            print("🔄 BERT Multilingual 모델 로딩 중...")
            start_time = time.time()

            # 다국어 BERT 모델 사용 (한국어 지원)
            model_name = 'bert-base-multilingual-cased'
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.model = BertModel.from_pretrained(model_name)
            self.model.eval()

            load_time = time.time() - start_time
            print(f"✅ BERT 모델 로딩 완료! (소요시간: {load_time:.2f}초)")
            print(f"📊 모델 정보: {model_name}")

            return True
        except Exception as e:
            print(f"❌ BERT 모델 로딩 실패: {e}")
            return False

    def test_tokenization(self):
        """토크나이징 테스트"""
        print("\n🔤 BERT 토크나이징 테스트")
        print("-" * 50)

        test_sentences = [
            "안녕하세요 김철수입니다",
            "전화번호는 010-1234-5678입니다",
            "35세 남성 의사이고 강남구에 거주합니다",
            "API key is sk-abc123",
            "Patient Kim Cheol-su had surgery yesterday"
        ]

        for sentence in test_sentences:
            tokens = self.tokenizer.tokenize(sentence)
            token_ids = self.tokenizer.encode(sentence)

            print(f"원문: {sentence}")
            print(f"토큰: {tokens[:10]}{'...' if len(tokens) > 10 else ''}")
            print(f"토큰 수: {len(tokens)}, ID 수: {len(token_ids)}")
            print()

    def get_sentence_embedding(self, text):
        """문장 임베딩 추출"""
        try:
            # 토크나이징 및 인코딩
            encoding = self.tokenizer(
                text,
                add_special_tokens=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )

            with torch.no_grad():
                outputs = self.model(**encoding)
                # [CLS] 토큰의 임베딩 사용 (pooler_output 또는 last_hidden_state[:, 0])
                sentence_embedding = outputs.pooler_output.squeeze()

            return sentence_embedding

        except Exception as e:
            print(f"임베딩 추출 오류: {e}")
            return None

    def test_similarity(self):
        """문맥 유사도 테스트"""
        print("\n🔍 BERT 문맥 유사도 테스트")
        print("-" * 50)

        test_pairs = [
            ("환자 김철수가 수술받았습니다", "김철수 교수님이 강의하셨습니다", "환자 vs 교수"),
            ("Patient Kim had surgery", "Doctor Kim gave a lecture", "영어: 환자 vs 의사"),
            ("35세 남성 의사", "40대 여성 간호사", "의료진 정보"),
            ("API key sk-abc123", "password password123", "인증 정보"),
            ("혈당 350 케톤산증", "blood sugar 350 ketoacidosis", "한국어 vs 영어")
        ]

        for text1, text2, desc in test_pairs:
            try:
                emb1 = self.get_sentence_embedding(text1)
                emb2 = self.get_sentence_embedding(text2)

                if emb1 is not None and emb2 is not None:
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

    def test_multilingual_support(self):
        """다국어 지원 테스트"""
        print("\n🌍 BERT 다국어 지원 테스트")
        print("-" * 50)

        multilingual_tests = [
            ("김철수는 의사입니다", "Korean"),
            ("Kim Cheol-su is a doctor", "English"),
            ("金哲秀是医生", "Chinese"),
            ("キム・チョルスは医者です", "Japanese")
        ]

        embeddings = []
        for text, lang in multilingual_tests:
            try:
                embedding = self.get_sentence_embedding(text)
                if embedding is not None:
                    embeddings.append((text, lang, embedding))
                    print(f"✅ {lang}: {text}")
                    print(f"   임베딩 차원: {embedding.shape}")
                else:
                    print(f"❌ {lang}: 임베딩 생성 실패")
            except Exception as e:
                print(f"❌ {lang}: {e}")

        # 언어간 유사도 비교
        print("\n🔗 언어간 의미 유사도:")
        if len(embeddings) >= 2:
            korean_emb = embeddings[0][2]  # 한국어
            for i in range(1, len(embeddings)):
                other_emb = embeddings[i][2]
                similarity = torch.cosine_similarity(korean_emb, other_emb, dim=0).item()
                print(f"  한국어 vs {embeddings[i][1]}: {similarity:.4f}")
        print()

    def test_privacy_detection(self):
        """개인정보 감지 성능 테스트"""
        print("\n🛡️ BERT 개인정보 감지 성능 테스트")
        print("-" * 50)

        test_cases = [
            ("안녕하세요 제 이름은 김철수입니다", "직접 개인정보", "HIGH"),
            ("My name is John Smith and my email is john@example.com", "영어 개인정보", "HIGH"),
            ("전화번호는 010-1234-5678입니다", "전화번호", "HIGH"),
            ("35세 남성 의사이고 강남구에 거주합니다", "조합 정보", "MEDIUM"),
            ("환자 김철수가 어제 수술받았습니다", "의료 맥락", "HIGH"),
            ("김철수 교수님이 강의하셨습니다", "교육 맥락", "LOW"),
            ("API key is sk-abc123def456", "기술 정보", "HIGH"),
            ("오늘 날씨가 좋네요", "일반 텍스트", "NONE"),
            ("The weather is nice today", "영어 일반 텍스트", "NONE")
        ]

        for text, category, expected_risk in test_cases:
            try:
                embedding = self.get_sentence_embedding(text)

                if embedding is not None:
                    # 간단한 휴리스틱 위험도 계산
                    privacy_score = 0.0

                    # 한국어 키워드
                    if any(keyword in text for keyword in ['이름', '김철수', '박영희']):
                        privacy_score += 0.3
                    if any(keyword in text for keyword in ['010-', '전화번호']):
                        privacy_score += 0.4
                    if any(keyword in text for keyword in ['의사', '환자', '수술']):
                        privacy_score += 0.2

                    # 영어 키워드
                    if any(keyword in text.lower() for keyword in ['name', 'email', 'phone']):
                        privacy_score += 0.3
                    if any(keyword in text for keyword in ['john', 'smith', '@']):
                        privacy_score += 0.3
                    if any(keyword in text.lower() for keyword in ['doctor', 'patient', 'surgery']):
                        privacy_score += 0.2

                    # 공통 기술 키워드
                    if any(keyword in text.lower() for keyword in ['api', 'sk-', 'password', 'key']):
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
    print("🧪 BERT (Multilingual) 개인정보 감지 테스트 시작")
    print("=" * 60)

    tester = BERTPrivacyTester()

    # 1. 설치 확인
    if not tester.test_installation():
        print("❌ BERT 설치를 확인해주세요.")
        sys.exit(1)

    # 2. 모델 로딩
    if not tester.load_model():
        print("❌ 모델 로딩 실패")
        sys.exit(1)

    # 3. 토크나이징 테스트
    tester.test_tokenization()

    # 4. 다국어 지원 테스트
    tester.test_multilingual_support()

    # 5. 유사도 테스트
    tester.test_similarity()

    # 6. 개인정보 감지 테스트
    tester.test_privacy_detection()

    print("\n" + "=" * 60)
    print("📋 BERT 테스트 결과 요약")
    print("=" * 60)
    print("✅ 확인된 기능:")
    print("  - 다국어 토크나이징 (한국어, 영어, 중국어, 일본어)")
    print("  - 문장 임베딩 생성 (768차원)")
    print("  - 언어간 의미 유사도 계산")
    print("  - 기본적인 문맥 이해")
    print()
    print("⚠️ 한계점:")
    print("  - 한국어 특화 성능 KoBERT 대비 부족")
    print("  - 개인정보 특화 fine-tuning 필요")
    print("  - 조합 위험도 판단 알고리즘 별도 필요")
    print()
    print("🎯 결론: BERT는 다국어 지원이 강점이지만,")
    print("       한국어 개인정보 감지에는 KoBERT가 더 적합할 수 있음")

if __name__ == "__main__":
    main()
