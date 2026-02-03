# english_interview_enhancer.py
# FlyReady Lab - 영어면접 기능 강화 모듈
# Phase B3: 발음 분석, 문법 교정, 필러워드 감지

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# =============================================================================
# 1. 필러워드 감지 시스템
# =============================================================================

class FillerWordDetector:
    """영어 필러워드 감지기"""

    # 영어 필러워드 목록 (STT가 인식할 수 있는 형태)
    FILLER_WORDS = {
        # 일반적인 필러
        "um": 1.0,
        "uh": 1.0,
        "uhm": 1.0,
        "umm": 1.0,
        "er": 0.8,
        "err": 0.8,
        "ah": 0.7,
        "ahh": 0.7,

        # 단어형 필러
        "like": 0.5,  # 문맥에 따라 필러가 아닐 수 있음
        "you know": 0.9,
        "i mean": 0.8,
        "sort of": 0.7,
        "kind of": 0.7,
        "basically": 0.6,
        "actually": 0.5,
        "literally": 0.6,
        "honestly": 0.5,
        "right": 0.4,  # 문맥 의존

        # 반복/주저
        "so": 0.3,  # 문장 시작 시 필러 가능성
        "well": 0.4,
        "anyway": 0.5,
    }

    # 문맥상 필러로 볼 수 없는 패턴
    NON_FILLER_PATTERNS = [
        r"i would like to",
        r"i like working",
        r"what it's like",
        r"looks like",
        r"feel like",
        r"sounds like",
        r"seems like",
    ]

    @staticmethod
    def detect_fillers(text: str) -> Dict[str, Any]:
        """필러워드 감지

        Returns:
            {
                "fillers_found": [{"word": str, "count": int, "positions": [int]}],
                "total_filler_count": int,
                "filler_ratio": float,
                "fluency_score": int,  # 0-100
                "feedback": str,
                "suggestions": [str],
            }
        """
        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words)

        if total_words == 0:
            return {
                "fillers_found": [],
                "total_filler_count": 0,
                "filler_ratio": 0.0,
                "fluency_score": 50,
                "feedback": "분석할 텍스트가 없습니다.",
                "suggestions": [],
            }

        # 필러가 아닌 패턴 제거
        filtered_text = text_lower
        for pattern in FillerWordDetector.NON_FILLER_PATTERNS:
            filtered_text = re.sub(pattern, "", filtered_text)

        fillers_found = []
        total_filler_score = 0

        for filler, weight in FillerWordDetector.FILLER_WORDS.items():
            if " " in filler:
                # 구문형 필러
                count = filtered_text.count(filler)
            else:
                # 단어형 필러
                pattern = r'\b' + re.escape(filler) + r'\b'
                matches = re.findall(pattern, filtered_text)
                count = len(matches)

            if count > 0:
                # 위치 찾기
                positions = [m.start() for m in re.finditer(r'\b' + re.escape(filler.split()[0]) + r'\b', text_lower)]

                fillers_found.append({
                    "word": filler,
                    "count": count,
                    "weight": weight,
                    "positions": positions[:5],  # 최대 5개 위치
                })
                total_filler_score += count * weight

        # 필러 비율 계산
        filler_ratio = total_filler_score / total_words if total_words > 0 else 0

        # 유창성 점수 계산 (필러가 적을수록 높음)
        fluency_score = max(0, min(100, int(100 - filler_ratio * 200)))

        # 피드백 생성
        if filler_ratio < 0.02:
            feedback = "Excellent! 필러워드 사용이 거의 없어 매우 유창하게 들립니다."
            suggestions = []
        elif filler_ratio < 0.05:
            feedback = "Good! 약간의 필러워드가 있지만 자연스러운 수준입니다."
            suggestions = ["약간의 망설임이 있습니다. 연습하면 더 좋아질 것입니다."]
        elif filler_ratio < 0.10:
            feedback = "Average. 필러워드가 다소 많습니다. 의식적으로 줄여보세요."
            top_fillers = sorted(fillers_found, key=lambda x: x["count"] * x["weight"], reverse=True)[:3]
            suggestions = [f"'{f['word']}' 사용을 줄여보세요 ({f['count']}회 감지)" for f in top_fillers]
        else:
            feedback = "필러워드가 많이 감지됩니다. 유창성 연습이 필요합니다."
            suggestions = [
                "답변 전에 잠시 생각하고 말하기 시작하세요",
                "필러워드 대신 짧은 휴지(pause)를 사용하세요",
                "미리 답변 구조를 생각하고 연습하세요",
            ]

        return {
            "fillers_found": fillers_found,
            "total_filler_count": int(total_filler_score),
            "filler_ratio": round(filler_ratio, 4),
            "fluency_score": fluency_score,
            "feedback": feedback,
            "suggestions": suggestions,
        }


