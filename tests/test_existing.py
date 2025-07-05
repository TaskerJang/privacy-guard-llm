"""
모든 모델 테스트 결과 통합 비교 분석
"""

import os
import re
from datetime import datetime

class ModelComparisonAnalyzer:
    def __init__(self):
        self.results_dir = "results"
        self.models = {
            "KoBERT": "kobert_results.txt",
            "BERT": "bert_results.txt",
            "RoBERTa": "roberta_results.txt",
            "KoELECTRA": "koelectra_results.txt",
            "기존도구들": "existing_results.txt"
        }

    def read_result_file(self, filename):
        """결과 파일 읽기"""
        filepath = os.path.join(self.results_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return f"❌ {filename} 파일을 찾을 수 없습니다."
        except Exception as e:
            return f"❌ {filename} 읽기 오류: {e}"

    def extract_key_metrics(self, content, model_name):
        """주요 지표 추출"""
        metrics = {
            "로딩_시간": "N/A",
            "처리_속도": "N/A",
            "임베딩_차원": "N/A",
            "토큰화_품질": "N/A",
            "한국어_지원": "N/A",
            "오류_발생": "N/A"
        }

        # 로딩 시간 추출
        loading_match = re.search(r'로딩 완료.*?(\d+\.?\d*)초', content)
        if loading_match:
            metrics["로딩_시간"] = f"{loading_match.group(1)}초"

        # 처리 시간 추출
        processing_match = re.search(r'처리 시간.*?(\d+\.?\d*)ms', content)
        if processing_match:
            metrics["처리_속도"] = f"{processing_match.group(1)}ms"

        # 임베딩 차원 추출
        embedding_match = re.search(r'임베딩 차원.*?\((\d+)\)', content)
        if embedding_match:
            metrics["임베딩_차원"] = embedding_match.group(1)
        elif "768" in content:
            metrics["임베딩_차원"] = "768"

        # 오류 개수 세기
        error_count = len(re.findall(r'❌|오류|실패', content))
        metrics["오류_발생"] = f"{error_count}개"

        # 모델별 특성
        if model_name in ["KoBERT", "KoELECTRA"]:
            metrics["한국어_지원"] = "⭐⭐⭐ 우수"
        elif model_name == "BERT":
            metrics["한국어_지원"] = "⭐⭐ 다국어"
        elif model_name == "RoBERTa":
            metrics["한국어_지원"] = "⭐ 제한적"
        else:
            metrics["한국어_지원"] = "N/A"

        return metrics

    def analyze_strengths_weaknesses(self, content, model_name):
        """강점과 약점 분석"""
        strengths = []
        weaknesses = []

        # 성공 지표들
        if "✅" in content:
            success_items = re.findall(r'✅\s*([^❌\n]+)', content)
            strengths.extend(success_items[:3])  # 상위 3개만

        # 실패/한계 지표들
        if "❌" in content or "⚠️" in content:
            failure_items = re.findall(r'[❌⚠️]\s*([^✅\n]+)', content)
            weaknesses.extend(failure_items[:3])  # 상위 3개만

        # 모델별 특화 분석
        if model_name == "KoBERT":
            if "한국어" in content:
                strengths.append("한국어 특화 성능")
            if "SKT" in content:
                strengths.append("검증된 모델 (SKT)")

        elif model_name == "BERT":
            if "다국어" in content or "multilingual" in content:
                strengths.append("다국어 지원")
            if "한국어" in content and "제한" in content:
                weaknesses.append("한국어 성능 제한")

        elif model_name == "RoBERTa":
            if "영어" in content:
                strengths.append("영어 성능 우수")
            if "한국어" in content and "부족" in content:
                weaknesses.append("한국어 지원 부족")

        elif model_name == "KoELECTRA":
            if "빠른" in content or "효율" in content:
                strengths.append("효율적인 처리 속도")
            if "ELECTRA" in content:
                strengths.append("ELECTRA 구조 장점")

        return strengths[:3], weaknesses[:3]

    def generate_comparison_table(self, all_metrics):
        """비교 표 생성"""
        print("📊 모델별 성능 비교표")
        print("=" * 80)

        # 헤더
        header = f"{'모델명':<12} {'로딩시간':<10} {'처리속도':<10} {'임베딩차원':<10} {'한국어지원':<15} {'오류수':<8}"
        print(header)
        print("-" * 80)

        # 각 모델 데이터
        for model_name, metrics in all_metrics.items():
            row = f"{model_name:<12} {metrics['로딩_시간']:<10} {metrics['처리_속도']:<10} {metrics['임베딩_차원']:<10} {metrics['한국어_지원']:<15} {metrics['오류_발생']:<8}"
            print(row)

    def generate_detailed_analysis(self, all_results, all_metrics):
        """상세 분석 리포트"""
        print("\n\n📋 상세 분석 리포트")
        print("=" * 60)

        for model_name, content in all_results.items():
            print(f"\n🔍 {model_name} 분석")
            print("-" * 40)

            strengths, weaknesses = self.analyze_strengths_weaknesses(content, model_name)

            print("✅ 주요 강점:")
            for i, strength in enumerate(strengths, 1):
                print(f"  {i}. {strength.strip()}")

            print("\n⚠️ 주요 약점:")
            for i, weakness in enumerate(weaknesses, 1):
                print(f"  {i}. {weakness.strip()}")

    def generate_recommendations(self, all_results):
        """추천 사항 생성"""
        print("\n\n🎯 프로젝트 추천 사항")
        print("=" * 60)

        # 모델별 점수 계산 (임의 지표)
        scores = {}

        for model_name, content in all_results.items():
            score = 0

            # 한국어 지원 점수
            if model_name in ["KoBERT", "KoELECTRA"]:
                score += 30
            elif model_name == "BERT":
                score += 20
            elif model_name == "RoBERTa":
                score += 10

            # 성공률 점수 (✅ 개수 기반)
            success_count = len(re.findall(r'✅', content))
            score += min(success_count * 2, 30)

            # 오류율 감점 (❌ 개수 기반)
            error_count = len(re.findall(r'❌', content))
            score -= min(error_count, 20)

            # 특별 보너스
            if "우수" in content:
                score += 10
            if "빠른" in content or "효율" in content:
                score += 5

            scores[model_name] = max(score, 0)

        # 순위 매기기
        ranked_models = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        print("🏆 모델 순위 (프로젝트 적합도 기준):")
        for i, (model_name, score) in enumerate(ranked_models, 1):
            print(f"  {i}위. {model_name}: {score}점")

        # 최종 추천
        best_model = ranked_models[0][0]
        print(f"\n🥇 최종 추천 모델: {best_model}")

        if best_model == "KoBERT":
            print("📝 추천 이유: 한국어 특화, 검증된 성능, 개인정보 감지에 적합")
        elif best_model == "KoELECTRA":
            print("📝 추천 이유: 한국어 지원 + 빠른 처리 속도, 실시간 처리에 유리")
        elif best_model == "BERT":
            print("📝 추천 이유: 다국어 지원, 안정적인 성능")
        elif best_model == "RoBERTa":
            print("📝 추천 이유: 영어 텍스트 처리 우수")

        print("\n💡 구현 전략:")
        print("  1. 메인 모델로 추천 모델 사용")
        print("  2. 기존 도구들과 하이브리드 접근")
        print("  3. 조합 위험도 계산 알고리즘 별도 구현")
        print("  4. 도메인별 특화 규칙 추가")

    def generate_next_steps(self):
        """다음 단계 가이드"""
        print("\n\n🚀 다음 단계 개발 가이드")
        print("=" * 60)

        print("📅 Week 1: 기반 구조")
        print("  - 선택된 모델 fine-tuning 환경 구축")
        print("  - 개인정보 라벨링 데이터셋 준비")
        print("  - 기본 분류기 구현")

        print("\n📅 Week 2: 핵심 알고리즘")
        print("  - 조합 위험도 계산 로직 구현")
        print("  - 문맥적 민감도 가중치 시스템")
        print("  - Chrome 확장프로그램 프로토타입")

        print("\n🎯 성공 지표:")
        print("  - 개인정보 감지 정확도 85% 이상")
        print("  - 처리 속도 3초 이내 (1000자 기준)")
        print("  - 조합 위험도 판단 기능 구현")
        print("  - 실시간 브라우저 연동 동작")

def main():
    """메인 함수"""
    print("🔍 모든 모델 테스트 결과 통합 분석")
    print("=" * 60)
    print(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    analyzer = ModelComparisonAnalyzer()

    # 모든 결과 파일 읽기
    all_results = {}
    all_metrics = {}

    print("📂 결과 파일 읽기 중...")
    for model_name, filename in analyzer.models.items():
        content = analyzer.read_result_file(filename)
        all_results[model_name] = content

        if "❌" not in content[:50]:  # 파일이 정상적으로 읽힌 경우
            metrics = analyzer.extract_key_metrics(content, model_name)
            all_metrics[model_name] = metrics
            print(f"✅ {model_name}: {filename}")
        else:
            print(f"❌ {model_name}: {filename} (파일 없음)")

    print()

    # 비교 분석 수행
    if all_metrics:
        analyzer.generate_comparison_table(all_metrics)
        analyzer.generate_detailed_analysis(all_results, all_metrics)
        analyzer.generate_recommendations(all_results)
        analyzer.generate_next_steps()
    else:
        print("❌ 분석할 결과 파일이 없습니다.")
        print("💡 먼저 각 모델 테스트를 실행해주세요:")
        print("   run_all_tests.bat")

if __name__ == "__main__":
    main()
