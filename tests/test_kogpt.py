import os
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
import json
from datetime import datetime

class SKTKoGPTPrivacyDetector:
    def __init__(self):
        """SKT KoGPT2 기반 개인정보 위험도 판단 및 설명 생성기"""
        print("SKT KoGPT2 모델 로딩 중...")

        self.model_name = "skt/kogpt2-base-v2"

        try:
            # SKT KoGPT2 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # 패딩 토큰 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # SKT KoGPT2 모델 로드 (CPU 최적화)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )

            self.device = "cpu"
            self.model.eval()

            print(f"SKT KoGPT2 로딩 완료 - 디바이스: {self.device}")
            print(f"모델 파라미터 수: {sum(p.numel() for p in self.model.parameters()) / 1e6:.1f}M")

        except Exception as e:
            print(f"[ERROR] SKT KoGPT2 로딩 실패: {str(e)}")
            raise

    def analyze_privacy_risk(self, text, max_new_tokens=50):
        """
        개인정보 위험도 분석 및 설명 생성

        Args:
            text (str): 분석할 텍스트
            max_new_tokens (int): 생성할 최대 새 토큰 수

        Returns:
            dict: 위험도 점수, 설명, 카테고리 등
        """

        # SKT KoGPT2에 최적화된 프롬프트
        prompt = f"다음 문장을 분석하여 개인정보 위험도를 판단하세요.\n문장: {text}\n위험도:"

        try:
            # 토크나이징 (올바른 파라미터 사용)
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=150,
                truncation=True,
                padding=False
            )

            print(f"[DEBUG] 프롬프트: {prompt}")
            print(f"[DEBUG] 입력 토큰 길이: {len(inputs['input_ids'][0])}")

            with torch.no_grad():
                # 텍스트 생성
                outputs = self.model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs.get('attention_mask'),
                    max_new_tokens=max_new_tokens,
                    num_return_sequences=1,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=2
                )

            # 결과 디코딩
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            print(f"[DEBUG] 생성된 전체 텍스트: {generated_text}")

            # 프롬프트 제거하여 응답만 추출
            if prompt in generated_text:
                response = generated_text[len(prompt):].strip()
            else:
                # 프롬프트가 정확히 일치하지 않는 경우 다른 방법 시도
                response = generated_text.split("위험도:")[-1].strip()

            print(f"[DEBUG] 추출된 응답: {response}")

            # 응답이 너무 짧거나 의미없으면 규칙 기반 사용
            if len(response) < 5 or not any(c.isalpha() for c in response):
                print("[DEBUG] 생성된 응답이 부족함 - 규칙 기반 사용")
                return self._rule_based_analysis(text)

            # 위험도 추출
            risk_level = self._extract_risk_level(response, text)

            return {
                "text": text,
                "risk_level": risk_level,
                "explanation": response[:150],  # 길이 제한
                "model": "SKT-KoGPT2-Generated",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"[ERROR] 생성 오류: {str(e)}")
            print("[DEBUG] 규칙 기반 분석으로 전환")
            return self._rule_based_analysis(text)

    def _extract_risk_level(self, response, original_text):
        """생성된 응답과 원본 텍스트에서 위험도 레벨 추출"""
        response_lower = response.lower()
        text_lower = original_text.lower()

        # 한국어 + 영어 키워드
        high_keywords = ["높음", "위험", "high", "개인정보", "민감", "유출", "식별", "문제"]
        medium_keywords = ["보통", "중간", "medium", "주의", "확인", "가능성"]
        low_keywords = ["낮음", "안전", "low", "문제없", "괜찮", "safe"]

        # 키워드 점수 계산
        high_score = sum(2 for keyword in high_keywords if keyword in response_lower)
        medium_score = sum(1 for keyword in medium_keywords if keyword in response_lower)
        low_score = sum(1 for keyword in low_keywords if keyword in response_lower)

        # 원본 텍스트의 명백한 개인정보 확인
        obvious_personal = ["010-", "011-", "주민", "@", "번호", "계좌"]
        obvious_count = sum(1 for pattern in obvious_personal if pattern in text_lower)

        print(f"[DEBUG] 위험도 점수 - High: {high_score}, Medium: {medium_score}, Low: {low_score}, Obvious: {obvious_count}")

        # 종합 판단
        if obvious_count >= 2 or high_score >= 2:
            return "HIGH"
        elif obvious_count >= 1 or high_score >= 1 or medium_score >= 2:
            return "MEDIUM"
        elif low_score >= 1:
            return "LOW"
        else:
            return "UNKNOWN"

    def _rule_based_analysis(self, text):
        """개선된 규칙 기반 분석 (모델 실패시 대안)"""

        # 정교한 개인정보 패턴
        high_risk_patterns = {
            "phone": ["010-", "011-", "016-", "017-", "018-", "019-", "전화", "핸드폰", "휴대폰"],
            "email": ["@", "이메일", "메일", ".com", ".net", ".org"],
            "id_number": ["주민", "번호", "생년월일", "등록번호"],
            "account": ["계좌", "카드번호", "신용카드", "체크카드"],
            "address": ["주소", "도로명", "번지", "동", "구", "시", "아파트"]
        }

        medium_risk_patterns = {
            "demographic": ["세", "나이", "남성", "여성", "출생"],
            "occupation": ["의사", "간호사", "교사", "직업", "회사", "병원", "학교"],
            "location": ["거주", "살고", "지역", "동네"],
            "medical": ["환자", "진료", "병명", "질병", "수술", "치료"],
            "personal": ["이름", "성명", "본명"]
        }

        # 패턴 매칭 및 점수 계산
        found_patterns = {}
        total_score = 0

        text_lower = text.lower()

        # HIGH 위험 패턴 확인
        for category, patterns in high_risk_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    found_patterns[category] = found_patterns.get(category, 0) + 1
                    total_score += 3

        # MEDIUM 위험 패턴 확인
        for category, patterns in medium_risk_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    found_patterns[category] = found_patterns.get(category, 0) + 1
                    total_score += 1

        # 조합 위험도 가중치
        pattern_categories = list(found_patterns.keys())
        combo_bonus = 0

        for i, cat1 in enumerate(pattern_categories):
            for cat2 in pattern_categories[i+1:]:
                # 개인정보 + 식별정보 조합
                if (cat1 in high_risk_patterns and cat2 in medium_risk_patterns) or \
                        (cat1 in medium_risk_patterns and cat2 in high_risk_patterns):
                    combo_bonus += 2
                    total_score += 2

        # 위험도 결정
        if total_score >= 6:
            risk_level = "HIGH"
            explanation = f"고위험 패턴 (점수: {total_score})"
        elif total_score >= 3:
            risk_level = "MEDIUM"
            explanation = f"중위험 패턴 (점수: {total_score})"
        elif total_score >= 1:
            risk_level = "LOW"
            explanation = f"저위험 패턴 (점수: {total_score})"
        else:
            risk_level = "SAFE"
            explanation = "개인정보 패턴 미발견"

        # 발견된 패턴 상세
        pattern_details = []
        for category, count in found_patterns.items():
            pattern_details.append(f"{category}({count})")

        detailed_explanation = f"{explanation}"
        if pattern_details:
            detailed_explanation += f", 패턴: {', '.join(pattern_details)}"
        if combo_bonus > 0:
            detailed_explanation += f", 조합가산: +{combo_bonus}"

        return {
            "text": text,
            "risk_level": risk_level,
            "explanation": f"[규칙기반] {detailed_explanation}",
            "risk_score": total_score,
            "found_patterns": found_patterns,
            "model": "SKT-KoGPT2-Rules",
            "timestamp": datetime.now().isoformat()
        }

    def batch_analyze(self, texts):
        """여러 텍스트 일괄 분석"""
        results = []

        print(f"SKT KoGPT2로 {len(texts)}개 텍스트 분석 시작...")

        for i, text in enumerate(texts):
            print(f"\n진행률: {i+1}/{len(texts)} - 분석 중: {text[:30]}...")

            result = self.analyze_privacy_risk(text)
            results.append(result)

            # CPU 메모리 관리
            if i % 3 == 0:
                import gc
                gc.collect()

        return results