# 전역 인스턴스
filler_detector = FillerWordDetector()


# =============================================================================
# 2. 발음 분석 시스템
# =============================================================================

class PronunciationAnalyzer:
    """영어 발음 분석기 (STT 결과 기반)"""

    # 한국인이 자주 틀리는 발음 패턴
    KOREAN_SPEAKER_ISSUES = {
        # L/R 혼동
        "r_l_confusion": {
            "patterns": [
                (r"\blight\b", "right"),
                (r"\bright\b", "light"),
                (r"\bread\b", "lead"),
                (r"\blead\b", "read"),
                (r"\brice\b", "lice"),
                (r"\bplay\b", "pray"),
                (r"\bpray\b", "play"),
                (r"\bfly\b", "fry"),
                (r"\bfry\b", "fly"),
                (r"\bglass\b", "grass"),
                (r"\bgrass\b", "glass"),
                (r"\bcollect\b", "correct"),
            ],
            "description": "L과 R 발음 구분",
            "tip": "L은 혀가 윗니 뒤에 닿고, R은 혀가 어디에도 닿지 않습니다.",
        },
        # V/B 혼동
        "v_b_confusion": {
            "patterns": [
                (r"\bvery\b", "berry"),
                (r"\bvote\b", "boat"),
                (r"\bvest\b", "best"),
                (r"\bban\b", "van"),
                (r"\bbase\b", "vase"),
            ],
            "description": "V와 B 발음 구분",
            "tip": "V는 윗니가 아랫입술에 닿고 바람이 빠집니다.",
        },
        # F/P 혼동
        "f_p_confusion": {
            "patterns": [
                (r"\bfan\b", "pan"),
                (r"\bfull\b", "pull"),
                (r"\bfine\b", "pine"),
                (r"\bfight\b", "pight"),
                (r"\bfirst\b", "pirst"),
            ],
            "description": "F와 P 발음 구분",
            "tip": "F는 윗니가 아랫입술에 닿고 바람이 새어나옵니다.",
        },
        # TH 발음
        "th_issues": {
            "patterns": [
                (r"\bthink\b", "sink"),
                (r"\bthank\b", "tank"),
                (r"\bthree\b", "tree"),
                (r"\bthat\b", "dat"),
                (r"\bthe\b", "da"),
                (r"\bthem\b", "dem"),
            ],
            "description": "TH 발음",
            "tip": "TH는 혀 끝을 윗니와 아랫니 사이에 놓고 발음합니다.",
        },
        # 모음 길이
        "vowel_length": {
            "patterns": [
                (r"\bship\b", "sheep"),
                (r"\bsheep\b", "ship"),
                (r"\bbit\b", "beat"),
                (r"\bbeat\b", "bit"),
                (r"\bfull\b", "fool"),
                (r"\bfool\b", "full"),
            ],
            "description": "장모음/단모음 구분",
            "tip": "장모음은 길게, 단모음은 짧게 발음하세요.",
        },
        # 어미 자음
        "final_consonants": {
            "patterns": [
                (r"world(?!\w)", "worl"),
                (r"helped(?!\w)", "help"),
                (r"asked(?!\w)", "ask"),
                (r"worked(?!\w)", "work"),
            ],
            "description": "어미 자음 탈락",
            "tip": "단어 끝의 자음을 명확하게 발음하세요.",
        },
    }

    # 항공 관련 발음 주의 단어
    AVIATION_TERMS = {
        "turbulence": {"ipa": "/ˈtɜːrbjʊləns/", "common_error": "터불런스"},
        "passenger": {"ipa": "/ˈpæsɪndʒər/", "common_error": "패신저"},
        "emergency": {"ipa": "/ɪˈmɜːrdʒənsi/", "common_error": "이머전시"},
        "altitude": {"ipa": "/ˈæltɪtuːd/", "common_error": "알티튜드"},
        "fasten": {"ipa": "/ˈfæsn/", "common_error": "패스튼 (t 발음 안함)"},
        "aisle": {"ipa": "/aɪl/", "common_error": "아일 (s 묵음)"},
        "safety": {"ipa": "/ˈseɪfti/", "common_error": "세이프티"},
        "cabin": {"ipa": "/ˈkæbɪn/", "common_error": "캐빈"},
        "service": {"ipa": "/ˈsɜːrvɪs/", "common_error": "서비스"},
        "hospitality": {"ipa": "/ˌhɒspɪˈtæləti/", "common_error": "호스피탈리티"},
    }

    @staticmethod
    def analyze_pronunciation(
        transcribed_text: str,
        original_text: str = None
    ) -> Dict[str, Any]:
        """발음 분석 (STT 결과 기반)

        Args:
            transcribed_text: STT가 인식한 텍스트
            original_text: 원래 의도한 텍스트 (있으면 비교)

        Returns:
            분석 결과 딕셔너리
        """
        text_lower = transcribed_text.lower()
        issues_found = []
        aviation_terms_found = []

        # 한국인 발음 문제 패턴 검사
        for issue_type, issue_data in PronunciationAnalyzer.KOREAN_SPEAKER_ISSUES.items():
            for pattern, confused_with in issue_data["patterns"]:
                if re.search(pattern, text_lower):
                    # 혼동 가능성 있는 단어 발견
                    issues_found.append({
                        "type": issue_type,
                        "description": issue_data["description"],
                        "word_found": re.search(pattern, text_lower).group(),
                        "might_be": confused_with,
                        "tip": issue_data["tip"],
                    })

        # 항공 용어 체크
        for term, info in PronunciationAnalyzer.AVIATION_TERMS.items():
            if term in text_lower:
                aviation_terms_found.append({
                    "term": term,
                    "ipa": info["ipa"],
                    "common_error": info["common_error"],
                })

        # 점수 계산 (이슈가 적을수록 높음)
        issue_count = len(issues_found)
        if issue_count == 0:
            score = 95
            rating = "Excellent"
        elif issue_count <= 2:
            score = 85
            rating = "Good"
        elif issue_count <= 4:
            score = 70
            rating = "Average"
        else:
            score = 55
            rating = "Needs Practice"

        # 피드백 생성
        if issue_count == 0:
            feedback = "발음이 명확합니다. 좋은 영어 발음을 유지하세요."
        else:
            unique_types = list(set(i["type"] for i in issues_found))
            feedback = f"{len(unique_types)}가지 발음 영역에서 주의가 필요합니다."

        return {
            "score": score,
            "rating": rating,
            "issues_found": issues_found[:5],  # 최대 5개
            "issue_types": list(set(i["type"] for i in issues_found)),
            "aviation_terms": aviation_terms_found,
            "feedback": feedback,
            "total_issues": issue_count,
        }


