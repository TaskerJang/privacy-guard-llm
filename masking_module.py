import os
import torch
import numpy as np
import pandas as pd
from typing import List, Dict
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
        try:
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
        self.id2label = {
            0: 'O', 1: 'B-PER', 2: 'I-PER', 3: 'B-ORG', 4: 'I-ORG',
            5: 'B-LOC', 6: 'I-LOC', 7: 'B-DATE', 8: 'I-DATE',
            9: 'B-DISEASE', 10: 'I-DISEASE', 11: 'B-CONTACT', 12: 'I-CONTACT'
        }
        print("⚠️  더미 NER 모델 사용 중 (실제 모델 경로를 설정하세요)")

    def predict(self, sentence: str) -> List[NERResult]:
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

            # raw 라벨 변환 (PER_B -> B-PER 등)
            raw_label = self.id2label[preds[i]]
            if "_" in raw_label:
                tag, pos = raw_label.split("_")
                entity_label = f"{pos}-{tag}"
            else:
                entity_label = raw_label

            results.append(NERResult(
                token=tokens[word_id],
                entity=entity_label,
                start_pos=0,
                end_pos=len(tokens[word_id])
            ))
            last_word_id = word_id

        return results

    def _dummy_predict(self, sentence: str) -> List[NERResult]:
        tokens = sentence.split()
        results = []
        for token in tokens:
            entity = 'O'
            if any(name in token for name in ['김','박','이','최','정','한']):
                entity = 'B-PER'
            elif any(org in token for org in ['병원','의료원','센터']):
                entity = 'B-ORG'
            elif any(date in token for date in ['년','월','일']):
                entity = 'B-DATE'
            elif '010-' in token or '02-' in token:
                entity = 'B-CONTACT'
            results.append(NERResult(token=token, entity=entity))
        return results

# ================== 2단계: Copula 위험도 분석 ==================
class CopulaRiskAnalyzer:
    def __init__(self):
        self._setup_copula_model()
        self.token_to_feature = {
            '서울대병원': {'기관_서울대병원':1,'기관_삼성서울':0,'기관_연세의료원':0},
            '삼성서울병원': {'기관_서울대병원':0,'기관_삼성서울':1,'기관_연세의료원':0},
            '간암': {'질병_간암':1,'질병_백혈병':0,'질병_고혈압':0},
            '백혈병': {'질병_간암':0,'질병_백혈병':1,'질병_고혈압':0},
            '2023년': {'날짜_2023년':1,'날짜_2022년':0,'날짜_2021년':0},
            '2024년': {'날짜_2023년':0,'날짜_2022년':1,'날짜_2021년':0},
        }

    def _setup_copula_model(self):
        np.random.seed(42)
        df_sample = pd.DataFrame({
            '기관': np.random.choice(['서울대병원','삼성서울','연세의료원'],1000),
            '질병': np.random.choice(['간암','백혈병','고혈압'],1000),
            '날짜': np.random.choice(['2023년','2022년','2021년'],1000)
        })
        df_encoded = pd.get_dummies(df_sample).astype(float)
        self.copula_model = GaussianMultivariate()
        self.copula_model.fit(df_encoded)
        # 샘플 수를 1000으로 줄여 속도 개선
        self.samples = self.copula_model.sample(1000).round()

    def calculate_risk_weights(self, ner_results: List[NERResult]) -> List[RiskWeight]:
        risk_weights = []
        for ner in ner_results:
            category = self._categorize_entity(ner.entity)
            rw = self._calculate_single_risk(ner.token, ner.entity, category)
            feature = None
            if ner.token in self.token_to_feature:
                feature = ", ".join(self.token_to_feature[ner.token].keys())
            risk_weights.append(RiskWeight(
                token=ner.token, entity=ner.entity,
                category=category, risk_weight=rw,
                copula_feature=feature
            ))
        return risk_weights

    def _categorize_entity(self, entity: str) -> str:
        direct = ['B-PER','I-PER','B-CONTACT','I-CONTACT']
        indirect = ['B-ORG','I-ORG','B-LOC','I-LOC','B-DATE','I-DATE','B-DISEASE','I-DISEASE']
        if entity in direct: return '직접'
        if entity in indirect: return '간접'
        return '기타'

    def _calculate_single_risk(self, token: str, entity: str, category: str) -> int:
        if category=='직접': return 100
        if category=='간접':
            feat = self.token_to_feature.get(token)
            if feat:
                return round(self._calculate_copula_risk(feat)*100)
            return 30
        return 0

    def _calculate_copula_risk(self, feat: Dict) -> float:
        match = (self.samples[list(feat.keys())]==pd.Series(feat)).all(axis=1)
        prob = match.sum()/len(self.samples)
        return 1-prob