def main():
    """SKT KoGPT2 테스트 메인 함수"""
    print("=" * 60)
    print("SKT KoGPT2 개인정보 위험도 분석 테스트")
    print("=" * 60)

    # 시스템 정보
    print(f"Python 버전: {sys.version}")
    print(f"PyTorch 버전: {torch.__version__}")
    print(f"실행 환경: CPU (GPU 없음)")

    # 테스트 데이터
    test_cases = [
        # 명확한 개인정보 (HIGH 예상)
        "김철수 010-1234-5678",
        "주민등록번호 123456-1234567",
        "이메일 kim@naver.com",

        # 조합 위험 정보 (MEDIUM 예상)
        "35세 남성 의사 강남구 거주",
        "환자 이름 김철수 수술 받음",
        "40대 여성 당뇨병 환자",

        # 간접 정보 (LOW 예상)
        "회사 프로젝트 예산 관련",
        "병원에서 진료 받았음",

        # 안전한 문장 (SAFE 예상)
        "오늘 날씨가 정말 좋네요",
        "파이썬 프로그래밍 공부 중"
    ]

    try:
        # SKT KoGPT2 분석기 초기화
        detector = SKTKoGPTPrivacyDetector()

        # 분석 실행
        start_time = time.time()
        results = detector.batch_analyze(test_cases)
        end_time = time.time()

        # 결과 출력
        print("\n" + "=" * 60)
        print("SKT KoGPT2 분석 결과")
        print("=" * 60)

        generated_count = 0
        rule_based_count = 0

        for i, result in enumerate(results):
            print(f"\n[테스트 케이스 {i+1}]")
            print(f"텍스트: {result['text']}")
            print(f"위험도: {result['risk_level']}")
            print(f"분석 방식: {result['model']}")
            print(f"설명: {result['explanation'][:80]}...")

            if "Generated" in result['model']:
                generated_count += 1
            else:
                rule_based_count += 1

            print("-" * 40)

        # 성능 통계
        processing_time = end_time - start_time
        print(f"\n처리 시간: {processing_time:.2f}초")
        print(f"평균 처리 시간: {processing_time / len(test_cases):.2f}초/건")
        print(f"GPT 생성 성공: {generated_count}건")
        print(f"규칙 기반 사용: {rule_based_count}건")
        print(f"GPT 생성 성공률: {generated_count/len(test_cases)*100:.1f}%")

        # 위험도 분포
        risk_counts = {}
        for result in results:
            risk_level = result['risk_level']
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

        print(f"\n위험도 분포:")
        for level, count in risk_counts.items():
            print(f"  {level}: {count}건 ({count/len(results)*100:.1f}%)")

        # 결과 저장
        save_results(results, start_time, end_time, generated_count, rule_based_count)

    except Exception as e:
        print(f"[ERROR] 전체 실행 실패: {str(e)}")
        import traceback
        traceback.print_exc()