# 전역 인스턴스
pronunciation_analyzer = PronunciationAnalyzer()


# =============================================================================
# 3. 문법 분석 시스템
# =============================================================================

class GrammarAnalyzer:
    """영어 문법 분석기"""

    # 일반적인 문법 오류 패턴
    GRAMMAR_PATTERNS = {
        # 주어-동사 일치
        "subject_verb_agreement": {
            "patterns": [
                (r"\bi am work\b", "I am working / I work"),
                (r"\bhe work\b", "he works"),
                (r"\bshe work\b", "she works"),
                (r"\bit work\b", "it works"),
                (r"\bthey works\b", "they work"),
                (r"\bwe works\b", "we work"),
                (r"\bi works\b", "I work"),
                (r"\bhe have\b", "he has"),
                (r"\bshe have\b", "she has"),
                (r"\bit have\b", "it has"),
            ],
            "category": "Subject-Verb Agreement",
            "description": "주어와 동사의 수 일치",
        },
        # 시제 오류
        "tense_errors": {
            "patterns": [
                (r"\bi am went\b", "I went / I have gone"),
                (r"\bi was go\b", "I went / I was going"),
                (r"\byesterday i go\b", "yesterday I went"),
                (r"\blast week i work\b", "last week I worked"),
                (r"\bnow i worked\b", "now I work / now I am working"),
            ],
            "category": "Tense",
            "description": "시제 사용",
        },
        # 관사 오류
        "article_errors": {
            "patterns": [
                (r"\bi am student\b", "I am a student"),
                (r"\bi want to be pilot\b", "I want to be a pilot"),
                (r"\bi am flight attendant\b", "I am a flight attendant"),
                (r"\bi have dream\b", "I have a dream"),
                (r"\bit is good idea\b", "it is a good idea"),
                (r"\bin the morning\b.*\bat morning\b", "in the morning"),
            ],
            "category": "Articles (a/an/the)",
            "description": "관사 사용",
        },
        # 전치사 오류
        "preposition_errors": {
            "patterns": [
                (r"\bi am good in\b", "I am good at"),
                (r"\bi interested in\b", "I am interested in"),
                (r"\bi am depend on\b", "I depend on"),
                (r"\blisten me\b", "listen to me"),
                (r"\barrived to\b", "arrived at/in"),
            ],
            "category": "Prepositions",
            "description": "전치사 사용",
        },
        # 불완전한 문장
        "incomplete_sentences": {
            "patterns": [
                (r"^because\b[^,\.]+$", "Because... (incomplete - needs main clause)"),
                (r"^although\b[^,\.]+$", "Although... (incomplete - needs main clause)"),
                (r"^if\b[^,\.]+$", "If... (incomplete - needs main clause)"),
            ],
            "category": "Sentence Structure",
            "description": "문장 완성도",
        },
        # 이중 부정
        "double_negatives": {
            "patterns": [
                (r"\bdon't have no\b", "don't have any / have no"),
                (r"\bcan't do nothing\b", "can't do anything / can do nothing"),
                (r"\bnever no\b", "never any"),
            ],
            "category": "Double Negatives",
            "description": "이중 부정 오류",
        },
    }

    @staticmethod
    def analyze_grammar(text: str) -> Dict[str, Any]:
        """문법 분석

        Returns:
            분석 결과 딕셔너리
        """
        text_lower = text.lower()
        errors_found = []

        # 패턴 기반 오류 검출
        for error_type, error_data in GrammarAnalyzer.GRAMMAR_PATTERNS.items():
            for pattern, correction in error_data["patterns"]:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    errors_found.append({
                        "type": error_type,
                        "category": error_data["category"],
                        "description": error_data["description"],
                        "found": match if isinstance(match, str) else match[0],
                        "suggestion": correction,
                    })

        # 점수 계산
        error_count = len(errors_found)
        if error_count == 0:
            score = 95
            rating = "Excellent"
        elif error_count <= 2:
            score = 80
            rating = "Good"
        elif error_count <= 4:
            score = 65
            rating = "Fair"
        else:
            score = 50
            rating = "Needs Improvement"

        # 카테고리별 요약
        category_summary = {}
        for error in errors_found:
            cat = error["category"]
            if cat not in category_summary:
                category_summary[cat] = 0
            category_summary[cat] += 1

        return {
            "score": score,
            "rating": rating,
            "errors_found": errors_found[:6],  # 최대 6개
            "error_count": error_count,
            "category_summary": category_summary,
            "feedback": GrammarAnalyzer._generate_feedback(error_count, category_summary),
        }

    @staticmethod
    def _generate_feedback(error_count: int, category_summary: Dict) -> str:
        """피드백 생성"""
        if error_count == 0:
            return "문법적으로 정확한 답변입니다!"

        most_common = max(category_summary, key=category_summary.get) if category_summary else None

        if most_common:
            return f"'{most_common}' 관련 문법에 주의가 필요합니다."
        return f"{error_count}개의 문법 오류가 감지되었습니다."