# ================== 3단계: 문맥적 위험 분석 ==================
class ContextualRiskAnalyzer:
    def __init__(self):
        self.high_risk_combinations = {('PER','ORG','DATE'):1.5,('PER','DISEASE','ORG'):1.8,('PER','CONTACT'):2.0,('ORG','DATE','DISEASE'):1.3}
        self.medical_risk_keywords = {'진단':1.2,'수술':1.2,'입원':1.2,'치료':1.2,'암':1.3,'종양':1.3,'질환':1.3,'응급':1.5,'중환자':1.5}

    def analyze_contextual_risk(self, text: str, risk_weights: List[RiskWeight]) -> List[RiskWeight]:
        types = [rw.entity[2:] for rw in risk_weights if rw.entity!='O']
        comb_mult = self._get_combination_multiplier(types)
        kw_mult = self._get_keyword_multiplier(text)
        adjusted = []
        for rw in risk_weights:
            w = rw.risk_weight
            if w>0:
                w = min(100, int(w*comb_mult*kw_mult))
            adjusted.append(RiskWeight(rw.token,rw.entity,rw.category,w,rw.copula_feature))
        return adjusted

    def _get_combination_multiplier(self, types: List[str]) -> float:
        m=1.0
        for pat, mult in self.high_risk_combinations.items():
            if set(pat).issubset(set(types)):
                m = max(m, mult)
        return m

    def _get_keyword_multiplier(self, text: str) -> float:
        m=1.0
        for kw, mult in self.medical_risk_keywords.items():
            if kw in text: m = max(m, mult)
        return m

# ================== 4단계: 마스킹 실행 ==================
class MaskingExecutor:
    def __init__(self, threshold: int = 50):
        self.threshold = threshold
        self.mask_patterns = {'PER':'[PERSON]','ORG':'[HOSPITAL]','LOC':'[LOCATION]','DATE':'[DATE]',
                              'DISEASE':'[DISEASE]','CONTACT':'[CONTACT]','CVL':'[TITLE]','NUM':'[NUMBER]','default':'[MASKED]'}

    def execute_masking(self, text: str, risk_weights: List[RiskWeight]) -> MaskingResult:
        masked_text = text
        log = []
        masked_count = 0
        total = len([rw for rw in risk_weights if rw.entity!='O'])
        for rw in sorted(risk_weights, key=lambda x: x.risk_weight, reverse=True):
            if rw.risk_weight>=self.threshold and rw.entity!='O':
                et = rw.entity[2:]
                pat = self.mask_patterns.get(et, self.mask_patterns['default'])
                if rw.token in masked_text:
                    masked_text = masked_text.replace(rw.token, pat, 1)
                    masked_count+=1
                    log.append({'token':rw.token,'entity':rw.entity,'risk_weight':rw.risk_weight,'masked_as':pat,'reason':f'위험도 {rw.risk_weight} >= 임계값 {self.threshold}'})
        return MaskingResult(text, masked_text, log, total, masked_count)

# ================== 전체 파이프라인 통합 ==================
class CompleteMedicalDeidentificationPipeline:
    def __init__(self, model_path: str=None, threshold: int=50, use_contextual_analysis: bool=True):
        print("🚀 의료 텍스트 비식별화 파이프라인 초기화 중...")
        self.ner_model = TrainedNERModel(model_path) if model_path else TrainedNERModel("dummy")
        self.copula_analyzer = CopulaRiskAnalyzer()
        self.contextual_analyzer = ContextualRiskAnalyzer() if use_contextual_analysis else None
        self.masking_executor = MaskingExecutor(threshold)
        print("✅ 파이프라인 초기화 완료!")

    def process(self, text: str, verbose: bool=True) -> MaskingResult:
        if verbose: print(f"\n📝 처리할 텍스트: {text}")
        ner_results = self.ner_model.predict(text)
        if verbose: print(f"🔍 1단계 NER 결과: {[(r.token, r.entity) for r in ner_results]}")
        risk_weights = self.copula_analyzer.calculate_risk_weights(ner_results)
        if verbose: print(f"📊 2단계 위험도: {[(r.token,r.risk_weight) for r in risk_weights if r.risk_weight>0]}")
        if self.contextual_analyzer:
            risk_weights = self.contextual_analyzer.analyze_contextual_risk(text, risk_weights)
            if verbose: print(f"🔄 3단계 조정된 위험도: {[(r.token,r.risk_weight) for r in risk_weights if r.risk_weight>0]}")
        result = self.masking_executor.execute_masking(text, risk_weights)
        if verbose: print(f"🎭 4단계 마스킹 결과: {result.masked_text}")
        return result

    def print_detailed_analysis(self, result: MaskingResult):
        print("\n"+"="*80)
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
    print("🚀 완전한 의료 텍스트 비식별화 파이프라인 테스트")
    # 변경된 model_path 지정
    model_path = "ner-koelectra-lora-merged"
    pipeline = CompleteMedicalDeidentificationPipeline(
        model_path=model_path,
        threshold=50,
        use_contextual_analysis=True
    )

    test_cases = [
        "김철수씨가 2023년 10월에 서울대병원에서 간암 진단을 받았습니다.",
        "박영희(010-1234-5678)는 삼성서울병원에서 수술을 받았다.",
        "환자는 내일 검사를 받을 예정입니다.",
        "이순신 교수는 연세의료원에서 백혈병 연구를 하고 있다."
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n{'='*20} 테스트 {i} {'='*20}")
        result = pipeline.process(text, verbose=True)
        pipeline.print_detailed_analysis(result)

    print("\n"+"="*80)
    print("✅ 모든 테스트 완료!")

if __name__ == "__main__":
    main()
