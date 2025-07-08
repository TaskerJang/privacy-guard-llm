"""
결과 분석기 - 실험 결과 분석 및 보고서 생성
통계 분석, 성능 비교, 시각화 데이터 생성
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import logging

class ResultAnalyzer:
    """실험 결과 분석기"""

    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.logger = logging.getLogger(__name__)
        self.df = self._create_dataframe()

    def _create_dataframe(self) -> pd.DataFrame:
        """결과를 pandas DataFrame으로 변환"""
        try:
            df = pd.DataFrame(self.results)
            return df
        except Exception as e:
            self.logger.error(f"DataFrame 생성 실패: {e}")
            return pd.DataFrame()

    def calculate_overall_metrics(self) -> Dict[str, Any]:
        """전체 성능 지표 계산"""
        if self.df.empty:
            return {}

        total_cases = len(self.df)
        correct_cases = len(self.df[self.df['correct'] == True])
        error_cases = len(self.df[self.df['error'] == True])

        metrics = {
            'total_cases': total_cases,
            'correct_cases': correct_cases,
            'error_cases': error_cases,
            'accuracy': correct_cases / total_cases * 100 if total_cases > 0 else 0,
            'error_rate': error_cases / total_cases * 100 if total_cases > 0 else 0,
            'avg_processing_time': self.df['processing_time'].mean(),
            'total_cost': self.df['cost'].sum(),
            'avg_cost_per_case': self.df['cost'].mean(),
            'avg_risk_score': self.df['risk_score'].mean(),
            'total_tokens': self.df['token_count'].sum(),
            'avg_tokens_per_case': self.df['token_count'].mean()
        }

        return metrics

    def analyze_by_model(self) -> Dict[str, Dict[str, Any]]:
        """모델별 성능 분석"""
        model_stats = {}

        for model_name in self.df['model_name'].unique():
            model_df = self.df[self.df['model_name'] == model_name]

            total_cases = len(model_df)
            correct_cases = len(model_df[model_df['correct'] == True])
            error_cases = len(model_df[model_df['error'] == True])

            model_stats[model_name] = {
                'total_cases': total_cases,
                'correct_cases': correct_cases,
                'error_cases': error_cases,
                'accuracy': correct_cases / total_cases * 100 if total_cases > 0 else 0,
                'error_rate': error_cases / total_cases * 100 if total_cases > 0 else 0,
                'avg_processing_time': model_df['processing_time'].mean(),
                'total_cost': model_df['cost'].sum(),
                'avg_cost_per_case': model_df['cost'].mean(),
                'avg_risk_score': model_df['risk_score'].mean(),
                'total_tokens': model_df['token_count'].sum(),
                'cost_per_accuracy': model_df['cost'].sum() / (correct_cases / total_cases) if correct_cases > 0 else float('inf')
            }

        return model_stats

    def analyze_by_domain(self) -> Dict[str, Dict[str, Any]]:
        """도메인별 성능 분석"""
        domain_stats = {}

        for domain in self.df['domain'].unique():
            domain_df = self.df[self.df['domain'] == domain]

            total_cases = len(domain_df)
            correct_cases = len(domain_df[domain_df['correct'] == True])

            domain_stats[domain] = {
                'total_cases': total_cases,
                'correct_cases': correct_cases,
                'accuracy': correct_cases / total_cases * 100 if total_cases > 0 else 0,
                'avg_processing_time': domain_df['processing_time'].mean(),
                'avg_cost': domain_df['cost'].mean(),
                'avg_risk_score': domain_df['risk_score'].mean()
            }

        return domain_stats

    def analyze_by_risk_level(self) -> Dict[str, Dict[str, Any]]:
        """위험도별 성능 분석"""
        risk_stats = {}

        for risk_level in self.df['expected_risk'].unique():
            risk_df = self.df[self.df['expected_risk'] == risk_level]

            total_cases = len(risk_df)
            correct_cases = len(risk_df[risk_df['correct'] == True])

            # 예측 분포
            predicted_distribution = risk_df['predicted_risk'].value_counts().to_dict()

            risk_stats[risk_level] = {
                'total_cases': total_cases,
                'correct_cases': correct_cases,
                'accuracy': correct_cases / total_cases * 100 if total_cases > 0 else 0,
                'predicted_distribution': predicted_distribution,
                'avg_risk_score': risk_df['risk_score'].mean()
            }

        return risk_stats

    def generate_confusion_matrix(self) -> Dict[str, Dict[str, int]]:
        """혼동 행렬 생성"""
        confusion_matrix = defaultdict(lambda: defaultdict(int))

        for _, row in self.df.iterrows():
            expected = row['expected_risk']
            predicted = row['predicted_risk']
            confusion_matrix[expected][predicted] += 1

        return dict(confusion_matrix)

    def find_misclassified_cases(self) -> List[Dict[str, Any]]:
        """오분류 사례 분석"""
        misclassified = self.df[self.df['correct'] == False]

        cases = []
        for _, row in misclassified.iterrows():
            cases.append({
                'text': row['text'],
                'model_name': row['model_name'],
                'expected_risk': row['expected_risk'],
                'predicted_risk': row['predicted_risk'],
                'explanation': row['explanation'],
                'domain': row['domain']
            })

        return cases

    def get_best_performing_models(self) -> Dict[str, str]:
        """최고 성능 모델 찾기"""
        model_stats = self.analyze_by_model()

        if not model_stats:
            return {}

        best_models = {
            'highest_accuracy': max(model_stats.items(), key=lambda x: x[1]['accuracy'])[0],
            'fastest_processing': min(model_stats.items(), key=lambda x: x[1]['avg_processing_time'])[0],
            'most_cost_effective': min(model_stats.items(), key=lambda x: x[1]['cost_per_accuracy'])[0],
            'lowest_error_rate': min(model_stats.items(), key=lambda x: x[1]['error_rate'])[0]
        }

        return best_models

    def generate_insights(self) -> List[str]:
        """인사이트 생성"""
        insights = []

        overall_metrics = self.calculate_overall_metrics()
        model_stats = self.analyze_by_model()
        domain_stats = self.analyze_by_domain()
        risk_stats = self.analyze_by_risk_level()

        # 전체 성능 인사이트
        accuracy = overall_metrics.get('accuracy', 0)
        if accuracy > 80:
            insights.append("✅ 전체적으로 높은 정확도를 보여줍니다.")
        elif accuracy > 60:
            insights.append("⚠️ 전체적으로 보통 수준의 정확도를 보여줍니다.")
        else:
            insights.append("❌ 전체적으로 낮은 정확도를 보여줍니다. 개선이 필요합니다.")

        # 모델 성능 인사이트
        if model_stats:
            best_model = max(model_stats.items(), key=lambda x: x[1]['accuracy'])
            worst_model = min(model_stats.items(), key=lambda x: x[1]['accuracy'])

            insights.append(f"🏆 최고 성능 모델: {best_model[0]} (정확도: {best_model[1]['accuracy']:.1f}%)")
            insights.append(f"📉 개선 필요 모델: {worst_model[0]} (정확도: {worst_model[1]['accuracy']:.1f}%)")

        # 도메인별 인사이트
        if domain_stats:
            domain_accuracies = [(domain, stats['accuracy']) for domain, stats in domain_stats.items()]
            domain_accuracies.sort(key=lambda x: x[1], reverse=True)

            insights.append(f"📋 도메인별 성능: {domain_accuracies[0][0]} 도메인이 가장 높음 ({domain_accuracies[0][1]:.1f}%)")
            if len(domain_accuracies) > 1:
                insights.append(f"🔍 개선 필요 도메인: {domain_accuracies[-1][0]} ({domain_accuracies[-1][1]:.1f}%)")

        # 위험도별 인사이트
        if risk_stats:
            risk_accuracies = [(risk, stats['accuracy']) for risk, stats in risk_stats.items()]
            risk_accuracies.sort(key=lambda x: x[1], reverse=True)

            insights.append(f"⚠️ 위험도별 성능: {risk_accuracies[0][0]} 위험도가 가장 정확함 ({risk_accuracies[0][1]:.1f}%)")

        # 비용 효율성 인사이트
        avg_cost = overall_metrics.get('avg_cost_per_case', 0)
        if avg_cost < 0.001:
            insights.append("💰 매우 저렴한 비용으로 분석이 가능합니다.")
        elif avg_cost < 0.01:
            insights.append("💵 적정한 비용으로 분석이 가능합니다.")
        else:
            insights.append("💸 비용이 높으니 효율적인 모델 선택이 필요합니다.")

        return insights

    def generate_report(self) -> str:
        """전체 분석 리포트 텍스트 생성"""
        lines = []

        lines.append("📊 Privacy Guard LLM 실험 분석 리포트")
        lines.append("=" * 60)

        # 전체 지표
        lines.append("\n[1] 전체 성능 요약")
        metrics = self.calculate_overall_metrics()
        if not metrics:
            return "⚠️ 결과 데이터가 없습니다."

        lines.append(f"- 전체 케이스 수: {metrics['total_cases']}")
        lines.append(f"- 정확히 분류된 케이스: {metrics['correct_cases']}개")
        lines.append(f"- 정확도: {metrics['accuracy']:.1f}%")
        lines.append(f"- 평균 처리 시간: {metrics['avg_processing_time']:.2f}초")
        lines.append(f"- 총 비용: ${metrics['total_cost']:.4f}")
        lines.append(f"- 평균 위험도 점수: {metrics['avg_risk_score']:.3f}")
        lines.append(f"- 평균 비용: ${metrics['avg_cost_per_case']:.4f}")

        # 모델별 성능
        lines.append("\n[2] 모델별 성능 요약")
        model_stats = self.analyze_by_model()
        for model, stat in model_stats.items():
            lines.append(f"- {model}: 정확도 {stat['accuracy']:.1f}%, 평균 시간 {stat['avg_processing_time']:.2f}s, 총 비용 ${stat['total_cost']:.4f}")

        # 도메인별 성능
        lines.append("\n[3] 도메인별 성능 요약")
        domain_stats = self.analyze_by_domain()
        for domain, stat in domain_stats.items():
            lines.append(f"- {domain}: 정확도 {stat['accuracy']:.1f}%, 평균 비용 ${stat['avg_cost']:.4f}")

        # 위험도별 성능
        lines.append("\n[4] 위험도별 성능 요약")
        risk_stats = self.analyze_by_risk_level()
        for level, stat in risk_stats.items():
            lines.append(f"- {level}: 정확도 {stat['accuracy']:.1f}%, 분포 {stat['predicted_distribution']}")

        # 인사이트
        lines.append("\n[5] 주요 인사이트")
        insights = self.generate_insights()
        for insight in insights:
            lines.append(f"- {insight}")

        return "\n".join(lines)