def save_results(results, start_time, end_time, generated_count, rule_based_count):
    """결과를 파일에 저장"""

    # results 폴더가 없으면 생성
    os.makedirs("../../results", exist_ok=True)

    # 결과 파일
    result_file = "../../results/kogpt_results.txt"
    json_file = "../../results/kogpt_results.json"

    with open(result_file, "w", encoding="utf-8") as f:
        f.write("SKT KoGPT2 개인정보 위험도 분석 결과\n")
        f.write("=" * 60 + "\n")
        f.write(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"처리 시간: {end_time - start_time:.2f}초\n")
        f.write(f"테스트 케이스 수: {len(results)}개\n")
        f.write(f"GPT 생성 성공: {generated_count}건\n")
        f.write(f"규칙 기반 사용: {rule_based_count}건\n")
        f.write(f"GPT 생성 성공률: {generated_count/len(results)*100:.1f}%\n\n")

        for i, result in enumerate(results):
            f.write(f"[테스트 케이스 {i+1}]\n")
            f.write(f"텍스트: {result['text']}\n")
            f.write(f"위험도: {result['risk_level']}\n")
            f.write(f"분석 방식: {result['model']}\n")
            f.write(f"설명: {result['explanation']}\n")
            f.write(f"타임스탬프: {result['timestamp']}\n")
            f.write("-" * 40 + "\n")

    # JSON 저장
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "model": "SKT-KoGPT2",
            "test_time": datetime.now().isoformat(),
            "processing_time": end_time - start_time,
            "total_cases": len(results),
            "generated_success": generated_count,
            "rule_based_count": rule_based_count,
            "success_rate": generated_count/len(results)*100,
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장 완료:")
    print(f"  - 상세 결과: {result_file}")
    print(f"  - JSON 결과: {json_file}")

if __name__ == "__main__":
    main()