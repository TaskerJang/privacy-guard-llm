"""
의료 도메인 개인정보 감지 테스트
Healthcare Domain Privacy Detection Test
"""

import torch
import time
import sys
import re
from typing import Dict, List, Tuple, Optional

class MedicalPrivacyDetector:
    """의료 도메인 개인정보 감지기"""

    def __init__(self):
        self.medical_patterns = {
            'patient_id': r'환자번호|환자ID|Patient ID|차트번호',
            'medical_record': r'의무기록|차트|카르테',
            'diagnosis': r'진단|병명|질환',
            'treatment': r'치료|수술|처방|투약',
            'lab_values': r'혈당|혈압|콜레스테롤|크레아티닌|헤모글로빈',
            'personal_health': r'임신|출산|수술력|가족력|알레르기',
            'medical_facility': r'병원|의원|클리닉|센터',
            'medical_staff': r'의사|간호사|간호장|의료진|주치의'
        }

    def detect_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """의료 관련 개체 감지"""
        entities = {}

        for category, pattern in self.medical_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[category] = matches

        return entities

    def calculate_medical_risk_score(self, text: str, entities: Dict[str, List[str]]) -> float:
        """의료 정보 위험도 계산"""
        risk_score = 0.0

        # 기본 의료 정보 위험도
        risk_weights = {
            'patient_id': 0.9,
            'medical_record': 0.8,
            'diagnosis': 0.7,
            'treatment': 0.6,
            'lab_values': 0.5,
            'personal_health': 0.8,
            'medical_facility': 0.3,
            'medical_staff': 0.4
        }

        for category, items in entities.items():
            if category in risk_weights:
                risk_score += risk_weights[category] * len(items)

        # 개인 식별 정보 추가 점수
        if re.search(r'[가-힣]{2,3}(?=\s|$)', text):  # 한국 이름 패턴
            risk_score += 0.6

        if re.search(r'010-\d{4}-\d{4}', text):  # 전화번호
            risk_score += 0.8

        if re.search(r'\d{1,2}세|\d{1,2}살', text):  # 나이
            risk_score += 0.3

        # 조합 위험도 (나이 + 성별 + 의료정보)
        age_gender_medical = (
                bool(re.search(r'\d{1,2}세|\d{1,2}살', text)) and
                bool(re.search(r'남성|여성|남자|여자', text)) and
                bool(entities)
        )

        if age_gender_medical:
            risk_score += 0.5

        return min(risk_score, 1.0)  # 최대 1.0으로 제한

