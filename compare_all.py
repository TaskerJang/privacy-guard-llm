import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

def load_model_results():
    """모든 모델의 결과를 로드"""
    models_data = {}

    # 기존 모델들
    model_files = {
        "KoBERT": "results/kobert_results.json",
        "BERT": "results/bert_results.json",
        "RoBERTa": "results/roberta_results.json",
        "KoELECTRA": "results/koelectra_results.json",
        "KoGPT": "results/kogpt_results.json",          # 새로 추가
        "KoSimCSE": "results/kosimcse_results.json",    # 새로 추가
        "Existing": "results/existing_results.json"
    }

    for model_name, file_path in model_files.items():
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    models_data[model_name] = json.load(f)
                print(f"[OK] {model_name} 결과 로드 완료")
            else:
                print(f"[WARNING] {model_name} 결과 파일 없음: {file_path}")
        except Exception as e:
            print(f"[ERROR] {model_name} 로드 오류: {str(e)}")

    return models_data

def analyze_model_performance(models_data):
    """모델 성능 분석"""

    performance_summary = {}

    for model_name, data in models_data.items():
        if not data or "results" not in data:
            continue

        results = data["results"]

        # 기본 통계
        total_cases = len(results)
        processing_time = data.get("processing_time", 0)
        avg_time_per_case = processing_time / total_cases if total_cases > 0 else 0

        # 위험도 분포 계산
        risk_distribution = {}
        error_count = 0

        for result in results:
            risk_level = result.get("risk_level", "UNKNOWN")
            if risk_level == "ERROR":
                error_count += 1
            else:
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

        # 모델별 특별 분석
        special_metrics = {}

        if model_name == "KoGPT":
            # 설명 생성 품질 분석
            explanation_lengths = []
            for result in results:
                explanation = result.get("explanation", "")
                explanation_lengths.append(len(explanation))

            special_metrics = {
                "avg_explanation_length": np.mean(explanation_lengths) if explanation_lengths else 0,
                "explanation_quality": "생성형 설명 제공"
            }

        elif model_name == "KoSimCSE":
            # 유사도 분석
            similarities = []
            for result in results:
                sim = result.get("max_similarity", 0)
                if sim > 0:
                    similarities.append(sim)

            special_metrics = {
                "avg_similarity": np.mean(similarities) if similarities else 0,
                "max_similarity": np.max(similarities) if similarities else 0,
                "min_similarity": np.min(similarities) if similarities else 0,
                "similarity_std": np.std(similarities) if similarities else 0
            }

        performance_summary[model_name] = {
            "total_cases": total_cases,
            "processing_time": processing_time,
            "avg_time_per_case": avg_time_per_case,
            "risk_distribution": risk_distribution,
            "error_count": error_count,
            "error_rate": error_count / total_cases if total_cases > 0 else 0,
            "special_metrics": special_metrics
        }

    return performance_summary

def create_comparison_charts(models_data, performance_summary):
    """비교 차트 생성"""

    # 1. 처리 시간 비교
    plt.figure(figsize=(15, 10))

    # 서브플롯 1: 평균 처리 시간
    plt.subplot(2, 3, 1)
    models = list(performance_summary.keys())
    avg_times = [performance_summary[model]["avg_time_per_case"] for model in models]

    plt.bar(models, avg_times)
    plt.title("평균 처리 시간 (초/건)")
    plt.xticks(rotation=45)
    plt.ylabel("시간 (초)")

    # 서브플롯 2: 위험도 분포
    plt.subplot(2, 3, 2)

    # 모든 모델의 위험도 통합
    all_risk_levels = set()
    for model in performance_summary.values():
        all_risk_levels.update(model["risk_distribution"].keys())

    risk_comparison = pd.DataFrame()
    for model_name in models:
        risk_dist = performance_summary[model_name]["risk_distribution"]
        for risk_level in all_risk_levels:
            risk_comparison.loc[model_name, risk_level] = risk_dist.get(risk_level, 0)

    risk_comparison.plot(kind="bar", stacked=True, ax=plt.gca())
    plt.title("위험도 분포 비교")
    plt.ylabel("건수")
    plt.legend(title="위험도")

    # 서브플롯 3: 오류율
    plt.subplot(2, 3, 3)
    error_rates = [performance_summary[model]["error_rate"] * 100 for model in models]

    plt.bar(models, error_rates)
    plt.title("오류율 (%)")
    plt.xticks(rotation=45)
    plt.ylabel("오류율 (%)")

    # 서브플롯 4: 특별 메트릭 (KoGPT)
    if "KoGPT" in performance_summary:
        plt.subplot(2, 3, 4)
        kogpt_metrics = performance_summary["KoGPT"]["special_metrics"]
        avg_length = kogpt_metrics.get("avg_explanation_length", 0)

        plt.bar(["KoGPT"], [avg_length])
        plt.title("KoGPT 평균 설명 길이")
        plt.ylabel("문자 수")

    # 서브플롯 5: 특별 메트릭 (KoSimCSE)
    if "KoSimCSE" in performance_summary:
        plt.subplot(2, 3, 5)
        kosimcse_metrics = performance_summary["KoSimCSE"]["special_metrics"]

        metrics_names = ["평균", "최대", "최소"]
        metrics_values = [
            kosimcse_metrics.get("avg_similarity", 0),
            kosimcse_metrics.get("max_similarity", 0),
            kosimcse_metrics.get("min_similarity", 0)
        ]

        plt.bar(metrics_names, metrics_values)
        plt.title("KoSimCSE 유사도 통계")
        plt.ylabel("유사도")
        plt.ylim(0, 1)

    # 서브플롯 6: 전체 성능 레이더 차트 준비
    plt.subplot(2, 3, 6)

    # 정규화된 성능 점수 계산 (0-1 스케일)
    normalized_scores = {}

    for model_name in models:
        perf = performance_summary[model_name]

        # 처리 속도 점수 (빠를수록 높은 점수)
        max_time = max([p["avg_time_per_case"] for p in performance_summary.values()])
        speed_score = 1 - (perf["avg_time_per_case"] / max_time) if max_time > 0 else 1

        # 정확도 점수 (오류율이 낮을수록 높은 점수)
        accuracy_score = 1 - perf["error_rate"]

        # 위험 탐지 능력 (HIGH + MEDIUM 비율)
        total_cases = perf["total_cases"]
        risk_cases = perf["risk_distribution"].get("HIGH", 0) + perf["risk_distribution"].get("MEDIUM", 0)
        detection_score = risk_cases / total_cases if total_cases > 0 else 0

        normalized_scores[model_name] = {
            "속도": speed_score,
            "정확도": accuracy_score,
            "탐지율": detection_score
        }

    # 성능 히트맵
    score_df = pd.DataFrame(normalized_scores).T
    sns.heatmap(score_df, annot=True, cmap="RdYlGn", vmin=0, vmax=1, ax=plt.gca())
    plt.title("모델 성능 히트맵")

    plt.tight_layout()
    plt.savefig("results/model_comparison_charts.png", dpi=300, bbox_inches="tight")
    plt.close()

    print("[INFO] 비교 차트 저장: results/model_comparison_charts.png")

