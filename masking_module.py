import os
import torch
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings("ignore")

# 학습된 모델 로드용
from transformers import AutoTokenizer, AutoModelForTokenClassification
from peft import PeftModel

# Copula 모델용 (2단계)
from copulas.multivariate import GaussianMultivariate

# ================== 데이터 구조 정의 ==================
@dataclass
class NERResult:
    """1단계 NER 결과"""
    token: str
    entity: str
    start_pos: int = 0
    end_pos: int = 0

@dataclass
class RiskWeight:
    """2단계 위험도 가중치"""
    token: str
    entity: str
    category: str  # '직접', '간접', '기타'
    risk_weight: int  # 0-100
    copula_feature: str = None

@dataclass
class MaskingResult:
    """최종 마스킹 결과"""
    original_text: str
    masked_text: str
    masking_log: List[Dict]
    total_entities: int
    masked_entities: int

# ================== 1단계: 학습된 NER 모델 ==================
class TrainedNERModel:
    """학습된 KoELECTRA NER 모델 로더"""

    def __init__(self, model_path: str, base_model: str = "monologg/koelectra-base-v3-discriminator"):
        self.model_path = model_path
        self.base_model = base_model
        self.tokenizer = None
        self.model = None
        self.id2label = None
        self._load_model()

    def _load_model(self):
        """학습된 모델 로드"""
        try:
            # LoRA 어댑터인지 병합 모델인지 확인
            is_lora = os.path.exists(os.path.join(self.model_path, "adapter_config.json"))

            if is_lora:
                print(f"🔄 LoRA 어댑터 로드 중: {self.model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                base = AutoModelForTokenClassification.from_pretrained(self.base_model)
                self.model = PeftModel.from_pretrained(base, self.model_path)
            else:
                print(f"🔄 병합 모델 로드 중: {self.model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForTokenClassification.from_pretrained(self.model_path)

            self.model.eval()
            self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
            print(f"✅ NER 모델 로드 완료! 라벨 수: {len(self.id2label)}")

        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            print("💡 더미 모델로 대체합니다...")
            self._create_dummy_model()

    def _create_dummy_model(self):
        """학습된 모델이 없을 때 더미 모델 생성"""
        self.id2label = {
            0: 'O', 1: 'B-PER', 2: 'I-PER', 3: 'B-ORG', 4: 'I-ORG',
            5: 'B-LOC', 6: 'I-LOC', 7: 'B-DATE', 8: 'I-DATE',
            9: 'B-DISEASE', 10: 'I-DISEASE', 11: 'B-CONTACT', 12: 'I-CONTACT'
        }
        print("⚠️  더미 NER 모델 사용 중 (실제 모델 경로를 설정하세요)")

    def predict(self, sentence: str) -> List[NERResult]:
        """문장에서 개체명 추출"""
        if self.model is None:
            return self._dummy_predict(sentence)

        tokens = sentence.split()
        enc = self.tokenizer(
            tokens, is_split_into_words=True,
            return_tensors="pt", padding="max_length",
            truncation=True, max_length=128
        )

        with torch.no_grad():
            logits = self.model(**enc).logits

        preds = logits.argmax(-1)[0].tolist()
        word_ids = enc.word_ids()

        results = []
        last_word_id = None

        for i, word_id in enumerate(word_ids):
            if word_id is None or word_id == last_word_id:
                continue

            entity_label = self.id2label[preds[i]]
            results.append(NERResult(
                token=tokens[word_id],
                entity=entity_label,
                start_pos=0,  # 실제 구현시 계산
                end_pos=len(tokens[word_id])
            ))
            last_word_id = word_id

        return results

    def _dummy_predict(self, sentence: str) -> List[NERResult]:
        """더미 예측 (모델 없을 때)"""
        # 간단한 규칙 기반 더미 NER
        tokens = sentence.split()
        results = []

        for token in tokens:
            entity = 'O'
            # 간단한 휴리스틱
            if any(name in token for name in ['김', '박', '이', '최', '정', '한']):
                entity = 'B-PER'
            elif any(org in token for org in ['병원', '의료원', '센터']):
                entity = 'B-ORG'
            elif any(date in token for date in ['년', '월', '일']):
                entity = 'B-DATE'
            elif '010-' in token or '02-' in token:
                entity = 'B-CONTACT'

            results.append(NERResult(token=token, entity=entity))

        return results

# ================== 2단계: Copula 위험도 분석 ==================
class CopulaRiskAnalyzer:
    """Copula 기반 위험도 분석기"""

    def __init__(self):
        self._setup_copula_model()
        self.token_to_feature = {
            '서울대병원': {'기관_서울대병원': 1, '기관_삼성서울': 0, '기관_연세의료원': 0},
            '삼성서울병원': {'기관_서울대병원': 0, '기관_삼성서울': 1, '기관_연세의료원': 0},
            '간암': {'질병_간암': 1, '질병_백혈병': 0, '질병_고혈압': 0},
            '백혈병': {'질병_간암': 0, '질병_백혈병': 1, '질병_고혈압': 0},
            '2023년': {'날짜_2023년': 1, '날짜_2022년': 0, '날짜_2021년': 0},
            '2024년': {'날짜_2023년': 0, '날짜_2022년': 1, '날짜_2021년': 0},
        }

    def _setup_copula_model(self):
        """Copula 모델 학습"""
        np.random.seed(42)
        df_sample = pd.DataFrame({
            '기관': np.random.choice(['서울대병원', '삼성서울', '연세의료원'], 1000),
            '질병': np.random.choice(['간암', '백혈병', '고혈압'], 1000),
            '날짜': np.random.choice(['2023년', '2022년', '2021년'], 1000)
        })

        df_encoded = pd.get_dummies(df_sample).astype(float)
        self.copula_model = GaussianMultivariate()
        self.copula_model.fit(df_encoded)
        self.samples = self.copula_model.sample(10000).round()

    def calculate_risk_weights(self, ner_results: List[NERResult]) -> List[RiskWeight]:
        """NER 결과를 위험도로 변환"""
        risk_weights = []

        for ner_result in ner_results:
            category = self._categorize_entity(ner_result.entity)
            risk_weight = self._calculate_single_risk(ner_result.token, ner_result.entity, category)

            copula_feature = None
            if ner_result.token in self.token_to_feature:
                copula_feature = ", ".join(self.token_to_feature[ner_result.token].keys())

            risk_weights.append(RiskWeight(
                token=ner_result.token,
                entity=ner_result.entity,
                category=category,
                risk_weight=risk_weight,
                copula_feature=copula_feature
            ))

        return risk_weights

    def _categorize_entity(self, entity: str) -> str:
        """엔티티를 직접/간접/기타로 분류"""
        direct_entities = ['B-PER', 'I-PER', 'B-CONTACT', 'I-CONTACT']
        indirect_entities = ['B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'B-DATE', 'I-DATE', 'B-DISEASE', 'I-DISEASE']

        if entity in direct_entities:
            return '직접'
        elif entity in indirect_entities:
            return '간접'
        else:
            return '기타'

    def _calculate_single_risk(self, token: str, entity: str, category: str) -> int:
        """단일 토큰의 위험도 계산"""
        if category == '직접':
            return 100
        elif category == '간접':
            feature_info = self.token_to_feature.get(token)
            if feature_info:
                risk_score = self._calculate_copula_risk(feature_info)
                return round(risk_score * 100)
            return 30  # 기본 간접 위험도
        else:
            return 0

    def _calculate_copula_risk(self, feature_dict: Dict) -> float:
        """Copula 기반 위험도 계산"""
        match = (self.samples[list(feature_dict.keys())] == pd.Series(feature_dict)).all(axis=1)
        probability = match.sum() / len(self.samples)
        return 1 - probability  # 희귀할수록 위험

# ================== 3단계: 문맥적 위험 분석 ==================
class ContextualRiskAnalyzer:
    """문맥을 고려한 위험도 조정"""

    def __init__(self):
        self.high_risk_combinations = {
            ('PER', 'ORG', 'DATE'): 1.5,
            ('PER', 'DISEASE', 'ORG'): 1.8,
            ('PER', 'CONTACT'): 2.0,
            ('ORG', 'DATE', 'DISEASE'): 1.3,
        }

        self.medical_risk_keywords = {
            '진단': 1.2, '수술': 1.2, '입원': 1.2, '치료': 1.2,
            '암': 1.3, '종양': 1.3, '질환': 1.3,
            '응급': 1.5, '중환자': 1.5
        }

    def analyze_contextual_risk(self, text: str, risk_weights: List[RiskWeight]) -> List[RiskWeight]:
        """문맥을 고려한 위험도 재조정"""
        entity_types = [self._normalize_entity_type(rw.entity) for rw in risk_weights if rw.entity != 'O']

        combination_multiplier = self._get_combination_multiplier(entity_types)
        keyword_multiplier = self._get_keyword_multiplier(text)

        adjusted_weights = []
        for risk_weight in risk_weights:
            adjusted_weight = risk_weight.risk_weight

            if adjusted_weight > 0:
                adjusted_weight = min(100, int(adjusted_weight * combination_multiplier * keyword_multiplier))

            adjusted_weights.append(RiskWeight(
                token=risk_weight.token,
                entity=risk_weight.entity,
                category=risk_weight.category,
                risk_weight=adjusted_weight,
                copula_feature=risk_weight.copula_feature
            ))

        return adjusted_weights

    def _normalize_entity_type(self, entity: str) -> str:
        if entity.startswith(('B-', 'I-')):
            return entity[2:]
        return entity

    def _get_combination_multiplier(self, entity_types: List[str]) -> float:
        entity_set = set(entity_types)
        max_multiplier = 1.0

        for pattern, multiplier in self.high_risk_combinations.items():
            if set(pattern).issubset(entity_set):
                max_multiplier = max(max_multiplier, multiplier)

        return max_multiplier

    def _get_keyword_multiplier(self, text: str) -> float:
        max_multiplier = 1.0
        for keyword, multiplier in self.medical_risk_keywords.items():
            if keyword in text:
                max_multiplier = max(max_multiplier, multiplier)
        return max_multiplier

# ================== 4단계: 마스킹 실행 ==================
class MaskingExecutor:
    """마스킹 실행기"""

    def __init__(self, threshold: int = 50):
        self.threshold = threshold
        self.mask_patterns = {
            'PER': '[PERSON]',
            'ORG': '[HOSPITAL]',
            'LOC': '[LOCATION]',
            'DATE': '[DATE]',
            'DISEASE': '[DISEASE]',
            'CONTACT': '[CONTACT]',
            'CVL': '[TITLE]',
            'NUM': '[NUMBER]',
            'default': '[MASKED]'
        }

    def execute_masking(self, text: str, risk_weights: List[RiskWeight]) -> MaskingResult:
        """임계값 기반 마스킹 실행"""
        masked_text = text
        masking_log = []
        masked_count = 0
        total_entities = len([rw for rw in risk_weights if rw.entity != 'O'])

        # 위험도 높은 순으로 정렬
        sorted_weights = sorted(risk_weights, key=lambda x: x.risk_weight, reverse=True)

        for risk_weight in sorted_weights:
            if risk_weight.risk_weight >= self.threshold and risk_weight.entity != 'O':
                entity_type = self._normalize_entity_type(risk_weight.entity)
                mask_pattern = self.mask_patterns.get(entity_type, self.mask_patterns['default'])

                if risk_weight.token in masked_text:
                    masked_text = masked_text.replace(risk_weight.token, mask_pattern, 1)
                    masked_count += 1

                    masking_log.append({
                        'token': risk_weight.token,
                        'entity': risk_weight.entity,
                        'risk_weight': risk_weight.risk_weight,
                        'masked_as': mask_pattern,
                        'reason': f'위험도 {risk_weight.risk_weight} >= 임계값 {self.threshold}'
                    })

        return MaskingResult(
            original_text=text,
            masked_text=masked_text,
            masking_log=masking_log,
            total_entities=total_entities,
            masked_entities=masked_count
        )

    def _normalize_entity_type(self, entity: str) -> str:
        if entity.startswith(('B-', 'I-')):
            return entity[2:]
        return entity

# ================== 전체 파이프라인 통합 ==================
class CompleteMedicalDeidentificationPipeline:
    """완전한 의료 텍스트 비식별화 파이프라인"""

    def __init__(self,
                 model_path: str = None,
                 threshold: int = 50,
                 use_contextual_analysis: bool = True):

        print("🚀 의료 텍스트 비식별화 파이프라인 초기화 중...")

        # 1단계: 학습된 NER 모델 로드
        self.ner_model = TrainedNERModel(model_path) if model_path else TrainedNERModel("dummy")

        # 2단계: Copula 위험도 분석기
        self.copula_analyzer = CopulaRiskAnalyzer()

        # 3단계: 문맥적 위험 분석기
        self.contextual_analyzer = ContextualRiskAnalyzer() if use_contextual_analysis else None

        # 4단계: 마스킹 실행기
        self.masking_executor = MaskingExecutor(threshold)

        print("✅ 파이프라인 초기화 완료!")

    def process(self, text: str, verbose: bool = True) -> MaskingResult:
        """전체 파이프라인 실행"""
        if verbose:
            print(f"\n📝 처리할 텍스트: {text}")

        # 1단계: NER (학습된 모델 사용!)
        ner_results = self.ner_model.predict(text)
        if verbose:
            print(f"🔍 1단계 NER 결과: {[(r.token, r.entity) for r in ner_results]}")

        # 2단계: Copula 위험도 계산
        risk_weights = self.copula_analyzer.calculate_risk_weights(ner_results)
        if verbose:
            print(f"📊 2단계 위험도: {[(r.token, r.risk_weight) for r in risk_weights if r.risk_weight > 0]}")

        # 3단계: 문맥적 위험도 조정
        if self.contextual_analyzer:
            risk_weights = self.contextual_analyzer.analyze_contextual_risk(text, risk_weights)
            if verbose:
                print(f"🔄 3단계 조정된 위험도: {[(r.token, r.risk_weight) for r in risk_weights if r.risk_weight > 0]}")

        # 4단계: 마스킹 실행
        result = self.masking_executor.execute_masking(text, risk_weights)
        if verbose:
            print(f"🎭 4단계 마스킹 결과: {result.masked_text}")

        return result

    def print_detailed_analysis(self, result: MaskingResult):
        """상세 분석 결과 출력"""
        print("\n" + "="*80)
        print("🏥 의료 텍스트 비식별화 분석 결과")
        print("="*80)
        print(f"📝 원문: {result.original_text}")
        print(f"🎭 마스킹: {result.masked_text}")
        print(f"📊 통계: {result.masked_entities}/{result.total_entities} 개체 마스킹")

        if result.masking_log:
            print("\n📋 마스킹 상세 로그:")
            for i, log in enumerate(result.masking_log, 1):
                print(f"  {i}. '{log['token']}' → {log['masked_as']} (위험도: {log['risk_weight']})")
        else:
            print("\n✅ 마스킹이 필요한 고위험 정보가 없습니다.")

# ================== 테스트 실행 ==================
def main():
    """메인 테스트 함수"""
    print("🚀 완전한 의료 텍스트 비식별화 파이프라인 테스트")

    # 파이프라인 초기화 (실제 모델 경로 설정 필요)
    model_path = "ner-koelectra-lora-merged"  # 실제 학습된 모델 경로로 변경
    pipeline = CompleteMedicalDeidentificationPipeline(
        model_path=model_path,  # 여기에 실제 학습된 모델 경로 입력!
        threshold=50,
        use_contextual_analysis=True
    )

    # 테스트 케이스
    test_cases = [
        "김철수씨가 2023년 10월에 서울대병원에서 간암 진단을 받았습니다.",
        "박영희(010-1234-5678)는 삼성서울병원에서 수술을 받았다.",
        "환자는 내일 검사를 받을 예정입니다.",
        "이순신 교수는 연세의료원에서 백혈병 연구를 하고 있다."
    ]

    # 각 테스트 케이스 실행
    for i, text in enumerate(test_cases, 1):
        print(f"\n{'='*20} 테스트 {i} {'='*20}")
        result = pipeline.process(text, verbose=True)
        pipeline.print_detailed_analysis(result)

    print(f"\n{'='*80}")
    print("✅ 모든 테스트 완료!")
    print("💡 실제 학습된 모델을 사용하려면 model_path를 수정하세요.")
    print("💡 예: 'ner-koelectra-lora-merged' 또는 './results/(epoch-10, lr-8e-05, batch-8)ner-koelectra-lora-merged'")

if __name__ == "__main__":
    main()