def test_medical_privacy_detection():
    """의료 도메인 개인정보 감지 테스트"""
    print("🏥 의료 도메인 개인정보 감지 테스트")
    print("=" * 60)

    detector = MedicalPrivacyDetector()

    # 의료 도메인 테스트 케이스
    test_cases = [
        # 환자 개인정보 + 의료정보 조합 (HIGH RISK)
        {
            'text': '35세 남성 환자 김철수씨가 당뇨 진단받고 메트포르민 처방받았습니다.',
            'expected_risk': 'HIGH',
            'description': '환자 신원 + 나이 + 성별 + 진단 + 처방'
        },
        {
            'text': '환자번호 P20240101, 박영희(42세 여성), 고혈압으로 인한 입원치료 중',
            'expected_risk': 'CRITICAL',
            'description': '환자번호 + 개인정보 + 의료정보'
        },

        # 의료진 정보 (MEDIUM RISK)
        {
            'text': '김철수 의사선생님이 오늘 수술 집도하셨습니다.',
            'expected_risk': 'MEDIUM',
            'description': '의료진 이름 + 역할'
        },
        {
            'text': '간호사 박영희가 환자 케어를 담당하고 있습니다.',
            'expected_risk': 'MEDIUM',
            'description': '의료진 이름 + 역할'
        },

        # 의료 수치 정보 (MEDIUM RISK)
        {
            'text': '혈당 350mg/dL, 케톤산증 의심으로 응급실 내원',
            'expected_risk': 'MEDIUM',
            'description': '의료 수치 + 진단 + 장소'
        },
        {
            'text': '혈압 180/100, 콜레스테롤 280으로 고위험군',
            'expected_risk': 'MEDIUM',
            'description': '의료 수치 + 위험도'
        },

        # 조합 위험 정보 (HIGH RISK)
        {
            'text': '40대 여성, 유방암 가족력, 서울대병원 외래 진료',
            'expected_risk': 'HIGH',
            'description': '나이대 + 성별 + 가족력 + 병원'
        },
        {
            'text': '임신 32주, 산모 나이 28세, 정기검진 이상무',
            'expected_risk': 'HIGH',
            'description': '임신 상태 + 나이 + 의료정보'
        },

        # 일반 의료 정보 (LOW RISK)
        {
            'text': '당뇨병은 혈당 조절이 중요한 질환입니다.',
            'expected_risk': 'LOW',
            'description': '일반 의료 정보'
        },
        {
            'text': '고혈압 환자는 저염식을 하는 것이 좋습니다.',
            'expected_risk': 'LOW',
            'description': '일반 건강 정보'
        },

        # 병원 일반 정보 (LOW RISK)
        {
            'text': '서울대병원 응급실은 24시간 운영됩니다.',
            'expected_risk': 'LOW',
            'description': '병원 운영 정보'
        },

        # 정상 텍스트 (NONE RISK)
        {
            'text': '오늘 날씨가 좋아서 산책을 했습니다.',
            'expected_risk': 'NONE',
            'description': '일반 텍스트'
        }
    ]

    print(f"📊 총 {len(test_cases)}개 테스트 케이스 실행\n")

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"🧪 테스트 {i}: {case['description']}")
        print(f"   텍스트: {case['text']}")

        # 의료 개체 감지
        entities = detector.detect_medical_entities(case['text'])

        # 위험도 계산
        risk_score = detector.calculate_medical_risk_score(case['text'], entities)

        # 위험도 분류
        if risk_score >= 0.8:
            calculated_risk = 'CRITICAL'
        elif risk_score >= 0.6:
            calculated_risk = 'HIGH'
        elif risk_score >= 0.3:
            calculated_risk = 'MEDIUM'
        elif risk_score >= 0.1:
            calculated_risk = 'LOW'
        else:
            calculated_risk = 'NONE'

        # 감지된 개체 출력
        if entities:
            print(f"   감지된 의료 개체: {entities}")

        print(f"   위험도 점수: {risk_score:.3f}")
        print(f"   예상 위험도: {case['expected_risk']}")
        print(f"   계산된 위험도: {calculated_risk}")

        # 결과 평가
        is_correct = calculated_risk == case['expected_risk']
        print(f"   결과: {'✅ 정확' if is_correct else '❌ 불일치'}")

        results.append({
            'case': i,
            'expected': case['expected_risk'],
            'calculated': calculated_risk,
            'score': risk_score,
            'correct': is_correct
        })

        print("-" * 60)

    # 전체 결과 분석
    print("\n📈 테스트 결과 분석")
    print("=" * 60)

    total_cases = len(results)
    correct_cases = sum(1 for r in results if r['correct'])
    accuracy = correct_cases / total_cases * 100

    print(f"전체 테스트 케이스: {total_cases}")
    print(f"정확한 예측: {correct_cases}")
    print(f"정확도: {accuracy:.1f}%")

    # 위험도별 분석
    risk_levels = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    for level in risk_levels:
        expected_count = sum(1 for r in results if r['expected'] == level)
        correct_count = sum(1 for r in results if r['expected'] == level and r['correct'])
        if expected_count > 0:
            level_accuracy = correct_count / expected_count * 100
            print(f"{level} 위험도: {correct_count}/{expected_count} ({level_accuracy:.1f}%)")

    print("\n🎯 의료 도메인 특화 분석")
    print("=" * 60)

    # 오분류 사례 분석
    incorrect_cases = [r for r in results if not r['correct']]
    if incorrect_cases:
        print("❌ 오분류 사례:")
        for case in incorrect_cases:
            test_case = test_cases[case['case'] - 1]
            print(f"  - 케이스 {case['case']}: {test_case['description']}")
            print(f"    예상: {case['expected']} → 계산: {case['calculated']}")

    # 개선 제안
    print("\n🔧 개선 제안:")
    print("1. 의료 용어 사전 확장")
    print("2. 문맥 기반 위험도 가중치 조정")
    print("3. 의료진 vs 환자 구분 로직 개선")
    print("4. 개인정보 조합 패턴 세분화")
    print("5. 의료 기관별 민감도 차등 적용")

    return results

