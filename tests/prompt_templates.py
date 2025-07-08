"""
프롬프트 템플릿 - 도메인별 특화 프롬프트
의료, 기업, 기술, 일반 도메인에 특화된 개인정보 위험도 분석 프롬프트
"""

class PromptTemplates:
    """도메인별 프롬프트 템플릿 관리"""

    @staticmethod
    def get_medical_prompt() -> str:
        """의료 도메인 특화 프롬프트"""
        return """
당신은 의료 도메인의 개인정보 보호 전문가입니다. 
주어진 텍스트에서 개인정보 노출 위험도를 분석해주세요.

**분석 기준:**
1. 환자 개인정보 (이름, 나이, 성별, 연락처, 주소, 환자번호)
2. 의료 정보 (진단명, 처방약, 수술내용, 검사결과, 병력)
3. 의료진 정보 (의사명, 간호사명, 담당자, 의료진 연락처)
4. 의료기관 정보 (병원명, 과명, 병실번호)
5. 조합 위험도 (개인정보 + 의료정보 결합시 위험 증가)

**위험도 분류:**
- CRITICAL (90-100점): 환자 완전 식별 가능 + 민감한 의료정보
- HIGH (70-89점): 개인정보 + 의료정보 조합으로 개인 식별 가능성 높음
- MEDIUM (40-69점): 의료진 정보 또는 일반적인 의료정보
- LOW (20-39점): 비특정 의료정보 또는 일반 건강 정보
- NONE (0-19점): 개인정보 없는 일반 의료 지식

**특별 고려사항:**
- 환자번호나 차트번호가 있으면 위험도 상승
- 나이+성별+질병 조합시 식별 가능성 높음
- 의료진 개인정보도 보호 대상

텍스트: "{text}"

다음 JSON 형식으로 응답해주세요:
{{
    "risk_score": 숫자 (0-100),
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
    "detected_entities": ["감지된 개체들"],
    "explanation": "위험도 판단 근거 (구체적으로)",
    "domain": "medical",
    "recommendations": ["마스킹 권장사항"]
}}
"""

    @staticmethod
    def get_business_prompt() -> str:
        """기업 도메인 특화 프롬프트"""
        return """
당신은 기업 정보보호 전문가입니다.
주어진 텍스트에서 기업 기밀정보 및 개인정보 노출 위험도를 분석해주세요.

**분석 기준:**
1. 직원 개인정보 (이름, 연락처, 이메일, 주소, 사번)
2. 기업 기밀정보 (프로젝트명, 예산, 매출, 계약내용, 전략)
3. 거래처 정보 (파트너사명, 계약조건, 거래금액)
4. 조직 정보 (부서, 직급, 보고라인)
5. 조합 위험도 (기업정보 + 개인정보 결합시 위험 증가)

**위험도 분류:**
- CRITICAL (90-100점): 기업 핵심 기밀 + 개인정보 조합
- HIGH (70-89점): 중요 기업정보 또는 직원 개인정보
- MEDIUM (40-69점): 일반 기업정보 또는 조직 정보
- LOW (20-39점): 공개 가능한 기업 정보
- NONE (0-19점): 위험 요소 없음

텍스트: "{text}"

JSON 형식으로 응답해주세요:
{{
    "risk_score": 숫자 (0-100),
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
    "detected_entities": ["감지된 개체들"],
    "explanation": "위험도 판단 근거",
    "domain": "business",
    "recommendations": ["보안 권장사항"]
}}
"""

    @staticmethod
    def get_technical_prompt() -> str:
        """기술 도메인 특화 프롬프트"""
        return """
당신은 기술 보안 전문가입니다.
주어진 텍스트에서 기술적 민감정보 및 개인정보 노출 위험도를 분석해주세요.

**분석 기준:**
1. 개인정보 (개발자명, 연락처, 계정정보, 이메일)
2. 인증정보 (API 키, 토큰, 패스워드, 인증서)
3. 시스템 정보 (서버 IP, 데이터베이스 정보, 포트, 경로)
4. 코드 정보 (함수명, 변수명, 설정파일 내용)
5. 조합 위험도 (시스템정보 + 인증정보 결합시 위험 증가)

**위험도 분류:**
- CRITICAL (90-100점): 실제 인증 키 + 시스템 접근 정보
- HIGH (70-89점): API 키, DB 정보, 개인 인증 정보
- MEDIUM (40-69점): 시스템 구성 정보 또는 일반 기술 정보
- LOW (20-39점): 공개 기술 정보 또는 일반적인 코드
- NONE (0-19점): 위험 요소 없음

텍스트: "{text}"

JSON 형식으로 응답해주세요:
{{
    "risk_score": 숫자 (0-100),
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
    "detected_entities": ["감지된 개체들"],
    "explanation": "위험도 판단 근거",
    "domain": "technical",
    "recommendations": ["보안 권장사항"]
}}
"""

    @staticmethod
    def get_general_prompt() -> str:
        """일반 도메인 프롬프트"""
        return """
당신은 개인정보 보호 전문가입니다.
주어진 텍스트에서 개인정보 노출 위험도를 분석해주세요.

**분석 기준:**
1. 직접 개인정보 (이름, 연락처, 주소, 주민번호, 이메일)
2. 간접 개인정보 (나이, 성별, 지역, 직업, 학력)
3. 민감정보 (건강상태, 정치적 성향, 종교, 성적 지향)
4. 조합 위험도 (여러 정보 결합시 개인 식별 가능성)

**위험도 분류:**
- CRITICAL (90-100점): 완전한 개인 식별 가능 + 민감정보
- HIGH (70-89점): 직접 개인정보 또는 개인 식별 가능
- MEDIUM (40-69점): 간접 개인정보 조합
- LOW (20-39점): 비특정 개인정보
- NONE (0-19점): 개인정보 없음

텍스트: "{text}"

JSON 형식으로 응답해주세요:
{{
    "risk_score": 숫자 (0-100),
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
    "detected_entities": ["감지된 개체들"],
    "explanation": "위험도 판단 근거",
    "domain": "general",
    "recommendations": ["개인정보 보호 권장사항"]
}}
"""

    @staticmethod
    def get_all_prompts() -> dict:
        """모든 프롬프트 반환"""
        return {
            'medical': PromptTemplates.get_medical_prompt(),
            'business': PromptTemplates.get_business_prompt(),
            'technical': PromptTemplates.get_technical_prompt(),
            'general': PromptTemplates.get_general_prompt()
        }

    @staticmethod
    def detect_domain(text: str) -> str:
        """텍스트에서 도메인 자동 감지"""
        text_lower = text.lower()

        # 의료 도메인 키워드
        medical_keywords = [
            '환자', '의사', '간호사', '병원', '진료', '수술', '처방', '약물', '치료',
            '진단', '검사', '혈압', '혈당', '의료진', '입원', '외래', '응급실',
            '병력', '차트', '의무기록', '처방전', '투약', '수술실', '병동'
        ]

        # 기업 도메인 키워드
        business_keywords = [
            '프로젝트', '예산', '계약', '거래처', '매출', '직원', '부서', '회사',
            '사업', '투자', '수익', '비용', '마케팅', '영업', '고객', '클라이언트',
            '사업부', '본부', '지사', '협력사', '파트너', '계약서', '제안서'
        ]

        # 기술 도메인 키워드
        technical_keywords = [
            'api', 'database', 'server', 'token', 'key', 'password', 'config',
            '개발', '시스템', '코드', '프로그램', '데이터베이스', '서버', '네트워크',
            'url', 'endpoint', 'json', 'xml', 'sql', 'python', 'java', 'javascript',
            '배포', '운영', '모니터링', '로그', '인증', '보안', '암호화'
        ]

        # 키워드 매칭으로 도메인 판별
        medical_score = sum(1 for keyword in medical_keywords if keyword in text_lower)
        business_score = sum(1 for keyword in business_keywords if keyword in text_lower)
        technical_score = sum(1 for keyword in technical_keywords if keyword in text_lower)

        scores = {
            'medical': medical_score,
            'business': business_score,
            'technical': technical_score
        }

        # 가장 높은 점수의 도메인 선택
        max_score = max(scores.values())
        if max_score == 0:
            return 'general'

        return max(scores, key=scores.get)

if __name__ == "__main__":
    # 프롬프트 테스트
    templates = PromptTemplates()

    test_texts = [
        "35세 남성 환자 김철수가 당뇨 진단받았습니다.",
        "Phoenix 프로젝트 예산 50억원",
        "API 키 sk-abc123 설정",
        "오늘 날씨가 좋습니다."
    ]

    print("🔍 도메인 자동 감지 테스트")
    print("=" * 50)

    for text in test_texts:
        domain = templates.detect_domain(text)
        print(f"텍스트: {text}")
        print(f"감지된 도메인: {domain}")
        print()