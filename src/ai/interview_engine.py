"""
AI Interview Engine.

Manages AI-powered mock interview sessions.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import uuid

from openai import OpenAI, AsyncOpenAI

from src.config.settings import get_settings
from src.ai.prompts import PromptTemplates, InterviewType

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Interview session states."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    ANSWERING = "answering"
    FEEDBACK = "feedback"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class InterviewQuestion:
    """Represents a single interview question."""
    id: str
    question: str
    time_limit: int
    tips: Optional[str] = None
    asked_at: Optional[datetime] = None
    answer: Optional[str] = None
    answer_duration: Optional[float] = None
    feedback: Optional[Dict[str, Any]] = None


@dataclass
class InterviewSession:
    """Represents a complete interview session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    interview_type: InterviewType = InterviewType.SELF_INTRODUCTION
    airline_name: str = "항공사"

    state: SessionState = SessionState.CREATED
    questions: List[InterviewQuestion] = field(default_factory=list)
    current_question_index: int = 0

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    overall_score: float = 0.0
    overall_feedback: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def current_question(self) -> Optional[InterviewQuestion]:
        """Get current question."""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    @property
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.state == SessionState.COMPLETED

    @property
    def progress(self) -> float:
        """Get session progress (0-1)."""
        if not self.questions:
            return 0.0
        return self.current_question_index / len(self.questions)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "interview_type": self.interview_type.value,
            "airline_name": self.airline_name,
            "state": self.state.value,
            "current_question_index": self.current_question_index,
            "total_questions": len(self.questions),
            "progress": self.progress,
            "overall_score": self.overall_score,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class InterviewEngine:
    """
    AI-powered interview engine.

    Manages interview sessions, asks questions, and provides feedback.
    """

    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.ai.openai_api_key)
        self._model = settings.ai.model
        self._max_tokens = settings.ai.max_tokens

        # Active sessions
        self._sessions: Dict[str, InterviewSession] = {}

    async def create_session(
        self,
        user_id: str,
        interview_type: InterviewType,
        airline_name: str = "항공사",
        num_questions: int = 5
    ) -> InterviewSession:
        """
        Create a new interview session.

        Args:
            user_id: User identifier
            interview_type: Type of interview
            airline_name: Target airline name
            num_questions: Number of questions to ask

        Returns:
            Created InterviewSession
        """
        # Get questions
        all_questions = PromptTemplates.get_questions(interview_type, airline_name)

        # Select questions (could add randomization or personalization)
        selected = all_questions[:num_questions]

        questions = [
            InterviewQuestion(
                id=str(uuid.uuid4()),
                question=q["question"],
                time_limit=q["time_limit"],
                tips=q.get("tips")
            )
            for q in selected
        ]

        session = InterviewSession(
            user_id=user_id,
            interview_type=interview_type,
            airline_name=airline_name,
            questions=questions
        )

        self._sessions[session.id] = session
        logger.info(f"Created interview session {session.id} for user {user_id}")

        return session

    async def start_session(self, session_id: str) -> InterviewSession:
        """Start an interview session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.state = SessionState.IN_PROGRESS
        session.started_at = datetime.utcnow()

        return session

    async def get_next_question(self, session_id: str) -> Optional[InterviewQuestion]:
        """
        Get the next question in the session.

        Returns:
            Next question or None if session is complete
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.current_question_index >= len(session.questions):
            return None

        question = session.questions[session.current_question_index]
        question.asked_at = datetime.utcnow()
        session.state = SessionState.ANSWERING

        return question

    async def submit_answer(
        self,
        session_id: str,
        answer: str,
        duration_seconds: float
    ) -> Dict[str, Any]:
        """
        Submit an answer and get feedback.

        Args:
            session_id: Session identifier
            answer: User's answer
            duration_seconds: Time taken to answer

        Returns:
            Feedback dictionary
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        question = session.current_question
        if not question:
            raise ValueError("No current question")

        # Store answer
        question.answer = answer
        question.answer_duration = duration_seconds

        # Get AI feedback
        session.state = SessionState.FEEDBACK
        feedback = await self._analyze_answer(question)
        question.feedback = feedback

        # Move to next question
        session.current_question_index += 1

        # Check if session is complete
        if session.current_question_index >= len(session.questions):
            await self._complete_session(session)

        return feedback

    async def _analyze_answer(self, question: InterviewQuestion) -> Dict[str, Any]:
        """Analyze answer using AI."""
        prompt = PromptTemplates.create_feedback_prompt(
            question=question.question,
            answer=question.answer,
            answer_duration=question.answer_duration,
            time_limit=question.time_limit
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": PromptTemplates.get_feedback_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self._max_tokens,
                temperature=0.7
            )

            content = response.choices[0].message.content

            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    feedback = json.loads(content[json_start:json_end])
                else:
                    raise json.JSONDecodeError("No JSON found", content, 0)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                feedback = {
                    "overall_score": 70,
                    "scores": {
                        "content": 70,
                        "delivery": 70,
                        "structure": 70,
                        "attitude": 70,
                        "time": 70
                    },
                    "strengths": ["답변을 완료했습니다"],
                    "improvements": ["더 구체적인 예시를 추가해보세요"],
                    "suggestions": content,
                    "sample_answer": None
                }

            return feedback

        except Exception as e:
            logger.error(f"Error analyzing answer: {e}")
            return {
                "overall_score": 0,
                "error": str(e),
                "suggestions": "피드백 생성 중 오류가 발생했습니다."
            }

    async def _complete_session(self, session: InterviewSession) -> None:
        """Complete the interview session and calculate final scores."""
        session.state = SessionState.COMPLETED
        session.completed_at = datetime.utcnow()

        # Calculate overall score
        total_score = 0
        answered_count = 0

        for q in session.questions:
            if q.feedback and "overall_score" in q.feedback:
                total_score += q.feedback["overall_score"]
                answered_count += 1

        if answered_count > 0:
            session.overall_score = total_score / answered_count

        # Generate overall feedback
        session.overall_feedback = await self._generate_overall_feedback(session)

        logger.info(
            f"Completed session {session.id} with score {session.overall_score:.1f}"
        )

    async def _generate_overall_feedback(self, session: InterviewSession) -> str:
        """Generate overall session feedback."""
        summary_prompt = f"""면접 세션 전체 요약을 해주세요.