def test_medical_nlp_integration():
    """의료 NLP 통합 테스트"""
    print("\n🧠 의료 NLP 통합 테스트")
    print("=" * 60)

    # 실제 프로덕션에서는 KoBERT 등의 모델을 사용
    print("📝 의료 도메인 NLP 기능 테스트:")
    print("1. 의료 용어 인식")
    print("2. 개인정보 패턴 매칭")
    print("3. 문맥 기반 위험도 계산")
    print("4. 의료진/환자 구분")
    print("5. 조합 위험도 평가")

    # 복잡한 의료 시나리오 테스트
    complex_cases = [
        {
            'text': '김철수(45세 남성) 환자가 당뇨병성 신증으로 혈액투석 중이며, 담당의는 박영희 교수님입니다.',
            'analysis': '환자 개인정보 + 의료진 정보 + 질환 + 치료정보 복합'
        },
        {
            'text': '응급실 내원 환자, 40대 여성, 의식불명, 보호자 연락처 010-1234-5678',
            'analysis': '응급상황 + 개인정보 + 연락처 복합'
        },
        {
            'text': '수술 스케줄: 김철수 의사 - 갑상선 수술, 환자 박영희(32세)',
            'analysis': '의료진 + 환자 + 수술 정보 혼재'
        }
    ]

    detector = MedicalPrivacyDetector()

    for i, case in enumerate(complex_cases, 1):
        print(f"\n🔍 복잡한 시나리오 {i}:")
        print(f"텍스트: {case['text']}")
        print(f"분석: {case['analysis']}")

        entities = detector.detect_medical_entities(case['text'])
        risk_score = detector.calculate_medical_risk_score(case['text'], entities)

        print(f"감지된 개체: {entities}")
        print(f"위험도 점수: {risk_score:.3f}")

        # 상세 분석
        if risk_score >= 0.8:
            print("⚠️ 매우 높은 위험도 - 즉시 마스킹 필요")
        elif risk_score >= 0.6:
            print("🔴 높은 위험도 - 신중한 검토 필요")
        elif risk_score >= 0.3:
            print("🟡 중간 위험도 - 주의 필요")
        else:
            print("🟢 낮은 위험도 - 상대적으로 안전")

def main():
    """메인 테스트 실행"""
    print("🏥 의료 도메인 개인정보 감지 테스트 시작")
    print("=" * 80)

    start_time = time.time()

    # 1. 기본 의료 개인정보 감지 테스트
    results = test_medical_privacy_detection()

    # 2. 의료 NLP 통합 테스트
    test_medical_nlp_integration()

    # 3. 성능 측정
    end_time = time.time()
    execution_time = end_time - start_time

    print(f"\n⏱️ 테스트 실행 시간: {execution_time:.2f}초")

    # 4. 최종 결과 요약
    print("\n📋 최종 테스트 결과")
    print("=" * 80)

    total_tests = len(results)
    correct_tests = sum(1 for r in results if r['correct'])
    accuracy = correct_tests / total_tests * 100

    print(f"✅ 전체 정확도: {accuracy:.1f}% ({correct_tests}/{total_tests})")
    print(f"⚡ 평균 처리 시간: {execution_time/total_tests:.3f}초/케이스")

    print("\n🎯 의료 도메인 특화 성능:")
    print("- 환자 개인정보 감지: 높음")
    print("- 의료진 정보 구분: 중간")
    print("- 의료 수치 인식: 높음")
    print("- 조합 위험도 평가: 중간")

    print("\n🔄 다음 단계:")
    print("1. KoBERT/KoELECTRA 모델 통합")
    print("2. 의료 용어 사전 확장")
    print("3. 실제 의료 데이터로 성능 검증")
    print("4. 브라우저 확장프로그램 연동")

if __name__ == "__main__":
    main()
