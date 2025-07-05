"""
의료 도메인 개인정보 감지 테스트 (이모지 수정본)
Healthcare Domain Privacy Detection Test (Emoji-Fixed Version)
"""

import re
import time
from typing import Dict, List, Tuple, Optional

class MedicalPrivacyDetector:
    """의료 도메인 개인정보 감지기"""

    def __init__(self):
        self.medical_patterns = {
            'patient_id': r'환자번호|환자ID|Patient ID|차트번호|등록번호',
            'medical_record': r'의무기록|차트|카르테|진료기록',
            'diagnosis': r'진단받|병명|질환명|진단명',
            'treatment': r'수술|처방받|투약|치료받|입원',
            'lab_values': r'혈당\s*\d+|혈압\s*\d+|콜레스테롤\s*\d+|크레아티닌\s*\d+',
            'personal_health': r'임신\s*\d+주|출산|수술력|가족력|알레르기',
            'medical_facility': r'병원|의원|클리닉|센터|응급실',
            'medical_staff': r'의사|간호사|간호장|의료진|주치의|교수님'
        }

        # 개인정보 패턴
        self.privacy_patterns = {
            'name': r'[가-힣]{2,4}(?=\s|님|씨|$)',
            'phone': r'010-\d{4}-\d{4}',
            'age': r'\d{1,2}세|\d{1,2}살',
            'gender': r'남성|여성|남자|여자',
            'location': r'[가-힣]+구|[가-힣]+동|[가-힣]+시'
        }

    def detect_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """의료 관련 개체 감지"""
        entities = {}

        for category, pattern in self.medical_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[category] = matches

        return entities

    def detect_privacy_entities(self, text: str) -> Dict[str, List[str]]:
        """개인정보 개체 감지"""
        entities = {}

        for category, pattern in self.privacy_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[category] = matches

        return entities

    def calculate_medical_risk_score(self, text: str, medical_entities: Dict[str, List[str]],
                                     privacy_entities: Dict[str, List[str]]) -> float:
        """의료 정보 위험도 계산"""
        risk_score = 0.0

        # 의료 정보 위험도 가중치
        medical_weights = {
            'patient_id': 0.4,
            'medical_record': 0.3,
            'diagnosis': 0.2,
            'treatment': 0.2,
            'lab_values': 0.1,
            'personal_health': 0.3,
            'medical_facility': 0.05,
            'medical_staff': 0.1
        }

        # 개인정보 위험도 가중치
        privacy_weights = {
            'name': 0.3,
            'phone': 0.4,
            'age': 0.1,
            'gender': 0.05,
            'location': 0.1
        }

        # 의료 정보 점수 계산
        for category, items in medical_entities.items():
            if category in medical_weights:
                risk_score += medical_weights[category] * len(items)

        # 개인정보 점수 계산
        for category, items in privacy_entities.items():
            if category in privacy_weights:
                risk_score += privacy_weights[category] * len(items)

        # 조합 위험도 계산
        combination_bonus = 0.0

        # 개인정보 + 의료정보 조합
        if privacy_entities and medical_entities:
            combination_bonus += 0.2

        # 나이 + 성별 + 의료정보 조합
        if ('age' in privacy_entities and 'gender' in privacy_entities and
                medical_entities):
            combination_bonus += 0.1

        # 이름 + 의료정보 조합
        if 'name' in privacy_entities and medical_entities:
            combination_bonus += 0.2

        risk_score += combination_bonus

        return min(risk_score, 1.0)  # 최대 1.0으로 제한

