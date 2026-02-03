# debate_enhancer.py
# Phase B4: 토론면접 고도화 - AI 토론 상대, 논리력 분석
# FlyReady Lab Enhancement

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re


class DebateStrategy(Enum):
    """토론 전략 유형"""
    LOGICAL = "logical"           # 논리적, 구조적 접근
    EMOTIONAL = "emotional"       # 감성적, 공감 기반
    DATA_DRIVEN = "data_driven"   # 데이터, 통계 중심
    EXAMPLE_BASED = "example_based"  # 사례 중심
    BALANCED = "balanced"         # 균형 잡힌 접근


class LogicalFallacy(Enum):
    """논리적 오류 유형"""
    STRAW_MAN = "straw_man"                    # 허수아비 공격
    AD_HOMINEM = "ad_hominem"                  # 인신공격
    HASTY_GENERALIZATION = "hasty_generalization"  # 성급한 일반화
    FALSE_DICHOTOMY = "false_dichotomy"        # 잘못된 이분법
    APPEAL_TO_AUTHORITY = "appeal_to_authority"  # 권위에의 호소
    APPEAL_TO_EMOTION = "appeal_to_emotion"    # 감정에의 호소
    CIRCULAR_REASONING = "circular_reasoning"  # 순환논증
    SLIPPERY_SLOPE = "slippery_slope"          # 미끄러운 경사면
    RED_HERRING = "red_herring"                # 논점 일탈
    BANDWAGON = "bandwagon"                    # 다수에의 호소


@dataclass
class ArgumentStructure:
    """논증 구조 분석 결과"""
    has_claim: bool = False           # 주장이 있는가
    has_reason: bool = False          # 근거가 있는가
    has_example: bool = False         # 예시가 있는가
    has_conclusion: bool = False      # 결론이 있는가
    structure_type: str = "incomplete"  # PREP, 삼단논법 등
    strength_score: int = 0           # 논증 강도 (0-100)
    components: Dict[str, str] = field(default_factory=dict)


@dataclass
class FallacyDetection:
    """논리적 오류 감지 결과"""
    fallacy_type: LogicalFallacy
    severity: str  # "low", "medium", "high"
    description: str
    suggestion: str
    matched_text: str


@dataclass
class RebuttalAnalysis:
    """반박 효과성 분석"""
    addresses_opponent: bool  # 상대 주장을 다루는가
    provides_counter: bool    # 반론을 제시하는가
    maintains_respect: bool   # 존중을 유지하는가
    effectiveness_score: int  # 반박 효과성 (0-100)
    feedback: str


# =====================
# 논증 구조 분석기
# =====================