def generate_final_report(models_data, performance_summary):
    """최종 보고서 생성"""

    report_file = "results/comparison_summary.txt"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("개인정보 탐지 모델 성능 비교 보고서\n")
        f.write("=" * 80 + "\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"비교 모델 수: {len(models_data)}개\n\n")

        # 요약 테이블
        f.write("성능 요약\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'모델명':<12} {'처리시간(초)':<12} {'오류율(%)':<10} {'HIGH위험':<10} {'특별기능':<20}\n")
        f.write("-" * 80 + "\n")

        for model_name, perf in performance_summary.items():
            avg_time = f"{perf['avg_time_per_case']:.2f}"
            error_rate = f"{perf['error_rate']*100:.1f}"
            high_risk = perf['risk_distribution'].get('HIGH', 0)

            special_feature = ""
            if model_name == "KoGPT":
                special_feature = "설명생성"
            elif model_name == "KoSimCSE":
                special_feature = "유사도탐지"
            elif "한국어" in model_name or "Ko" in model_name:
                special_feature = "한국어특화"
            else:
                special_feature = "기본"

            f.write(f"{model_name:<12} {avg_time:<12} {error_rate:<10} {high_risk:<10} {special_feature:<20}\n")

        f.write("\n[모델별 특징 및 추천 용도]\n")
        f.write("-" * 80 + "\n")

        for model_name, perf in performance_summary.items():
            f.write(f"\n[{model_name}]\n")

            if model_name == "KoGPT":
                f.write("강점: 문맥 기반 설명 생성, 동적 위험도 판단\n")
                f.write("추천: 사용자 피드백 시스템, 위험도 근거 제시\n")
                avg_len = perf['special_metrics'].get('avg_explanation_length', 0)
                f.write(f"평균 설명 길이: {avg_len:.0f}자\n")

            elif model_name == "KoSimCSE":
                f.write("강점: 유사 패턴 탐지, 오탐 보정, 확장 학습\n")
                f.write("추천: 새로운 위험 패턴 발견, 기존 모델 보완\n")
                avg_sim = perf['special_metrics'].get('avg_similarity', 0)
                f.write(f"평균 유사도: {avg_sim:.3f}\n")

            elif "KoBERT" in model_name:
                f.write("강점: 한국어 개체 인식, 기본 개인정보 탐지\n")
                f.write("추천: 1차 스크리닝, 개체명 추출\n")

            elif "KoELECTRA" in model_name:
                f.write("강점: 빠른 처리 속도, 효율적 분류\n")
                f.write("추천: 실시간 필터링, 대용량 처리\n")

            f.write(f"처리 속도: {perf['avg_time_per_case']:.2f}초/건\n")
            f.write(f"정확도: {(1-perf['error_rate'])*100:.1f}%\n")

        f.write(f"\n[통합 시스템 추천 구성]\n")
        f.write("-" * 80 + "\n")
        f.write("1단계: KoELECTRA (빠른 1차 필터링)\n")
        f.write("2단계: KoBERT (개체명 정확 인식)\n")
        f.write("3단계: KoSimCSE (유사 패턴 보완 탐지)\n")
        f.write("4단계: KoGPT (설명 생성 및 최종 판단)\n\n")
        f.write("이 4단계 파이프라인으로 속도와 정확도를 모두 확보 가능!\n")

def main():
    """메인 실행 함수"""
    print("[INFO] 모델 성능 비교 분석 시작...")

    # 결과 로드
    models_data = load_model_results()

    if not models_data:
        print("[ERROR] 로드할 결과 파일이 없습니다.")
        return

    # 성능 분석
    performance_summary = analyze_model_performance(models_data)

    # 차트 생성
    create_comparison_charts(models_data, performance_summary)

    # 최종 보고서 생성
    generate_final_report(models_data, performance_summary)

    print(f"[COMPLETE] 분석 완료! 총 {len(models_data)}개 모델 비교")
    print("결과 파일:")
    print("  - results/comparison_summary.txt")
    print("  - results/model_comparison_charts.png")

if __name__ == "__main__":
    main()