# 전역 인스턴스
grammar_analyzer = GrammarAnalyzer()


# =============================================================================
# 4. 말하기 속도 분석
# =============================================================================

class SpeakingPaceAnalyzer:
    """말하기 속도 분석기"""

    # 이상적인 말하기 속도 범위 (WPM)
    IDEAL_WPM_RANGE = (120, 160)

    # 면접 답변 권장 시간 (초)
    IDEAL_ANSWER_DURATION = (30, 90)

    @staticmethod
    def analyze_pace(
        text: str,
        duration_seconds: float
    ) -> Dict[str, Any]:
        """말하기 속도 분석

        Args:
            text: 말한 내용
            duration_seconds: 소요 시간 (초)

        Returns:
            분석 결과
        """
        words = text.split()
        word_count = len(words)

        if duration_seconds <= 0:
            duration_seconds = 1

        # WPM 계산
        wpm = (word_count / duration_seconds) * 60

        # 평가
        min_wpm, max_wpm = SpeakingPaceAnalyzer.IDEAL_WPM_RANGE
        min_dur, max_dur = SpeakingPaceAnalyzer.IDEAL_ANSWER_DURATION

        if min_wpm <= wpm <= max_wpm:
            pace_rating = "optimal"
            pace_score = 100
            pace_feedback = "적절한 말하기 속도입니다."
        elif wpm < min_wpm:
            pace_rating = "slow"
            pace_score = max(50, 100 - (min_wpm - wpm))
            pace_feedback = "말하기 속도가 다소 느립니다. 좀 더 자신감 있게 말해보세요."
        else:
            pace_rating = "fast"
            pace_score = max(50, 100 - (wpm - max_wpm) * 0.5)
            pace_feedback = "말하기 속도가 빠릅니다. 천천히 명확하게 말해보세요."

        # 답변 길이 평가
        if min_dur <= duration_seconds <= max_dur:
            duration_rating = "optimal"
            duration_feedback = "적절한 답변 길이입니다."
        elif duration_seconds < min_dur:
            duration_rating = "short"
            duration_feedback = "답변이 너무 짧습니다. 더 구체적으로 답변해보세요."
        else:
            duration_rating = "long"
            duration_feedback = "답변이 다소 깁니다. 핵심만 간결하게 말해보세요."

        return {
            "word_count": word_count,
            "duration_seconds": round(duration_seconds, 1),
            "wpm": round(wpm, 1),
            "pace_rating": pace_rating,
            "pace_score": int(pace_score),
            "pace_feedback": pace_feedback,
            "duration_rating": duration_rating,
            "duration_feedback": duration_feedback,
            "ideal_wpm_range": SpeakingPaceAnalyzer.IDEAL_WPM_RANGE,
        }


