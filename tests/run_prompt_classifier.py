"""
Privacy Guard LLM - Prompt Classifier 메인 실행 파일
2025년 7월 최신 모델 기반 개인정보 위험도 분석

사용법:
    python run_prompt_classifier.py --mode all      # 모든 모델 테스트
    python run_prompt_classifier.py --mode precision # 정밀 비교 그룹만
    python run_prompt_classifier.py --mode speed    # 속도 테스트 그룹만
    python run_prompt_classifier.py --mode sample   # 샘플 케이스만
"""

import os
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List

# 프로젝트 모듈 import
from llm_configs import LLMConfigManager
from prompt_templates import PromptTemplates
from test_cases import TestCases
from llm_api_client import LLMAPIClient
from result_analyzer import ResultAnalyzer

def setup_logging():
    """로깅 설정"""
    import logging

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{log_dir}/prompt_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)

def run_experiment(mode: str = "all", max_cost: float = 5.0, save_results: bool = True):
    """실험 실행"""
    logger = setup_logging()

    print("🚀 Privacy Guard LLM - Prompt Classifier 실험 시작")
    print("=" * 80)
    print(f"🔧 실행 모드: {mode}")
    print(f"💰 최대 비용: ${max_cost:.2f}")
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 설정 초기화
    config_manager = LLMConfigManager()
    templates = PromptTemplates()
    api_client = LLMAPIClient(max_cost=max_cost)

    # 사용 가능한 모델 확인
    available_models = config_manager.get_available_models()
    if not available_models:
        print("❌ 사용 가능한 모델이 없습니다.")
        print("API 키를 .env 파일에 설정하고 필요한 라이브러리를 설치하세요.")
        return

    # 실험 모드에 따른 모델 선택
    if mode == "precision":
        test_models = config_manager.get_precision_group()
        print(f"🎯 정밀 비교 그룹: {test_models}")
    elif mode == "speed":
        test_models = config_manager.get_speed_group()
        print(f"⚡ 속도 테스트 그룹: {test_models}")
    elif mode == "cost":
        test_models = config_manager.get_cost_efficient_group()
        print(f"💰 비용 효율 그룹: {test_models}")
    elif mode == "sample":
        test_models = available_models[:3]  # 처음 3개 모델만
        print(f"📋 샘플 테스트: {test_models}")
    else:  # mode == "all"
        test_models = available_models
        print(f"🤖 전체 모델: {test_models}")

    # 테스트 케이스 선택
    if mode == "sample":
        test_cases = TestCases.get_sample_cases(5)
    else:
        test_cases = TestCases.get_all_cases()

    print(f"\n📊 실험 규모:")
    print(f"   🤖 테스트 모델: {len(test_models)}개")
    print(f"   📋 테스트 케이스: {len(test_cases)}개")
    print(f"   🧪 총 분석 수: {len(test_models) * len(test_cases)}개")

    # 비용 추정
    estimated_cost = len(test_models) * len(test_cases) * 0.01  # 대략적인 추정
    print(f"   💰 예상 비용: ${estimated_cost:.2f}")

    if estimated_cost > max_cost:
        print(f"⚠️  예상 비용이 한도를 초과합니다. 계속하시겠습니까? (y/n)")
        if input().lower() != 'y':
            print("실험을 취소합니다.")
            return

    print(f"\n🚀 실험 시작...")
    print("-" * 80)

    # 실험 실행
    all_results = []
    start_time = time.time()

    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 테스트 케이스 {i}/{len(test_cases)}: {case['description']}")
        print(f"   📄 텍스트: {case['text']}")
        print(f"   🏷️  도메인: {case['domain']}")
        print(f"   🎯 예상 위험도: {case['expected_risk']}")

        case_results = []

        for model_name in test_models:
            try:
                print(f"   🤖 {model_name} 분석 중...")

                # 모델 설정 가져오기
                config = config_manager.get_config(model_name)

                # 프롬프트 생성
                prompt = templates.get_all_prompts()[case['domain']].format(text=case['text'])

                # API 호출
                result = api_client.analyze_text(
                    text=case['text'],
                    config=config,
                    prompt=prompt,
                    expected_risk=case['expected_risk']
                )

                case_results.append(result)

                # 결과 출력
                print(f"      위험도: {result['predicted_risk']} (점수: {result['risk_score']:.3f})")
                print(f"      처리시간: {result['processing_time']:.2f}초")
                print(f"      비용: ${result['cost']:.4f}")
                print(f"      정확도: {'✅' if result['correct'] else '❌'}")

                # API 호출 제한
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"모델 {model_name} 분석 실패: {e}")
                print(f"      ❌ 분석 실패: {e}")
                continue

        all_results.extend(case_results)

        # 진행률 출력
        progress = (i / len(test_cases)) * 100
        print(f"   📊 진행률: {progress:.1f}%")

        # 중간 결과 저장 (10개 케이스마다)
        if save_results and i % 10 == 0:
            save_intermediate_results(all_results, mode)

    # 실험 완료
    total_time = time.time() - start_time
    print(f"\n🎉 실험 완료!")
    print(f"⏱️  총 소요 시간: {total_time:.2f}초")
    print(f"💰 총 비용: ${api_client.total_cost:.4f}")

    # 결과 분석
    analyzer = ResultAnalyzer(all_results)
    analysis_report = analyzer.generate_report()

    # 결과 출력
    print("\n📊 실험 결과 분석")
    print("=" * 80)
    print(analysis_report)

    # 결과 저장
    if save_results:
        save_final_results(all_results, analysis_report, mode)

    return all_results

def save_intermediate_results(results: List[Dict], mode: str):
    """중간 결과 저장"""
    os.makedirs("../results", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/intermediate_{mode}_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"   💾 중간 결과 저장: {filename}")

def save_final_results(results: List[Dict], analysis_report: str, mode: str):
    """최종 결과 저장"""
    os.makedirs("../results", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON 결과 저장
    results_filename = f"results/final_{mode}_{timestamp}.json"
    with open(results_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 분석 보고서 저장
    report_filename = f"results/report_{mode}_{timestamp}.md"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"# Privacy Guard LLM - 실험 결과 보고서\n\n")
        f.write(f"- 실행 모드: {mode}\n")
        f.write(f"- 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- 총 분석 수: {len(results)}개\n\n")
        f.write(analysis_report)

    print(f"💾 최종 결과 저장:")
    print(f"   📄 결과 데이터: {results_filename}")
    print(f"   📋 분석 보고서: {report_filename}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Privacy Guard LLM - Prompt Classifier')
    parser.add_argument('--mode', choices=['all', 'precision', 'speed', 'cost', 'sample'],
                        default='sample', help='실험 모드')
    parser.add_argument('--max-cost', type=float, default=5.0, help='최대 비용 한도')
    parser.add_argument('--no-save', action='store_true', help='결과 저장 안함')

    args = parser.parse_args()

    # 실험 실행
    try:
        results = run_experiment(
            mode=args.mode,
            max_cost=args.max_cost,
            save_results=not args.no_save
        )

        print(f"\n✅ 실험 성공적으로 완료!")
        print(f"📊 총 {len(results)}개 결과 생성")

    except KeyboardInterrupt:
        print(f"\n⏹️  사용자에 의해 실험이 중단되었습니다.")

    except Exception as e:
        print(f"\n❌ 실험 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()