class ArgumentAnalyzer:
    """논증 구조 분석"""

    # 주장 표현 패턴
    CLAIM_PATTERNS = [
        r'생각합니다',
        r'주장합니다',
        r'믿습니다',
        r'~해야\s*(합니다|한다고)',
        r'~라고\s*봅니다',
        r'~입니다',
        r'반대합니다',
        r'찬성합니다',
        r'동의합니다',
        r'동의하지\s*않습니다',
        r'중요합니다',
        r'필요합니다',
    ]

    # 근거 표현 패턴
    REASON_PATTERNS = [
        r'왜냐하면',
        r'그\s*이유는',
        r'~때문입니다',
        r'~때문에',
        r'근거로',
        r'이유로',
        r'첫째|둘째|셋째',
        r'먼저|다음으로|마지막으로',
        r'~에서\s*볼\s*수\s*있듯이',
        r'연구에\s*따르면',
        r'통계에\s*의하면',
        r'실제로',
    ]

    # 예시 표현 패턴
    EXAMPLE_PATTERNS = [
        r'예를\s*들어',
        r'예시로',
        r'사례로',
        r'경험상',
        r'실제\s*사례',
        r'~의\s*경우',
        r'예컨대',
        r'가령',
        r'구체적으로',
        r'일례로',
    ]

    # 결론 표현 패턴
    CONCLUSION_PATTERNS = [
        r'따라서',
        r'그러므로',
        r'결론적으로',
        r'정리하자면',
        r'요약하면',
        r'결국',
        r'종합하면',
        r'이상으로',
        r'마무리하자면',
    ]

    # PREP 전환어
    PREP_TRANSITIONS = {
        'point': [r'저는', r'제\s*생각에는', r'~라고\s*생각합니다'],
        'reason': [r'왜냐하면', r'그\s*이유는', r'~때문입니다'],
        'example': [r'예를\s*들어', r'실제로', r'예시로'],
        'point_final': [r'그래서', r'따라서', r'그러므로'],
    }

    def analyze_structure(self, text: str) -> ArgumentStructure:
        """논증 구조 분석"""
        result = ArgumentStructure()

        # 주장 확인
        for pattern in self.CLAIM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result.has_claim = True
                result.components['claim'] = self._extract_component(text, pattern)
                break

        # 근거 확인
        for pattern in self.REASON_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result.has_reason = True
                result.components['reason'] = self._extract_component(text, pattern)
                break

        # 예시 확인
        for pattern in self.EXAMPLE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result.has_example = True
                result.components['example'] = self._extract_component(text, pattern)
                break

        # 결론 확인
        for pattern in self.CONCLUSION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result.has_conclusion = True
                result.components['conclusion'] = self._extract_component(text, pattern)
                break

        # 구조 유형 판단
        result.structure_type = self._determine_structure_type(result)

        # 강도 점수 계산
        result.strength_score = self._calculate_strength(result, text)

        return result

    def _extract_component(self, text: str, pattern: str, max_len: int = 100) -> str:
        """패턴 주변 텍스트 추출"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + max_len)
            return text[start:end].strip()
        return ""

    def _determine_structure_type(self, result: ArgumentStructure) -> str:
        """논증 구조 유형 판단"""
        components_count = sum([
            result.has_claim,
            result.has_reason,
            result.has_example,
            result.has_conclusion
        ])

        if result.has_claim and result.has_reason and result.has_example and result.has_conclusion:
            return "PREP (완전)"
        elif result.has_claim and result.has_reason and result.has_example:
            return "PRE (결론 부족)"
        elif result.has_claim and result.has_reason:
            return "주장-근거"
        elif result.has_claim:
            return "단순 주장"
        elif components_count == 0:
            return "구조 없음"
        else:
            return "불완전"

    def _calculate_strength(self, result: ArgumentStructure, text: str) -> int:
        """논증 강도 점수 계산"""
        score = 0

        # 기본 구조 점수
        if result.has_claim:
            score += 25
        if result.has_reason:
            score += 25
        if result.has_example:
            score += 20
        if result.has_conclusion:
            score += 15

        # 전환어 사용 보너스
        transitions = ['첫째', '둘째', '다음으로', '마지막으로', '또한', '더불어']
        transition_count = sum(1 for t in transitions if t in text)
        score += min(15, transition_count * 5)

        return min(100, score)


# =====================
# 논리적 오류 감지기
# =====================

class FallacyDetector:
    """논리적 오류 감지"""

    FALLACY_PATTERNS = {
        LogicalFallacy.STRAW_MAN: {
            'patterns': [
                r'그러니까.*말씀은.*아니',
                r'~라고\s*하셨는데\s*그건',
                r'그\s*말은.*아닌가요',
            ],
            'keywords': ['왜곡', '그런 말', '그게 아니라'],
            'description': '상대방의 주장을 왜곡하여 반박하는 오류입니다.',
            'suggestion': '상대방의 실제 주장을 정확히 인용하고 그에 대해 반박하세요.',
        },
        LogicalFallacy.AD_HOMINEM: {
            'patterns': [
                r'그런\s*사람이',
                r'~출신이라서',
                r'경험이\s*없으니까',
            ],
            'keywords': ['인격', '사람이', '자격', '뭘 알아'],
            'description': '상대방의 주장이 아닌 인격이나 배경을 공격하는 오류입니다.',
            'suggestion': '상대방의 주장 자체에 집중하여 논리적으로 반박하세요.',
        },
        LogicalFallacy.HASTY_GENERALIZATION: {
            'patterns': [
                r'모든\s*사람이',
                r'항상\s*그렇',
                r'다\s*그래',
                r'언제나',
                r'절대로',
            ],
            'keywords': ['모두', '전부', '항상', '절대', '다들'],
            'description': '충분하지 않은 사례로 일반화하는 오류입니다.',
            'suggestion': '"대부분", "많은 경우" 등으로 표현을 완화하고, 구체적인 근거를 제시하세요.',
        },
        LogicalFallacy.FALSE_DICHOTOMY: {
            'patterns': [
                r'둘\s*중\s*하나',
                r'아니면.*뿐',
                r'~이거나.*밖에',
                r'오직\s*두\s*가지',
            ],
            'keywords': ['둘 중', '아니면', '양자택일'],
            'description': '복잡한 문제를 두 가지 선택지로만 제한하는 오류입니다.',
            'suggestion': '다양한 대안이 있을 수 있음을 인정하고, 중간 입장도 고려하세요.',
        },
        LogicalFallacy.APPEAL_TO_EMOTION: {
            'patterns': [
                r'생각해\s*보세요',
                r'안타깝게도',
                r'불쌍하지\s*않',
            ],
            'keywords': ['마음', '감정', '안타깝', '불쌍', '슬프'],
            'description': '논리적 근거 대신 감정에 호소하는 오류입니다.',
            'suggestion': '감정적 호소와 함께 논리적 근거도 제시하세요.',
        },
        LogicalFallacy.BANDWAGON: {
            'patterns': [
                r'다들\s*그렇게',
                r'많은\s*사람들이',
                r'대세가',
                r'트렌드',
            ],
            'keywords': ['다들', '대세', '트렌드', '세계적으로'],
            'description': '다수가 그렇다고 해서 옳다고 주장하는 오류입니다.',
            'suggestion': '다수의 의견이 반드시 옳은 것은 아니므로, 본질적 근거를 제시하세요.',
        },
        LogicalFallacy.SLIPPERY_SLOPE: {
            'patterns': [
                r'그러면\s*결국',
                r'나중에는',
                r'~하면.*될\s*것',
                r'~로\s*이어질',
            ],
            'keywords': ['결국', '나중에', '이어질', '악화될'],
            'description': '한 단계에서 극단적 결과로 비약하는 오류입니다.',
            'suggestion': '각 단계 사이의 인과관계를 명확히 설명하세요.',
        },
    }

    def detect_fallacies(self, text: str) -> List[FallacyDetection]:
        """텍스트에서 논리적 오류 감지"""
        detected = []

        for fallacy_type, config in self.FALLACY_PATTERNS.items():
            # 패턴 매칭
            for pattern in config['patterns']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    detected.append(FallacyDetection(
                        fallacy_type=fallacy_type,
                        severity=self._determine_severity(text, config['keywords']),
                        description=config['description'],
                        suggestion=config['suggestion'],
                        matched_text=match.group()
                    ))
                    break

            # 키워드 매칭 (패턴에서 감지되지 않은 경우)
            if not any(d.fallacy_type == fallacy_type for d in detected):
                keyword_count = sum(1 for kw in config['keywords'] if kw in text)
                if keyword_count >= 2:
                    detected.append(FallacyDetection(
                        fallacy_type=fallacy_type,
                        severity='low',
                        description=config['description'],
                        suggestion=config['suggestion'],
                        matched_text=f"키워드 {keyword_count}개 감지"
                    ))

        return detected

    def _determine_severity(self, text: str, keywords: List[str]) -> str:
        """오류 심각도 판단"""
        keyword_count = sum(1 for kw in keywords if kw in text)
        if keyword_count >= 3:
            return 'high'
        elif keyword_count >= 2:
            return 'medium'
        return 'low'


# =====================
# 반박 효과성 분석기
# =====================

class RebuttalAnalyzer:
    """반박 효과성 분석"""

    # 상대방 언급 패턴
    ADDRESSING_PATTERNS = [
        r'~님의?\s*말씀',
        r'~님께서',
        r'앞서\s*말씀하신',
        r'방금\s*말씀',
        r'그\s*의견에',
        r'~라고\s*하셨는데',
        r'말씀하신\s*것처럼',
    ]

    # 반론 제시 패턴
    COUNTER_PATTERNS = [
        r'하지만',
        r'그러나',
        r'반면에',
        r'다른\s*관점에서',
        r'오히려',
        r'그런데',
        r'동의하기\s*어려',
        r'다르게\s*생각',
    ]

    # 존중 표현 패턴
    RESPECT_PATTERNS = [
        r'좋은\s*말씀',
        r'일리가\s*있',
        r'충분히\s*이해',
        r'그\s*점은\s*공감',
        r'맞는\s*말씀',
        r'존중합니다',
        r'이해합니다',
    ]

    # 비존중 표현 패턴 (감점 요소)
    DISRESPECT_PATTERNS = [
        r'틀렸',
        r'말도\s*안\s*되',
        r'이해가\s*안',
        r'황당',
        r'어이가\s*없',
    ]

    def analyze_rebuttal(
        self,
        user_statement: str,
        opponent_statement: str,
        context: List[str]
    ) -> RebuttalAnalysis:
        """반박 효과성 분석"""

        # 상대방 주장 다루는지 확인
        addresses_opponent = any(
            re.search(pattern, user_statement, re.IGNORECASE)
            for pattern in self.ADDRESSING_PATTERNS
        )

        # 반론 제시 확인
        provides_counter = any(
            re.search(pattern, user_statement, re.IGNORECASE)
            for pattern in self.COUNTER_PATTERNS
        )

        # 존중 유지 확인
        respect_count = sum(
            1 for pattern in self.RESPECT_PATTERNS
            if re.search(pattern, user_statement, re.IGNORECASE)
        )
        disrespect_count = sum(
            1 for pattern in self.DISRESPECT_PATTERNS
            if re.search(pattern, user_statement, re.IGNORECASE)
        )
        maintains_respect = respect_count > 0 or disrespect_count == 0

        # 효과성 점수 계산
        score = 0
        if addresses_opponent:
            score += 30
        if provides_counter:
            score += 35
        if maintains_respect:
            score += 20
        if respect_count > 0:
            score += 15
        if disrespect_count > 0:
            score -= 20

        # 상대방 발언의 핵심 단어 포함 여부
        opponent_keywords = self._extract_keywords(opponent_statement)
        keyword_overlap = sum(1 for kw in opponent_keywords if kw in user_statement)
        if keyword_overlap >= 2:
            score += 10

        score = max(0, min(100, score))

        # 피드백 생성
        feedback = self._generate_feedback(
            addresses_opponent,
            provides_counter,
            maintains_respect,
            disrespect_count
        )

        return RebuttalAnalysis(
            addresses_opponent=addresses_opponent,
            provides_counter=provides_counter,
            maintains_respect=maintains_respect,
            effectiveness_score=score,
            feedback=feedback
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """핵심 키워드 추출 (간단한 구현)"""
        # 불용어 제거 후 단어 추출
        stopwords = {'저는', '그래서', '하지만', '그러나', '입니다', '합니다', '있습니다'}
        words = re.findall(r'[가-힣]+', text)
        keywords = [w for w in words if len(w) >= 2 and w not in stopwords]
        return keywords[:10]

    def _generate_feedback(
        self,
        addresses: bool,
        counter: bool,
        respect: bool,
        disrespect: int
    ) -> str:
        """피드백 메시지 생성"""
        feedback_parts = []

        if addresses:
            feedback_parts.append("상대방의 발언을 잘 인용하고 있습니다.")
        else:
            feedback_parts.append("상대방의 구체적인 발언을 언급하면 더 효과적입니다.")

        if counter:
            feedback_parts.append("명확한 반론을 제시했습니다.")
        else:
            feedback_parts.append("'하지만', '반면에' 등을 사용해 반론을 명시하면 좋습니다.")

        if disrespect > 0:
            feedback_parts.append("존중하는 표현으로 바꾸면 설득력이 높아집니다.")
        elif respect:
            feedback_parts.append("상대를 존중하는 태도가 좋습니다.")

        return " ".join(feedback_parts)


# =====================
# AI 토론 전략 분석기
# =====================

class DebateStrategyAnalyzer:
    """토론 전략 분석 및 추천"""

    STRATEGY_INDICATORS = {
        DebateStrategy.LOGICAL: {
            'patterns': [r'따라서', r'그러므로', r'왜냐하면', r'논리적으로'],
            'weight': 1.0,
        },
        DebateStrategy.EMOTIONAL: {
            'patterns': [r'마음', r'감정', r'느낌', r'공감', r'안타깝'],
            'weight': 0.8,
        },
        DebateStrategy.DATA_DRIVEN: {
            'patterns': [r'통계', r'데이터', r'연구', r'조사', r'\d+%', r'수치'],
            'weight': 1.2,
        },
        DebateStrategy.EXAMPLE_BASED: {
            'patterns': [r'예를 들어', r'사례', r'경험', r'실제로'],
            'weight': 0.9,
        },
        DebateStrategy.BALANCED: {
            'patterns': [r'한편으로는', r'양측', r'균형', r'모두'],
            'weight': 0.7,
        },
    }

    def analyze_strategy(self, statements: List[str]) -> Dict:
        """사용자의 토론 전략 분석"""
        all_text = " ".join(statements)

        strategy_scores = {}
        for strategy, config in self.STRATEGY_INDICATORS.items():
            count = sum(
                len(re.findall(pattern, all_text, re.IGNORECASE))
                for pattern in config['patterns']
            )
            strategy_scores[strategy] = count * config['weight']

        # 주 전략 식별
        if strategy_scores:
            dominant_strategy = max(strategy_scores, key=strategy_scores.get)
        else:
            dominant_strategy = DebateStrategy.BALANCED

        return {
            'dominant_strategy': dominant_strategy,
            'strategy_scores': strategy_scores,
            'recommendation': self._get_strategy_recommendation(dominant_strategy, strategy_scores)
        }

    def _get_strategy_recommendation(
        self,
        dominant: DebateStrategy,
        scores: Dict[DebateStrategy, float]
    ) -> str:
        """전략 개선 추천"""
        recommendations = {
            DebateStrategy.LOGICAL: "논리적 접근이 좋습니다. 구체적인 예시를 추가하면 더 설득력 있습니다.",
            DebateStrategy.EMOTIONAL: "감성적 접근을 잘 활용하고 있습니다. 객관적 근거를 추가하면 균형 잡힙니다.",
            DebateStrategy.DATA_DRIVEN: "데이터 기반 논증이 강합니다. 청중과의 공감대 형성도 고려해보세요.",
            DebateStrategy.EXAMPLE_BASED: "사례 제시가 좋습니다. 사례에서 일반 원칙으로 연결하면 더 강력합니다.",
            DebateStrategy.BALANCED: "균형 잡힌 시각입니다. 핵심 주장을 좀 더 명확히 하면 좋겠습니다.",
        }

        return recommendations.get(dominant, "다양한 전략을 활용해보세요.")

    def suggest_counter_strategy(self, opponent_strategy: DebateStrategy) -> Dict:
        """상대방 전략에 대한 대응 전략 추천"""
        counter_strategies = {
            DebateStrategy.LOGICAL: {
                'counter': DebateStrategy.DATA_DRIVEN,
                'advice': "상대방의 논리에 대해 구체적인 데이터와 반례를 제시하세요.",
            },
            DebateStrategy.EMOTIONAL: {
                'counter': DebateStrategy.LOGICAL,
                'advice': "감정적 호소에 대해 객관적 사실과 논리로 대응하세요.",
            },
            DebateStrategy.DATA_DRIVEN: {
                'counter': DebateStrategy.EXAMPLE_BASED,
                'advice': "통계의 예외 사례나 실제 현장 사례로 반박하세요.",
            },
            DebateStrategy.EXAMPLE_BASED: {
                'counter': DebateStrategy.LOGICAL,
                'advice': "개별 사례가 일반화될 수 없는 이유를 논리적으로 설명하세요.",
            },
            DebateStrategy.BALANCED: {
                'counter': DebateStrategy.LOGICAL,
                'advice': "중립적 입장의 약점을 지적하고 명확한 입장의 필요성을 강조하세요.",
            },
        }

        return counter_strategies.get(opponent_strategy, {
            'counter': DebateStrategy.BALANCED,
            'advice': "다양한 관점에서 균형 있게 반론을 제시하세요.",
        })


# =====================
# 토론 기여도 분석기
# =====================

class DebateContributionAnalyzer:
    """토론 기여도 분석"""

    def analyze_contribution(
        self,
        user_statements: List[str],
        all_statements: List[Dict],
        topic: str
    ) -> Dict:
        """사용자의 토론 기여도 분석"""

        total_user = len(user_statements)
        total_all = len(all_statements)

        # 발언 비율
        participation_rate = (total_user / total_all * 100) if total_all > 0 else 0

        # 평균 발언 길이
        avg_length = sum(len(s) for s in user_statements) / total_user if total_user > 0 else 0

        # 토론 주제 연관성
        topic_relevance = self._calculate_topic_relevance(user_statements, topic)

        # 새로운 논점 제시 여부
        new_points = self._count_new_points(user_statements, all_statements)

        # 종합 기여도 점수
        contribution_score = self._calculate_contribution_score(
            participation_rate, avg_length, topic_relevance, new_points
        )

        return {
            'participation_rate': round(participation_rate, 1),
            'avg_statement_length': round(avg_length, 0),
            'topic_relevance': topic_relevance,
            'new_points_count': new_points,
            'contribution_score': contribution_score,
            'feedback': self._generate_contribution_feedback(
                participation_rate, avg_length, topic_relevance, new_points
            )
        }

    def _calculate_topic_relevance(self, statements: List[str], topic: str) -> int:
        """주제 연관성 점수"""
        topic_keywords = re.findall(r'[가-힣]+', topic)
        topic_keywords = [kw for kw in topic_keywords if len(kw) >= 2]

        all_text = " ".join(statements)
        matches = sum(1 for kw in topic_keywords if kw in all_text)

        if not topic_keywords:
            return 70

        relevance = min(100, int((matches / len(topic_keywords)) * 100) + 30)
        return relevance

    def _count_new_points(self, user_statements: List[str], all_statements: List[Dict]) -> int:
        """새로운 논점 제시 횟수"""
        new_points = 0
        previous_keywords = set()

        for stmt in all_statements:
            if stmt.get('is_user'):
                current_keywords = set(re.findall(r'[가-힣]{2,}', stmt.get('content', '')))
                new_keywords = current_keywords - previous_keywords
                if len(new_keywords) >= 3:
                    new_points += 1

            previous_keywords.update(re.findall(r'[가-힣]{2,}', stmt.get('content', '')))

        return new_points

    def _calculate_contribution_score(
        self,
        participation: float,
        avg_length: float,
        relevance: int,
        new_points: int
    ) -> int:
        """종합 기여도 점수"""
        score = 0

        # 참여율 (적정 범위: 20-35%)
        if 20 <= participation <= 35:
            score += 30
        elif 15 <= participation <= 40:
            score += 20
        else:
            score += 10

        # 발언 길이 (적정: 50-200자)
        if 50 <= avg_length <= 200:
            score += 25
        elif 30 <= avg_length <= 250:
            score += 15
        else:
            score += 5

        # 주제 연관성
        score += int(relevance * 0.3)

        # 새로운 논점
        score += min(15, new_points * 5)

        return min(100, score)

    def _generate_contribution_feedback(
        self,
        participation: float,
        avg_length: float,
        relevance: int,
        new_points: int
    ) -> str:
        """기여도 피드백 생성"""
        feedback = []

        if participation < 20:
            feedback.append("발언 횟수를 늘려 적극적으로 참여하세요.")
        elif participation > 40:
            feedback.append("다른 참가자에게도 발언 기회를 주세요.")
        else:
            feedback.append("적절한 발언 비율을 유지하고 있습니다.")

        if avg_length < 50:
            feedback.append("발언을 좀 더 구체적으로 전개하세요.")
        elif avg_length > 200:
            feedback.append("핵심을 간결하게 전달하면 더 효과적입니다.")

        if relevance < 60:
            feedback.append("주제와 더 연관된 내용으로 발언하세요.")

        if new_points == 0:
            feedback.append("새로운 관점이나 논점을 제시해보세요.")

        return " ".join(feedback)


# =====================
# 통합 토론 분석기
# =====================

class EnhancedDebateAnalyzer:
    """통합 토론 분석기"""

    def __init__(self):
        self.argument_analyzer = ArgumentAnalyzer()
        self.fallacy_detector = FallacyDetector()
        self.rebuttal_analyzer = RebuttalAnalyzer()
        self.strategy_analyzer = DebateStrategyAnalyzer()
        self.contribution_analyzer = DebateContributionAnalyzer()

    def analyze_debate_complete(
        self,
        user_statements: List[str],
        all_history: List[Dict],
        topic: str,
        user_position: str
    ) -> Dict:
        """종합 토론 분석"""

        # 1. 논증 구조 분석 (각 발언별)
        argument_analyses = []
        for stmt in user_statements:
            analysis = self.argument_analyzer.analyze_structure(stmt)
            argument_analyses.append({
                'statement': stmt[:50] + "..." if len(stmt) > 50 else stmt,
                'structure_type': analysis.structure_type,
                'strength': analysis.strength_score,
                'has_claim': analysis.has_claim,
                'has_reason': analysis.has_reason,
                'has_example': analysis.has_example,
            })

        # 평균 논증 강도
        avg_argument_strength = (
            sum(a['strength'] for a in argument_analyses) / len(argument_analyses)
            if argument_analyses else 0
        )

        # 2. 논리적 오류 감지
        all_user_text = " ".join(user_statements)
        fallacies = self.fallacy_detector.detect_fallacies(all_user_text)
        fallacy_summary = [
            {
                'type': f.fallacy_type.value,
                'severity': f.severity,
                'description': f.description,
                'suggestion': f.suggestion,
            }
            for f in fallacies
        ]

        # 3. 반박 효과성 분석
        rebuttal_analyses = []
        for i, stmt in enumerate(user_statements):
            # 이전 상대방 발언 찾기
            opponent_stmt = self._find_previous_opponent_statement(all_history, i, user_position)
            if opponent_stmt:
                rebuttal = self.rebuttal_analyzer.analyze_rebuttal(
                    stmt, opponent_stmt, [s.get('content', '') for s in all_history]
                )
                rebuttal_analyses.append({
                    'statement_index': i + 1,
                    'effectiveness': rebuttal.effectiveness_score,
                    'addresses_opponent': rebuttal.addresses_opponent,
                    'provides_counter': rebuttal.provides_counter,
                    'maintains_respect': rebuttal.maintains_respect,
                    'feedback': rebuttal.feedback,
                })

        avg_rebuttal_score = (
            sum(r['effectiveness'] for r in rebuttal_analyses) / len(rebuttal_analyses)
            if rebuttal_analyses else 50
        )

        # 4. 토론 전략 분석
        strategy_analysis = self.strategy_analyzer.analyze_strategy(user_statements)

        # 5. 기여도 분석
        contribution_analysis = self.contribution_analyzer.analyze_contribution(
            user_statements, all_history, topic
        )

        # 6. 종합 점수 계산
        logic_score = self._calculate_logic_score(
            avg_argument_strength, len(fallacies), avg_rebuttal_score
        )
        persuasion_score = self._calculate_persuasion_score(
            argument_analyses, rebuttal_analyses, strategy_analysis
        )

        # 7. 등급 결정
        total_score = int((logic_score + persuasion_score + contribution_analysis['contribution_score']) / 3)
        grade = self._determine_grade(total_score)

        return {
            'total_score': total_score,
            'grade': grade,
            'logic_score': logic_score,
            'persuasion_score': persuasion_score,
            'contribution_score': contribution_analysis['contribution_score'],
            'argument_analyses': argument_analyses,
            'avg_argument_strength': round(avg_argument_strength, 0),
            'fallacies': fallacy_summary,
            'fallacy_count': len(fallacies),
            'rebuttal_analyses': rebuttal_analyses,
            'avg_rebuttal_score': round(avg_rebuttal_score, 0),
            'strategy': {
                'dominant': strategy_analysis['dominant_strategy'].value,
                'recommendation': strategy_analysis['recommendation'],
            },
            'contribution': contribution_analysis,
            'overall_feedback': self._generate_overall_feedback(
                logic_score, persuasion_score, contribution_analysis, fallacies
            ),
            'improvement_priorities': self._get_improvement_priorities(
                avg_argument_strength, fallacies, avg_rebuttal_score, contribution_analysis
            ),
        }

    def _find_previous_opponent_statement(
        self,
        history: List[Dict],
        user_statement_index: int,
        user_position: str
    ) -> Optional[str]:
        """사용자 발언 직전 상대방 발언 찾기"""
        user_count = 0
        last_opponent = None

        for entry in history:
            if entry.get('is_user'):
                if user_count == user_statement_index:
                    return last_opponent
                user_count += 1
            else:
                if entry.get('position') != user_position:
                    last_opponent = entry.get('content', '')

        return last_opponent

    def _calculate_logic_score(
        self,
        argument_strength: float,
        fallacy_count: int,
        rebuttal_score: float
    ) -> int:
        """논리력 점수 계산"""
        score = argument_strength * 0.4 + rebuttal_score * 0.4 + 20
        score -= fallacy_count * 10  # 오류당 10점 감점
        return max(0, min(100, int(score)))

    def _calculate_persuasion_score(
        self,
        arguments: List[Dict],
        rebuttals: List[Dict],
        strategy: Dict
    ) -> int:
        """설득력 점수 계산"""
        score = 50

        # 완전한 PREP 구조 보너스
        prep_count = sum(1 for a in arguments if 'PREP' in a.get('structure_type', ''))
        score += prep_count * 10

        # 반박 효과성
        if rebuttals:
            avg_rebuttal = sum(r['effectiveness'] for r in rebuttals) / len(rebuttals)
            score += (avg_rebuttal - 50) * 0.3

        # 전략 일관성 보너스
        if strategy.get('dominant_strategy') in [DebateStrategy.LOGICAL, DebateStrategy.DATA_DRIVEN]:
            score += 10

        return max(0, min(100, int(score)))

    def _determine_grade(self, score: int) -> str:
        """등급 결정"""
        if score >= 90:
            return 'S'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

    def _generate_overall_feedback(
        self,
        logic: int,
        persuasion: int,
        contribution: Dict,
        fallacies: List
    ) -> str:
        """종합 피드백 생성"""
        feedback = []

        if logic >= 80:
            feedback.append("논리적인 토론 전개가 인상적입니다.")
        elif logic >= 60:
            feedback.append("논리 구조를 더 명확히 하면 좋겠습니다.")
        else:
            feedback.append("주장-근거-예시의 구조를 갖추어 발언해보세요.")

        if persuasion >= 80:
            feedback.append("설득력 있는 주장을 잘 펼쳤습니다.")
        elif persuasion < 60:
            feedback.append("상대방의 발언에 더 적극적으로 반응해보세요.")

        if fallacies:
            feedback.append(f"논리적 오류가 {len(fallacies)}건 감지되었으니 주의하세요.")

        feedback.append(contribution.get('feedback', ''))

        return " ".join(feedback)

    def _get_improvement_priorities(
        self,
        argument_strength: float,
        fallacies: List,
        rebuttal_score: float,
        contribution: Dict
    ) -> List[str]:
        """개선 우선순위 도출"""
        priorities = []

        if argument_strength < 60:
            priorities.append("논증 구조 강화: 주장에 반드시 근거와 예시를 포함하세요")

        if fallacies:
            priorities.append(f"논리적 오류 수정: {fallacies[0]['description']}")

        if rebuttal_score < 60:
            priorities.append("반박 효과성 향상: 상대 발언을 인용하며 반론을 제시하세요")

        if contribution.get('contribution_score', 0) < 60:
            priorities.append("토론 기여도 향상: 새로운 관점을 제시하고 적극 참여하세요")

        return priorities[:3] if priorities else ["전반적으로 좋은 토론이었습니다!"]


# =====================
# 편의 함수
# =====================

def analyze_debate_answer(
    statement: str,
    previous_opponent: str = "",
    topic: str = "",
    user_position: str = "neutral"
) -> Dict:
    """단일 발언 분석 (간편 함수)"""
    argument_analyzer = ArgumentAnalyzer()
    fallacy_detector = FallacyDetector()
    rebuttal_analyzer = RebuttalAnalyzer()

    # 논증 구조
    structure = argument_analyzer.analyze_structure(statement)

    # 논리적 오류
    fallacies = fallacy_detector.detect_fallacies(statement)

    # 반박 효과성 (이전 상대 발언이 있는 경우)
    rebuttal = None
    if previous_opponent:
        rebuttal = rebuttal_analyzer.analyze_rebuttal(statement, previous_opponent, [])

    return {
        'structure': {
            'type': structure.structure_type,
            'strength': structure.strength_score,
            'has_claim': structure.has_claim,
            'has_reason': structure.has_reason,
            'has_example': structure.has_example,
        },
        'fallacies': [
            {
                'type': f.fallacy_type.value,
                'severity': f.severity,
                'suggestion': f.suggestion,
            }
            for f in fallacies
        ],
        'rebuttal': {
            'score': rebuttal.effectiveness_score,
            'feedback': rebuttal.feedback,
        } if rebuttal else None,
    }


def get_debate_analysis_complete(
    user_statements: List[str],
    all_history: List[Dict],
    topic: str,
    user_position: str
) -> Dict:
    """종합 토론 분석 (간편 함수)"""
    analyzer = EnhancedDebateAnalyzer()
    return analyzer.analyze_debate_complete(
        user_statements, all_history, topic, user_position
    )


def get_argument_feedback(statement: str) -> Dict:
    """논증 피드백 (간편 함수)"""
    analyzer = ArgumentAnalyzer()
    structure = analyzer.analyze_structure(statement)

    feedback = []
    if not structure.has_claim:
        feedback.append("명확한 주장을 제시하세요.")
    if not structure.has_reason:
        feedback.append("'왜냐하면', '그 이유는' 등으로 근거를 설명하세요.")
    if not structure.has_example:
        feedback.append("'예를 들어', '실제로' 등으로 예시를 추가하세요.")
    if not structure.has_conclusion:
        feedback.append("'따라서', '그러므로'로 결론을 정리하세요.")

    if not feedback:
        feedback.append("완전한 논증 구조입니다!")

    return {
        'structure_type': structure.structure_type,
        'strength': structure.strength_score,
        'feedback': feedback,
    }