# 전역 인스턴스
pace_analyzer = SpeakingPaceAnalyzer()


# =============================================================================
# 5. 통합 영어 면접 분석 엔진
# =============================================================================

class EnhancedEnglishAnalyzer:
    """통합 영어 면접 분석 엔진"""

    def __init__(self):
        self.filler_detector = filler_detector
        self.pronunciation_analyzer = pronunciation_analyzer
        self.grammar_analyzer = grammar_analyzer
        self.pace_analyzer = pace_analyzer

    def analyze_answer(
        self,
        transcribed_text: str,
        question: str,
        duration_seconds: float = None
    ) -> Dict[str, Any]:
        """답변 종합 분석

        Args:
            transcribed_text: STT로 인식된 텍스트
            question: 면접 질문
            duration_seconds: 답변 소요 시간

        Returns:
            종합 분석 결과
        """
        # 1. 필러워드 분석
        filler_result = self.filler_detector.detect_fillers(transcribed_text)

        # 2. 발음 분석
        pronunciation_result = self.pronunciation_analyzer.analyze_pronunciation(transcribed_text)

        # 3. 문법 분석
        grammar_result = self.grammar_analyzer.analyze_grammar(transcribed_text)

        # 4. 말하기 속도 분석 (시간이 있으면)
        pace_result = None
        if duration_seconds and duration_seconds > 0:
            pace_result = self.pace_analyzer.analyze_pace(transcribed_text, duration_seconds)

        # 종합 점수 계산
        scores = {
            "fluency": filler_result["fluency_score"],
            "pronunciation": pronunciation_result["score"],
            "grammar": grammar_result["score"],
        }
        if pace_result:
            scores["pace"] = pace_result["pace_score"]

        # 가중 평균 (문법이 가장 중요)
        weights = {"fluency": 0.2, "pronunciation": 0.3, "grammar": 0.35, "pace": 0.15}
        total_weight = sum(weights[k] for k in scores.keys())
        weighted_sum = sum(scores[k] * weights.get(k, 0.2) for k in scores.keys())
        overall_score = int(weighted_sum / total_weight)

        # 등급 결정
        if overall_score >= 90:
            grade = "A"
            grade_text = "Excellent"
        elif overall_score >= 80:
            grade = "B"
            grade_text = "Good"
        elif overall_score >= 70:
            grade = "C"
            grade_text = "Fair"
        elif overall_score >= 60:
            grade = "D"
            grade_text = "Needs Practice"
        else:
            grade = "F"
            grade_text = "More Practice Needed"

        # 주요 개선점 정리
        improvements = []
        if filler_result["filler_ratio"] > 0.05:
            improvements.append("필러워드 줄이기")
        if pronunciation_result["total_issues"] > 2:
            improvements.append("발음 연습")
        if grammar_result["error_count"] > 2:
            improvements.append("문법 정확성")
        if pace_result and pace_result["pace_rating"] != "optimal":
            improvements.append("말하기 속도 조절")

        return {
            "overall_score": overall_score,
            "grade": grade,
            "grade_text": grade_text,
            "scores": scores,
            "filler_analysis": filler_result,
            "pronunciation_analysis": pronunciation_result,
            "grammar_analysis": grammar_result,
            "pace_analysis": pace_result,
            "improvements": improvements[:4],
            "word_count": len(transcribed_text.split()),
        }


