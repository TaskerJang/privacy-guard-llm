"""
테스트 케이스 - 다양한 도메인별 개인정보 위험도 테스트 시나리오
"""

class TestCases:
    """테스트 케이스 관리"""

    @staticmethod
    def get_medical_cases():
        """의료 도메인 테스트 케이스"""
        return [
            {
                'text': '환자 김철수(45세 남성, 010-1234-5678)가 당뇨병성 신증으로 혈액투석 중이며, 담당의 박영희 교수님께서 신장이식 검토 중입니다.',
                'expected_risk': 'CRITICAL',
                'domain': 'medical',
                'description': '환자 개인정보 + 의료진 + 복잡한 의료정보 조합'
            },
            {
                'text': '환자번호 P20240101, 박영희(42세 여성), 고혈압으로 인한 입원치료 중, 3병동 301호',
                'expected_risk': 'CRITICAL',
                'domain': 'medical',
                'description': '환자번호 + 개인정보 + 의료정보 + 병실정보'
            },
            {
                'text': '혈당 350mg/dL, 케톤산증 의심으로 응급실 내원한 40대 여성',
                'expected_risk': 'HIGH',
                'domain': 'medical',
                'description': '의료 수치 + 나이/성별 조합'
            },
            {
                'text': '김철수 의사선생님이 오늘 수술을 집도하셨습니다. 연락처 010-5678-9012',
                'expected_risk': 'HIGH',
                'domain': 'medical',
                'description': '의료진 개인정보 + 연락처'
            },
            {
                'text': '30대 남성 환자의 혈압이 180/100으로 측정되었습니다.',
                'expected_risk': 'MEDIUM',
                'domain': 'medical',
                'description': '나이대 + 성별 + 의료 수치'
            },
            {
                'text': '당뇨병 환자의 혈당 관리 방법에 대한 일반적인 가이드라인',
                'expected_risk': 'LOW',
                'domain': 'medical',
                'description': '일반 의료 정보'
            },
            {
                'text': '고혈압은 조용한 살인자로 불리는 질환입니다.',
                'expected_risk': 'NONE',
                'domain': 'medical',
                'description': '일반 의료 지식'
            }
        ]

    @staticmethod
    def get_business_cases():
        """기업 도메인 테스트 케이스"""
        return [
            {
                'text': 'Phoenix 프로젝트 예산 50억원, 담당자 김철수 (010-1234-5678), 삼성전자와 계약 체결 예정',
                'expected_risk': 'CRITICAL',
                'domain': 'business',
                'description': '프로젝트 기밀 + 개인정보 + 거래처 정보'
            },
            {
                'text': '직원 박영희(마케팅팀, 010-5678-9012, yhpark@company.com) 2024년 연봉 7천만원',
                'expected_risk': 'CRITICAL',
                'domain': 'business',
                'description': '직원 개인정보 + 급여 정보'
            },
            {
                'text': '올해 3분기 매출 목표는 전년 대비 15% 증가한 120억원으로 설정',
                'expected_risk': 'MEDIUM',
                'domain': 'business',
                'description': '기업 재무 정보'
            },
            {
                'text': '마케팅팀 김철수 팀장이 신규 캠페인을 기획 중입니다.',
                'expected_risk': 'MEDIUM',
                'domain': 'business',
                'description': '직원 이름 + 부서 + 직급'
            },
            {
                'text': '회사의 비전은 글로벌 IT 리더가 되는 것입니다.',
                'expected_risk': 'LOW',
                'domain': 'business',
                'description': '일반 기업 정보'
            },
            {
                'text': '효율적인 업무 프로세스 개선 방안을 논의했습니다.',
                'expected_risk': 'NONE',
                'domain': 'business',
                'description': '일반 업무 내용'
            }
        ]

    @staticmethod
    def get_technical_cases():
        """기술 도메인 테스트 케이스"""
        return [
            {
                'text': 'API 키 sk-proj-abc123456, 데이터베이스 서버 192.168.1.100:3306, 관리자 계정 admin@company.com/password123',
                'expected_risk': 'CRITICAL',
                'domain': 'technical',
                'description': 'API 키 + 시스템 정보 + 계정 정보'
            },
            {
                'text': 'AWS 접근 키 AKIA1234567890, 비밀 키 wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                'expected_risk': 'CRITICAL',
                'domain': 'technical',
                'description': 'AWS 인증 정보'
            },
            {
                'text': '개발자 김철수(kcs@company.com)가 production 서버에 배포 완료',
                'expected_risk': 'HIGH',
                'domain': 'technical',
                'description': '개발자 개인정보 + 시스템 정보'
            },
            {
                'text': '데이터베이스 연결 문자열: mysql://user:pass@localhost:3306/mydb',
                'expected_risk': 'HIGH',
                'domain': 'technical',
                'description': '데이터베이스 연결 정보'
            },
            {
                'text': '서버 IP 주소는 192.168.1.100이고 포트는 8080입니다.',
                'expected_risk': 'MEDIUM',
                'domain': 'technical',
                'description': '서버 정보'
            },
            {
                'text': 'Python Flask 프레임워크를 사용해서 웹 API를 개발했습니다.',
                'expected_risk': 'LOW',
                'domain': 'technical',
                'description': '일반 기술 정보'
            },
            {
                'text': 'MySQL 데이터베이스 최적화를 위한 인덱스 설정 방법',
                'expected_risk': 'NONE',
                'domain': 'technical',
                'description': '일반 기술 가이드'
            }
        ]

    @staticmethod
    def get_general_cases():
        """일반 도메인 테스트 케이스"""
        return [
            {
                'text': '김철수(35세, 서울 강남구 거주, 010-1234-5678, kim@example.com, 주민번호 850101-1234567)가 온라인 쇼핑몰에서 구매',
                'expected_risk': 'CRITICAL',
                'domain': 'general',
                'description': '완전한 개인정보 조합'
            },
            {
                'text': '박영희 씨(42세 여성, 부산 해운대구, 010-5678-9012)가 아파트 임대 문의',
                'expected_risk': 'HIGH',
                'domain': 'general',
                'description': '개인정보 + 위치 정보'
            },
            {
                'text': '이철수 님의 신용카드 번호는 1234-5678-9012-3456입니다.',
                'expected_risk': 'HIGH',
                'domain': 'general',
                'description': '이름 + 금융 정보'
            },
            {
                'text': '30대 남성이 온라인으로 책을 주문했습니다.',
                'expected_risk': 'MEDIUM',
                'domain': 'general',
                'description': '나이대 + 성별 정보'
            },
            {
                'text': '서울 거주 직장인들의 출퇴근 패턴을 분석했습니다.',
                'expected_risk': 'LOW',
                'domain': 'general',
                'description': '일반화된 그룹 정보'
            },
            {
                'text': '오늘 날씨가 좋아서 한강에서 산책했습니다.',
                'expected_risk': 'NONE',
                'domain': 'general',
                'description': '개인정보 없는 일반 텍스트'
            }
        ]

    @staticmethod
    def get_all_cases():
        """모든 테스트 케이스 반환"""
        all_cases = []
        all_cases.extend(TestCases.get_medical_cases())
        all_cases.extend(TestCases.get_business_cases())
        all_cases.extend(TestCases.get_technical_cases())
        all_cases.extend(TestCases.get_general_cases())
        return all_cases

    @staticmethod
    def get_cases_by_domain(domain):
        """특정 도메인의 테스트 케이스 반환"""
        domain_map = {
            'medical': TestCases.get_medical_cases,
            'business': TestCases.get_business_cases,
            'technical': TestCases.get_technical_cases,
            'general': TestCases.get_general_cases
        }

        if domain in domain_map:
            return domain_map[domain]()
        else:
            raise ValueError(f"지원하지 않는 도메인: {domain}")

    @staticmethod
    def get_cases_by_risk_level(risk_level):
        """특정 위험도 레벨의 테스트 케이스 반환"""
        all_cases = TestCases.get_all_cases()
        return [case for case in all_cases if case['expected_risk'] == risk_level]

    @staticmethod
    def get_high_risk_cases():
        """고위험 테스트 케이스만 반환 (CRITICAL, HIGH)"""
        all_cases = TestCases.get_all_cases()
        return [case for case in all_cases if case['expected_risk'] in ['CRITICAL', 'HIGH']]

    @staticmethod
    def get_sample_cases(count=5):
        """샘플 테스트 케이스 (각 도메인에서 하나씩 + 추가)"""
        sample_cases = []

        # 각 도메인에서 하나씩
        sample_cases.append(TestCases.get_medical_cases()[0])
        sample_cases.append(TestCases.get_business_cases()[0])
        sample_cases.append(TestCases.get_technical_cases()[0])
        sample_cases.append(TestCases.get_general_cases()[0])

        # 추가 케이스
        if count > 4:
            all_cases = TestCases.get_all_cases()
            remaining = count - 4
            for i in range(remaining):
                if i < len(all_cases) - 4:
                    sample_cases.append(all_cases[i + 4])

        return sample_cases[:count]

    @staticmethod
    def print_summary():
        """테스트 케이스 요약 출력"""
        print("📋 테스트 케이스 요약")
        print("=" * 60)

        domains = ['medical', 'business', 'technical', 'general']
        total_cases = 0

        for domain in domains:
            cases = TestCases.get_cases_by_domain(domain)
            total_cases += len(cases)
            print(f"\n🏷️  {domain.upper()} 도메인: {len(cases)}개")

            # 위험도별 분포
            risk_counts = {}
            for case in cases:
                risk = case['expected_risk']
                risk_counts[risk] = risk_counts.get(risk, 0) + 1

            for risk, count in sorted(risk_counts.items()):
                print(f"   {risk}: {count}개")

        print(f"\n📊 총 테스트 케이스: {total_cases}개")

        # 전체 위험도 분포
        all_cases = TestCases.get_all_cases()
        risk_distribution = {}
        for case in all_cases:
            risk = case['expected_risk']
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1

        print(f"\n⚠️  전체 위험도 분포:")
        for risk, count in sorted(risk_distribution.items()):
            percentage = (count / total_cases) * 100
            print(f"   {risk}: {count}개 ({percentage:.1f}%)")

if __name__ == "__main__":
    # 테스트 케이스 요약 출력
    TestCases.print_summary()

    print(f"\n🔍 샘플 테스트 케이스:")
    sample_cases = TestCases.get_sample_cases(3)
    for i, case in enumerate(sample_cases, 1):
        print(f"\n{i}. {case['description']}")
        print(f"   도메인: {case['domain']}")
        print(f"   텍스트: {case['text']}")
        print(f"   예상 위험도: {case['expected_risk']}")