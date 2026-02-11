"""
초안 생성기 핵심 로직
DraftGenerator 클래스: 채팅형 인터뷰 -> 초안 생성 -> 60점 보정
"""

import json
import re
from typing import Optional, Dict, Any, Tuple

from utils.llm_client import call_openai_chat
from utils.prompt_templates import score_by_code
from utils.draft_prompts import build_draft_prompt, get_adjustment_prompt
from data.interview_questions import (
    get_questions,
    get_question_count,
    get_interviewer_prompt,
    INTERVIEWER_SYSTEM_PROMPT
)


class DraftGenerator:
    """
    초안 생성기 메인 클래스
    채팅형 인터뷰 -> 초안 생성 -> 첨삭 연결
    """

    def __init__(self, question_num: int):
        """
        Args:
            question_num: 문항 번호 (1, 2, 3)
        """
        self.question_num = question_num
        self.questions = get_questions(question_num)
        self.total_questions = get_question_count(question_num)
        self.current_q = 0
        self.answers = {}
        self.conversation_history = []
        self.state = "interviewing"  # interviewing -> generating -> done

    def get_first_question(self) -> str:
        """첫 번째 질문 반환"""
        if self.questions:
            return self.questions[0]["question"]
        return "질문을 불러오는데 실패했습니다."

    def get_current_question(self) -> Optional[Dict]:
        """현재 질문 정보 반환"""
        if self.current_q < len(self.questions):
            return self.questions[self.current_q]
        return None

    def get_progress(self) -> Tuple[int, int]:
        """진행 상황 반환 (현재, 전체)"""
        return self.current_q, self.total_questions

    def process_answer(self, user_input: str) -> Dict[str, Any]:
        """
        사용자 답변 처리 -> 다음 질문 or 초안 생성

        Args:
            user_input: 사용자 답변

        Returns:
            {
                "type": "followup" | "next_question" | "generate" | "challenge",
                "message": str,
                "progress": (current, total)
            }
        """
        # 현재 질문에 대한 답변 저장
        current_question = self.get_current_question()
        if current_question:
            self.answers[current_question["id"]] = {
                "question": current_question["question"],
                "answer": user_input,
                "intent": current_question.get("intent", "")
            }

        # 대화 기록 추가
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # 1. 답변이 너무 짧으면 후속 질문 (다양한 유도 질문 사용)
        if len(user_input.strip()) < 15:
            # 연속 짧은 답변 카운트
            if "short_answer_count" not in self.__dict__:
                self.short_answer_count = 0
            self.short_answer_count += 1

            # 질문별 맞춤 후속 질문
            current_q = self.get_current_question()
            q_id = current_q["id"] if current_q else ""

            # 다양한 후속 질문 풀
            followup_options = {
                "q1_1": [  # 왜 대한항공?
                    "대한항공만의 특별한 점이 뭐라고 생각해요?",
                    "대한항공 비행기 타본 적 있어요? 그때 느낀 게 있다면요?",
                    "다른 항공사 말고 대한항공이어야 하는 이유가 있을까요?"
                ],
                "q1_2": [  # 서비스 경험
                    "어떤 일이었는지 조금만 더 설명해줄 수 있어요?",
                    "그 경험에서 구체적으로 뭘 했어요?",
                    "그때 어떤 역할이었어요?"
                ],
                "default": [
                    "조금만 더 자세히 말해줄 수 있어요?",
                    "예를 들어서 설명해줄 수 있을까요?",
                    "그게 어떤 의미인지 더 이야기해주세요."
                ]
            }

            # 3번 이상 짧은 답변이면 그냥 넘어가기
            if self.short_answer_count >= 3:
                self.short_answer_count = 0
                # 현재 답변 저장하고 다음으로
                if current_q:
                    self.answers[current_q["id"]] = {
                        "question": current_q["question"],
                        "answer": user_input + " (간략 답변)",
                        "intent": current_q.get("intent", "")
                    }
                self.current_q += 1

                if self.current_q >= len(self.questions):
                    self.state = "generating"
                    return {
                        "type": "generate",
                        "message": "알겠어요, 충분해요. 초안을 만들어볼게요.",
                        "progress": self.get_progress()
                    }

                next_q = self.questions[self.current_q]
                return {
                    "type": "next_question",
                    "message": f"알겠어요. 다음 질문으로 넘어갈게요.\n\n{next_q['question']}",
                    "progress": self.get_progress()
                }

            # 맞춤형 후속 질문 선택
            options = followup_options.get(q_id, followup_options["default"])
            response_msg = options[min(self.short_answer_count - 1, len(options) - 1)]

            self.conversation_history.append({
                "role": "assistant",
                "content": response_msg
            })
            return {
                "type": "followup",
                "message": response_msg,
                "progress": self.get_progress()
            }

        # 2. 탈락 패턴 감지 시 방향 전환
        if current_question and "warning_triggers" in current_question:
            for trigger in current_question["warning_triggers"]:
                if trigger in user_input:
                    warning_msg = current_question.get(
                        "warning_response",
                        "다른 관점에서 생각해볼까요?"
                    )
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": warning_msg
                    })
                    return {
                        "type": "challenge",
                        "message": warning_msg,
                        "progress": self.get_progress()
                    }

        # 3. 다음 질문으로
        self.current_q += 1

        # 4. 모든 질문 완료 체크
        if self.current_q >= len(self.questions):
            self.state = "generating"
            return {
                "type": "generate",
                "message": "좋아요, 충분히 모았어요. 초안을 만들어볼게요.",
                "progress": self.get_progress()
            }

        # 5. 다음 질문 반환
        next_q = self.questions[self.current_q]
        self.conversation_history.append({
            "role": "assistant",
            "content": next_q["question"]
        })

        return {
            "type": "next_question",
            "message": next_q["question"],
            "progress": self.get_progress()
        }

    def generate_draft(self) -> str:
        """
        수집된 답변 -> 60 +/- 3점 초안 생성
        """
        # 답변 데이터 준비
        answers_for_prompt = {}
        for q_id, data in self.answers.items():
            answers_for_prompt[data["question"]] = data["answer"]

        # 초안 생성 프롬프트 빌드
        prompt = build_draft_prompt(self.question_num, answers_for_prompt)

        # GPT 호출
        messages = [
            {"role": "system", "content": "당신은 대한항공 자소서 초안 작성기입니다. 사용자 경험만 사용하고 절대로 창작하지 않습니다."},
            {"role": "user", "content": prompt}
        ]

        result = call_openai_chat(messages, model="gpt-4o-mini")

        if result:
            draft = result["content"]
            # 글자수 조정
            draft = self._adjust_length(draft)
            # 탈락 패턴 제거
            draft = self._remove_fatal_patterns(draft)
            self.state = "done"
            return draft

        return "[오류] 초안 생성에 실패했습니다. 다시 시도해주세요."

    def generate_calibrated_draft(self, target: int = 60, tolerance: int = 3) -> Tuple[str, int]:
        """
        60 +/- 3점이 될 때까지 최대 3회 재생성

        Args:
            target: 목표 점수 (기본 60)
            tolerance: 허용 오차 (기본 3)

        Returns:
            (draft: str, code_score: int)
        """
        for attempt in range(3):
            # 초안 생성
            draft = self.generate_draft()

            if draft.startswith("[오류]"):
                return draft, 0

            # 코드 채점 실행 (빠름)
            code_result = score_by_code(draft, self.question_num)
            code_score = code_result["total"]

            # 목표 범위 (33~39) 체크 (60점 중 35~38 = 전체 57~63)
            target_min = int(target * 0.55) - tolerance  # ~33
            target_max = int(target * 0.65) + tolerance  # ~42

            if target_min <= code_score <= target_max:
                return draft, code_score

            # 범위 벗어나면 조정
            if code_score > target_max:
                # 너무 높음 -> 약점 추가
                draft = self._adjust_draft(draft, "reduce_score")
            elif code_score < target_min:
                # 너무 낮음 -> 보강
                draft = self._adjust_draft(draft, "increase_score")

        # 3회 시도 후 최선의 결과 반환
        final_result = score_by_code(draft, self.question_num)
        return draft, final_result["total"]

    def _adjust_draft(self, draft: str, adjustment_type: str) -> str:
        """점수 조정을 위한 초안 수정"""
        adjustment_prompt = get_adjustment_prompt(adjustment_type)
        if not adjustment_prompt:
            return draft

        messages = [
            {"role": "system", "content": "당신은 자소서 수정 전문가입니다. 지시에 따라 초안을 수정합니다."},
            {"role": "user", "content": f"[현재 초안]\n{draft}\n\n{adjustment_prompt}"}
        ]

        result = call_openai_chat(messages, model="gpt-4o-mini")
        if result:
            return result["content"]
        return draft

    def _adjust_length(self, text: str) -> str:
        """540~580자로 조정"""
        # 공백/줄바꿈 제외 글자수
        char_count = len(text.replace(" ", "").replace("\n", ""))

        if char_count > 590:
            # 너무 길면 마지막 문장 줄이기
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
            if len(sentences) > 2:
                # 마지막 문장 제거 후 재조합
                text = " ".join(sentences[:-1]) + "."

        elif char_count < 530:
            # 너무 짧은 경우는 그대로 (추가 생성은 위험)
            pass

        return text

    def _remove_fatal_patterns(self, text: str) -> str:
        """탈락 패턴 최종 제거"""
        fatal_patterns = [
            "어릴 때부터",
            "승무원 언니",
            "하늘을 나는 꿈",
            "남들이 싫어해서",
            "팀을 위해 희생",
            "아무도 안 해서",
            "최선을 다하겠습니다"
        ]

        for pattern in fatal_patterns:
            if pattern in text:
                # 해당 표현 제거 (단순 제거보다 대체가 좋지만 일단 제거)
                text = text.replace(pattern, "")

        # 연속 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def get_collected_answers(self) -> Dict:
        """수집된 답변 반환 (디버깅/확인용)"""
        return self.answers

    def reset(self):
        """상태 초기화"""
        self.current_q = 0
        self.answers = {}
        self.conversation_history = []
        self.state = "interviewing"


def validate_draft_score(draft: str, question_num: int, target: int = 60) -> Dict[str, Any]:
    """
    초안 점수 검증

    Returns:
        {
            "code_score": int,  # 코드 채점 점수 (60점 만점)
            "estimated_total": int,  # 예상 총점 (100점 만점)
            "in_range": bool,  # 목표 범위 내 여부
            "details": dict  # 상세 채점 결과
        }
    """
    code_result = score_by_code(draft, question_num)
    code_score = code_result["total"]

    # AI 채점 없이 코드 점수만으로 예상 총점 계산
    # 코드 60점 + AI 40점 가정, AI는 평균 22점 추정
    estimated_ai = 22
    estimated_total = code_score + estimated_ai

    # 목표 범위: 57~63
    in_range = (target - 3) <= estimated_total <= (target + 3)

    return {
        "code_score": code_score,
        "estimated_total": estimated_total,
        "in_range": in_range,
        "details": code_result
    }