면접 유형: {session.interview_type.value}
전체 점수: {session.overall_score:.1f}점
질문 수: {len(session.questions)}

각 질문별 결과:
"""
        for i, q in enumerate(session.questions, 1):
            score = q.feedback.get("overall_score", 0) if q.feedback else 0
            summary_prompt += f"\n{i}. {q.question}\n   점수: {score}점\n"

        summary_prompt += "\n\n전체적인 강점, 개선점, 다음 단계 제안을 포함해 요약해주세요."

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": PromptTemplates.get_feedback_prompt()},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating overall feedback: {e}")
            return f"면접 완료. 전체 점수: {session.overall_score:.1f}점"

    async def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    async def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get detailed session results."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        return {
            "session": session.to_dict(),
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "time_limit": q.time_limit,
                    "answer": q.answer,
                    "answer_duration": q.answer_duration,
                    "feedback": q.feedback
                }
                for q in session.questions
            ],
            "overall_score": session.overall_score,
            "overall_feedback": session.overall_feedback
        }

    async def cancel_session(self, session_id: str) -> None:
        """Cancel a session."""
        session = self._sessions.get(session_id)
        if session:
            session.state = SessionState.CANCELLED
            logger.info(f"Cancelled session {session_id}")

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed = 0

        for session_id in list(self._sessions.keys()):
            session = self._sessions[session_id]
            if session.started_at and session.started_at < cutoff:
                del self._sessions[session_id]
                removed += 1

        if removed:
            logger.info(f"Cleaned up {removed} old interview sessions")

        return removed


# Singleton instance
interview_engine = InterviewEngine()