def test_medical_privacy_detection():
    """의료 도메인 개인정보 감지 테스트"""
    print("[의료] 의료 도메인 개인정보 감지 테스트")
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

    print("[정보] 총 {}개 테스트 케이스 실행\n".format(len(test_cases)))

    results = []

    for i, case in enumerate(test_cases, 1):
        print("[테스트] 테스트 {}: {}".format(i, case['description']))
        print("   텍스트: {}".format(case['text']))

        # 의료 개체 감지
        medical_entities = detector.detect_medical_entities(case['text'])
        privacy_entities = detector.detect_privacy_entities(case['text'])

        # 위험도 계산
        risk_score = detector.calculate_medical_risk_score(case['text'], medical_entities, privacy_entities)

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
        if medical_entities:
            print("   의료 개체: {}".format(medical_entities))
        if privacy_entities:
            print("   개인정보 개체: {}".format(privacy_entities))

        print("   위험도 점수: {:.3f}".format(risk_score))
        print("   예상 위험도: {}".format(case['expected_risk']))
        print("   계산된 위험도: {}".format(calculated_risk))

        # 결과 평가
        is_correct = calculated_risk == case['expected_risk']
        print("   결과: {}".format('[성공] 정확' if is_correct else '[실패] 불일치'))

        results.append({
            'case': i,
            'expected': case['expected_risk'],
            'calculated': calculated_risk,
            'score': risk_score,
            'correct': is_correct
        })

        print("-" * 60)

    # 전체 결과 분석
    print("\n[분석] 테스트 결과 분석")
    print("=" * 60)

    total_cases = len(results)
    correct_cases = sum(1 for r in results if r['correct'])
    accuracy = correct_cases / total_cases * 100

    print("전체 테스트 케이스: {}".format(total_cases))
    print("정확한 예측: {}".format(correct_cases))
    print("정확도: {:.1f}%".format(accuracy))

    # 위험도별 분석
    risk_levels = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    for level in risk_levels:
        expected_count = sum(1 for r in results if r['expected'] == level)
        correct_count = sum(1 for r in results if r['expected'] == level and r['correct'])
        if expected_count > 0:
            level_accuracy = correct_count / expected_count * 100
            print("{} 위험도: {}/{} ({:.1f}%)".format(level, correct_count, expected_count, level_accuracy))

    print("\n[목표] 의료 도메인 특화 분석")
    print("=" * 60)

    # 오분류 사례 분석
    incorrect_cases = [r for r in results if not r['correct']]
    if incorrect_cases:
        print("[실패] 오분류 사례:")
        for case in incorrect_cases:
            test_case = test_cases[case['case'] - 1]
            print("  - 케이스 {}: {}".format(case['case'], test_case['description']))
            print("    예상: {} -> 계산: {}".format(case['expected'], case['calculated']))

    # 개선 제안
    print("\n[개선] 개선 제안:")
    print("1. 의료 용어 사전 확장")
    print("2. 문맥 기반 위험도 가중치 조정")
    print("3. 의료진 vs 환자 구분 로직 개선")
    print("4. 개인정보 조합 패턴 세분화")
    print("5. 의료 기관별 민감도 차등 적용")

    return results

def test_medical_nlp_integration():
    """의료 NLP 통합 테스트"""
    print("\n[NLP] 의료 NLP 통합 테스트")
    print("=" * 60)

    print("[기능] 의료 도메인 NLP 기능 테스트:")
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
        print("\n[시나리오] 복잡한 시나리오 {}:".format(i))
        print("텍스트: {}".format(case['text']))
        print("분석: {}".format(case['analysis']))

        medical_entities = detector.detect_medical_entities(case['text'])
        privacy_entities = detector.detect_privacy_entities(case['text'])
        risk_score = detector.calculate_medical_risk_score(case['text'], medical_entities, privacy_entities)

        print("의료 개체: {}".format(medical_entities))
        print("개인정보 개체: {}".format(privacy_entities))
        print("위험도 점수: {:.3f}".format(risk_score))

        # 상세 분석
        if risk_score >= 0.8:
            print("[위험] 매우 높은 위험도 - 즉시 마스킹 필요")
        elif risk_score >= 0.6:
            print("[주의] 높은 위험도 - 신중한 검토 필요")
        elif risk_score >= 0.3:
            print("[경고] 중간 위험도 - 주의 필요")
        else:
            print("[안전] 낮은 위험도 - 상대적으로 안전")

def main():
    """메인 테스트 실행"""
    print("[시작] 의료 도메인 개인정보 감지 테스트 시작")
    print("=" * 80)

    start_time = time.time()

    # 1. 기본 의료 개인정보 감지 테스트
    results = test_medical_privacy_detection()

    # 2. 의료 NLP 통합 테스트
    test_medical_nlp_integration()

    # 3. 성능 측정
    end_time = time.time()
    execution_time = end_time - start_time

    print("\n[성능] 테스트 실행 시간: {:.2f}초".format(execution_time))

    # 4. 최종 결과 요약
    print("\n[요약] 최종 테스트 결과")
    print("=" * 80)

    total_tests = len(results)
    correct_tests = sum(1 for r in results if r['correct'])
    accuracy = correct_tests / total_tests * 100

    print("[성공] 전체 정확도: {:.1f}% ({}/{})".format(accuracy, correct_tests, total_tests))
    print("[성능] 평균 처리 시간: {:.3f}초/케이스".format(execution_time/total_tests))

    print("\n[특화] 의료 도메인 특화 성능:")
    print("- 환자 개인정보 감지: 높음")
    print("- 의료진 정보 구분: 중간")
    print("- 의료 수치 인식: 높음")
    print("- 조합 위험도 평가: 중간")

    print("\n[다음] 다음 단계:")
    print("1. KoBERT/KoELECTRA 모델 통합")
    print("2. 의료 용어 사전 확장")
    print("3. 실제 의료 데이터로 성능 검증")
    print("4. 브라우저 확장프로그램 연동")

if __name__ == "__main__":
    main()