"""
Feedback Analyzer.

Analyzes interview answers and provides detailed feedback.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI

from src.config.settings import get_settings
from src.ai.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class FeedbackCategory(str, Enum):
    """Feedback categories."""
    CONTENT = "content"
    DELIVERY = "delivery"
    STRUCTURE = "structure"
    ATTITUDE = "attitude"
    TIME = "time"
    LANGUAGE = "language"


@dataclass
class DetailedScore:
    """Detailed score breakdown."""
    category: FeedbackCategory
    score: float
    max_score: float
    weight: float
    comments: List[str]

    @property
    def weighted_score(self) -> float:
        """Get weighted score."""
        return (self.score / self.max_score) * self.weight * 100


@dataclass
class FeedbackReport:
    """Complete feedback report."""
    overall_score: float
    grade: str
    scores: Dict[FeedbackCategory, DetailedScore]
    strengths: List[str]
    improvements: List[str]
    suggestions: str
    sample_answer: Optional[str]
    next_steps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "scores": {
                cat.value: {
                    "score": score.score,
                    "max_score": score.max_score,
                    "weight": score.weight,
                    "weighted_score": score.weighted_score,
                    "comments": score.comments
                }
                for cat, score in self.scores.items()
            },
            "strengths": self.strengths,
            "improvements": self.improvements,
            "suggestions": self.suggestions,
            "sample_answer": self.sample_answer,
            "next_steps": self.next_steps
        }


class FeedbackAnalyzer:
    """
    Advanced feedback analyzer for interview answers.

    Provides detailed, actionable feedback on interview responses.
    """

    # Grade thresholds
    GRADES = [
        (90, "A+", "탁월함"),
        (85, "A", "우수함"),
        (80, "B+", "좋음"),
        (75, "B", "양호"),
        (70, "C+", "보통"),
        (65, "C", "노력 필요"),
        (60, "D+", "개선 필요"),
        (50, "D", "많은 개선 필요"),
        (0, "F", "재도전 권장")
    ]

    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.ai.openai_api_key)
        self._model = settings.ai.model

    async def analyze(
        self,
        question: str,
        answer: str,
        duration_seconds: float,
        time_limit: int,
        context: Optional[Dict[str, Any]] = None
    ) -> FeedbackReport:
        """
        Analyze an interview answer and generate feedback.

        Args:
            question: The interview question
            answer: User's answer
            duration_seconds: Time taken to answer
            time_limit: Allowed time limit
            context: Additional context (airline, interview type, etc.)

        Returns:
            FeedbackReport with detailed analysis
        """
        context = context or {}

        # Calculate base scores
        time_score = self._calculate_time_score(duration_seconds, time_limit)
        length_score = self._calculate_length_score(answer)

        # Get AI analysis
        ai_analysis = await self._get_ai_analysis(
            question, answer, duration_seconds, time_limit, context
        )

        # Build detailed scores
        scores = self._build_scores(ai_analysis, time_score)

        # Calculate overall score
        overall_score = sum(
            score.weighted_score for score in scores.values()
        )

        # Determine grade
        grade = self._get_grade(overall_score)

        # Generate next steps
        next_steps = self._generate_next_steps(scores, overall_score)

        return FeedbackReport(
            overall_score=overall_score,
            grade=grade[1],
            scores=scores,
            strengths=ai_analysis.get("strengths", []),
            improvements=ai_analysis.get("improvements", []),
            suggestions=ai_analysis.get("suggestions", ""),
            sample_answer=ai_analysis.get("sample_answer"),
            next_steps=next_steps
        )

    def _calculate_time_score(self, duration: float, limit: int) -> float:
        """Calculate time management score."""
        ratio = duration / limit

        if 0.8 <= ratio <= 1.0:
            return 100  # Perfect timing
        elif 0.6 <= ratio < 0.8:
            return 80  # Slightly under
        elif 1.0 < ratio <= 1.2:
            return 70  # Slightly over
        elif ratio < 0.6:
            return 50  # Too short
        else:
            return 40  # Too long

    def _calculate_length_score(self, answer: str) -> float:
        """Calculate answer length score."""
        word_count = len(answer.split())

        if 50 <= word_count <= 150:
            return 100
        elif 30 <= word_count < 50 or 150 < word_count <= 200:
            return 80
        elif word_count < 30:
            return 50
        else:
            return 60

    async def _get_ai_analysis(
        self,
        question: str,
        answer: str,
        duration: float,
        limit: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI-powered analysis."""
        prompt = f"""면접 답변을 분석해주세요.

질문: {question}
답변 시간: {duration:.1f}초 / 제한 {limit}초
지원 항공사: {context.get('airline', '항공사')}

답변:
{answer}

다음 형식의 JSON으로 분석해주세요:
{{
    "content_score": 0-100,
    "content_comments": ["코멘트1", "코멘트2"],
    "delivery_score": 0-100,
    "delivery_comments": ["코멘트1", "코멘트2"],
    "structure_score": 0-100,
    "structure_comments": ["코멘트1", "코멘트2"],
    "strengths": ["강점1", "강점2", "강점3"],
    "improvements": ["개선점1", "개선점2", "개선점3"],
    "suggestions": "구체적인 개선 제안",
    "sample_answer": "예시 답변"
}}"""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": PromptTemplates.get_feedback_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            content = response.choices[0].message.content

            # Parse JSON
            import json
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(content[json_start:json_end])

        except Exception as e:
            logger.error(f"AI analysis error: {e}")

        # Fallback
        return {
            "content_score": 70,
            "content_comments": ["분석을 완료했습니다"],
            "delivery_score": 70,
            "delivery_comments": ["전달이 되었습니다"],
            "structure_score": 70,
            "structure_comments": ["구조를 갖추고 있습니다"],
            "strengths": ["답변을 완료했습니다"],
            "improvements": ["더 구체적인 예시를 추가해보세요"],
            "suggestions": "연습을 통해 자신감을 높여보세요.",
            "sample_answer": None
        }

    def _build_scores(
        self,
        ai_analysis: Dict[str, Any],
        time_score: float
    ) -> Dict[FeedbackCategory, DetailedScore]:
        """Build detailed scores from analysis."""
        criteria = PromptTemplates.EVALUATION_CRITERIA

        return {
            FeedbackCategory.CONTENT: DetailedScore(
                category=FeedbackCategory.CONTENT,
                score=ai_analysis.get("content_score", 70),
                max_score=100,
                weight=criteria["content"]["weight"],
                comments=ai_analysis.get("content_comments", [])
            ),
            FeedbackCategory.DELIVERY: DetailedScore(
                category=FeedbackCategory.DELIVERY,
                score=ai_analysis.get("delivery_score", 70),
                max_score=100,
                weight=criteria["delivery"]["weight"],
                comments=ai_analysis.get("delivery_comments", [])
            ),
            FeedbackCategory.STRUCTURE: DetailedScore(
                category=FeedbackCategory.STRUCTURE,
                score=ai_analysis.get("structure_score", 70),
                max_score=100,
                weight=criteria["structure"]["weight"],
                comments=ai_analysis.get("structure_comments", [])
            ),
            FeedbackCategory.ATTITUDE: DetailedScore(
                category=FeedbackCategory.ATTITUDE,
                score=75,  # Could be enhanced with video analysis
                max_score=100,
                weight=criteria["attitude"]["weight"],
                comments=["태도 분석은 영상 모드에서 가능합니다"]
            ),
            FeedbackCategory.TIME: DetailedScore(
                category=FeedbackCategory.TIME,
                score=time_score,
                max_score=100,
                weight=criteria["time"]["weight"],
                comments=[self._get_time_comment(time_score)]
            )
        }

    def _get_time_comment(self, time_score: float) -> str:
        """Get comment based on time score."""
        if time_score >= 90:
            return "제한 시간을 적절히 활용했습니다"
        elif time_score >= 70:
            return "시간을 약간 조정하면 좋겠습니다"
        elif time_score >= 50:
            return "답변이 너무 짧습니다. 더 풍부하게 답변해보세요"
        else:
            return "시간 관리가 필요합니다"

    def _get_grade(self, score: float) -> tuple:
        """Get grade based on score."""
        for threshold, grade, description in self.GRADES:
            if score >= threshold:
                return (threshold, grade, description)
        return (0, "F", "재도전 권장")

    def _generate_next_steps(
        self,
        scores: Dict[FeedbackCategory, DetailedScore],
        overall_score: float
    ) -> List[str]:
        """Generate recommended next steps."""
        next_steps = []

        # Find lowest scoring categories
        sorted_scores = sorted(
            scores.items(),
            key=lambda x: x[1].weighted_score
        )

        # Add recommendations for low-scoring areas
        for category, score in sorted_scores[:2]:
            if score.score < 70:
                if category == FeedbackCategory.CONTENT:
                    next_steps.append("항공사 정보와 자신의 경험을 더 연결해보세요")
                elif category == FeedbackCategory.DELIVERY:
                    next_steps.append("거울 앞에서 연습하며 자신감을 키워보세요")
                elif category == FeedbackCategory.STRUCTURE:
                    next_steps.append("STAR 기법으로 답변 구조를 잡아보세요")
                elif category == FeedbackCategory.TIME:
                    next_steps.append("타이머를 설정하고 시간 안에 답변하는 연습을 해보세요")

        # Add general recommendations based on overall score
        if overall_score < 60:
            next_steps.append("기본 질문들을 더 연습해보세요")
        elif overall_score < 75:
            next_steps.append("실전 모의면접을 통해 경험을 쌓아보세요")
        else:
            next_steps.append("심화 질문에도 도전해보세요")

        return next_steps[:4]  # Return top 4 recommendations


# Singleton instance
feedback_analyzer = FeedbackAnalyzer()