# 전역 분석기
enhanced_english_analyzer = EnhancedEnglishAnalyzer()


# =============================================================================
# 편의 함수
# =============================================================================

def analyze_english_answer(
    text: str,
    question: str,
    duration_seconds: float = None
) -> Dict[str, Any]:
    """영어 답변 분석 (단일 함수)"""
    return enhanced_english_analyzer.analyze_answer(text, question, duration_seconds)


def get_filler_analysis(text: str) -> Dict[str, Any]:
    """필러워드 분석만"""
    return filler_detector.detect_fillers(text)


def get_pronunciation_analysis(text: str) -> Dict[str, Any]:
    """발음 분석만"""
    return pronunciation_analyzer.analyze_pronunciation(text)


def get_grammar_analysis(text: str) -> Dict[str, Any]:
    """문법 분석만"""
    return grammar_analyzer.analyze_grammar(text)


def get_pace_analysis(text: str, duration: float) -> Dict[str, Any]:
    """말하기 속도 분석만"""
    return pace_analyzer.analyze_pace(text, duration)


# =============================================================================
# 모듈 테스트
# =============================================================================

if __name__ == "__main__":
    print("=== English Interview Enhancer Test ===")

    test_text = "Um, I think, uh, I am very passionate about, you know, working as a flight attendant. I have work in service industry before and I am good in communicate with people."

    # 1. 필러워드 테스트
    print("\n1. Filler Words")
    filler_result = get_filler_analysis(test_text)
    print(f"   Fillers found: {filler_result['total_filler_count']}")
    print(f"   Fluency score: {filler_result['fluency_score']}")

    # 2. 발음 테스트
    print("\n2. Pronunciation")
    pron_result = get_pronunciation_analysis(test_text)
    print(f"   Score: {pron_result['score']}")
    print(f"   Issues: {pron_result['total_issues']}")

    # 3. 문법 테스트
    print("\n3. Grammar")
    grammar_result = get_grammar_analysis(test_text)
    print(f"   Score: {grammar_result['score']}")
    print(f"   Errors: {grammar_result['error_count']}")

    # 4. 종합 분석
    print("\n4. Full Analysis")
    full_result = analyze_english_answer(test_text, "Why do you want to be a flight attendant?", 45.0)
    print(f"   Overall: {full_result['overall_score']} ({full_result['grade']})")
    print(f"   Improvements: {full_result['improvements']}")

    print("\nModule ready!")
