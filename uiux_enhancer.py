# -*- coding: utf-8 -*-
"""
uiux_enhancer.py
G. UI/UX (-) 해결 모듈

해결하는 문제:
30. 용어 불일치 → 전체 용어 통일
31. 진행률 불명확 → 모든 연습에 진행 바 추가
32. 뒤로가기 일관성 없음 → 통일된 네비게이션
33. 로딩 지루함 → 로딩 중 팁/격려 메시지
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import random


# ============================================================
# 30. 용어 통일
# ============================================================

class UITermType(Enum):
    """UI 용어 유형"""
    BUTTON = "button"
    MESSAGE = "message"
    TITLE = "title"
    PLACEHOLDER = "placeholder"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class UITerm:
    """UI 용어"""
    term_id: str
    term_type: UITermType
    korean: str
    context: str  # 사용 맥락


class TermStandardizer:
    """용어 표준화 시스템"""

    # 표준화된 용어 사전
    STANDARD_TERMS = {
        # 버튼 용어
        "btn_retry": UITerm("btn_retry", UITermType.BUTTON, "다시 시도", "재시도 버튼"),
        "btn_next": UITerm("btn_next", UITermType.BUTTON, "다음", "다음 단계 버튼"),
        "btn_prev": UITerm("btn_prev", UITermType.BUTTON, "이전", "이전 단계 버튼"),
        "btn_start": UITerm("btn_start", UITermType.BUTTON, "시작하기", "시작 버튼"),
        "btn_submit": UITerm("btn_submit", UITermType.BUTTON, "제출하기", "제출 버튼"),
        "btn_confirm": UITerm("btn_confirm", UITermType.BUTTON, "확인", "확인 버튼"),
        "btn_cancel": UITerm("btn_cancel", UITermType.BUTTON, "취소", "취소 버튼"),
        "btn_save": UITerm("btn_save", UITermType.BUTTON, "저장하기", "저장 버튼"),
        "btn_finish": UITerm("btn_finish", UITermType.BUTTON, "완료하기", "완료 버튼"),
        "btn_back": UITerm("btn_back", UITermType.BUTTON, "돌아가기", "뒤로가기 버튼"),
        "btn_home": UITerm("btn_home", UITermType.BUTTON, "홈으로", "홈 버튼"),
        "btn_record": UITerm("btn_record", UITermType.BUTTON, "녹음하기", "녹음 시작 버튼"),
        "btn_stop": UITerm("btn_stop", UITermType.BUTTON, "녹음 중지", "녹음 중지 버튼"),

        # 메시지 용어
        "msg_loading": UITerm("msg_loading", UITermType.MESSAGE, "불러오는 중...", "로딩 메시지"),
        "msg_processing": UITerm("msg_processing", UITermType.MESSAGE, "처리 중...", "처리 중 메시지"),
        "msg_analyzing": UITerm("msg_analyzing", UITermType.MESSAGE, "분석 중...", "분석 중 메시지"),
        "msg_saving": UITerm("msg_saving", UITermType.MESSAGE, "저장 중...", "저장 중 메시지"),
        "msg_success": UITerm("msg_success", UITermType.MESSAGE, "완료되었습니다!", "성공 메시지"),
        "msg_error": UITerm("msg_error", UITermType.MESSAGE, "오류가 발생했습니다", "에러 메시지"),
        "msg_empty": UITerm("msg_empty", UITermType.MESSAGE, "내용이 없습니다", "빈 상태 메시지"),

        # 제목 용어
        "title_result": UITerm("title_result", UITermType.TITLE, "결과 분석", "결과 섹션 제목"),
        "title_feedback": UITerm("title_feedback", UITermType.TITLE, "피드백", "피드백 섹션 제목"),
        "title_score": UITerm("title_score", UITermType.TITLE, "점수", "점수 섹션 제목"),
        "title_improvement": UITerm("title_improvement", UITermType.TITLE, "개선점", "개선점 섹션 제목"),
        "title_strength": UITerm("title_strength", UITermType.TITLE, "잘한 점", "장점 섹션 제목"),

        # 플레이스홀더
        "ph_answer": UITerm("ph_answer", UITermType.PLACEHOLDER, "답변을 입력해주세요...", "답변 입력창"),
        "ph_search": UITerm("ph_search", UITermType.PLACEHOLDER, "검색어를 입력하세요", "검색창"),
    }

    # 비표준 용어 → 표준 용어 매핑
    LEGACY_MAPPING = {
        "다시하기": "btn_retry",
        "다시 도전하기": "btn_retry",
        "재시도": "btn_retry",
        "다음으로": "btn_next",
        "다음 단계": "btn_next",
        "이전으로": "btn_prev",
        "뒤로": "btn_back",
        "뒤로 가기": "btn_back",
        "처리중...": "msg_processing",
        "로딩중...": "msg_loading",
        "분석중...": "msg_analyzing",
    }

    def __init__(self):
        pass

    def get_term(self, term_id: str) -> str:
        """표준 용어 조회"""
        term = self.STANDARD_TERMS.get(term_id)
        return term.korean if term else term_id

    def standardize(self, text: str) -> str:
        """비표준 용어를 표준 용어로 변환"""
        term_id = self.LEGACY_MAPPING.get(text)
        if term_id:
            return self.get_term(term_id)
        return text

    def get_all_terms(self, term_type: UITermType = None) -> Dict[str, str]:
        """모든 용어 조회"""
        terms = self.STANDARD_TERMS.values()
        if term_type:
            terms = [t for t in terms if t.term_type == term_type]
        return {t.term_id: t.korean for t in terms}

    def get_term_reference(self) -> Dict[str, List[Dict]]:
        """용어 참조표"""
        reference = {}
        for term in self.STANDARD_TERMS.values():
            type_name = term.term_type.value
            if type_name not in reference:
                reference[type_name] = []
            reference[type_name].append({
                "id": term.term_id,
                "korean": term.korean,
                "context": term.context
            })
        return reference


# ============================================================
# 31. 진행률 표시
# ============================================================

@dataclass
class ProgressState:
    """진행 상태"""
    current_step: int
    total_steps: int
    step_name: str
    is_complete: bool = False

    @property
    def percent(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100

    @property
    def fraction_text(self) -> str:
        return f"{self.current_step}/{self.total_steps}"


class ProgressBarManager:
    """진행 바 관리자"""

    # 페이지별 단계 정의
    PAGE_STEPS = {
        "모의면접": ["질문 준비", "답변 녹음", "분석 중", "결과 확인"],
        "롤플레잉": ["시나리오 선택", "상황 진행", "응답 분석", "점수 확인"],
        "영어면접": ["질문 선택", "답변 녹음", "발음 분석", "문법 분석", "결과"],
        "토론면접": ["주제 확인", "입장 선택", "토론 진행", "반론 대응", "평가"],
        "자소서첨삭": ["자소서 입력", "분석 중", "키워드 확인", "피드백 확인"],
        "표정연습": ["준비", "녹화 중", "분석 중", "결과"],
    }

    def __init__(self):
        self.current_states: Dict[str, ProgressState] = {}

    def init_progress(self, page_name: str) -> ProgressState:
        """진행 상태 초기화"""
        steps = self.PAGE_STEPS.get(page_name, ["시작", "진행", "완료"])
        state = ProgressState(
            current_step=0,
            total_steps=len(steps),
            step_name=steps[0]
        )
        self.current_states[page_name] = state
        return state

    def update_progress(self, page_name: str, step: int) -> ProgressState:
        """진행 상태 업데이트"""
        steps = self.PAGE_STEPS.get(page_name, ["시작", "진행", "완료"])

        if step >= len(steps):
            step = len(steps) - 1
            is_complete = True
        else:
            is_complete = False

        state = ProgressState(
            current_step=step + 1,
            total_steps=len(steps),
            step_name=steps[step],
            is_complete=is_complete
        )
        self.current_states[page_name] = state
        return state

    def get_progress_html(self, state: ProgressState) -> str:
        """진행 바 HTML"""
        percent = state.percent
        color = "green" if state.is_complete else "blue"

        return f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>{state.step_name}</span>
                <span>{state.fraction_text}</span>
            </div>
            <div style="background: #e0e0e0; border-radius: 10px; height: 8px; overflow: hidden;">
                <div style="background: {color}; width: {percent}%; height: 100%; transition: width 0.3s;"></div>
            </div>
        </div>
        """

    def get_step_indicator_html(self, state: ProgressState, page_name: str) -> str:
        """단계 인디케이터 HTML"""
        steps = self.PAGE_STEPS.get(page_name, ["시작", "진행", "완료"])
        html_parts = []

        for i, step in enumerate(steps):
            if i + 1 < state.current_step:
                status = "completed"
                icon = "check"
            elif i + 1 == state.current_step:
                status = "current"
                icon = str(i + 1)
            else:
                status = "pending"
                icon = str(i + 1)

            html_parts.append(f'<span class="step-{status}">{icon}. {step}</span>')

        return " → ".join(html_parts)


# ============================================================
# 32. 통일된 네비게이션
# ============================================================

@dataclass
class NavigationItem:
    """네비게이션 항목"""
    label: str
    page: str
    icon: str
    is_active: bool = False


@dataclass
class NavigationConfig:
    """네비게이션 설정"""
    show_back_button: bool
    back_destination: str
    show_home_button: bool
    breadcrumb: List[str]
    bottom_nav_visible: bool


class NavigationManager:
    """네비게이션 관리자"""

    # 페이지 계층 구조
    PAGE_HIERARCHY = {
        "Home": None,
        "모의면접": "Home",
        "롤플레잉": "Home",
        "영어면접": "Home",
        "토론면접": "Home",
        "자소서첨삭": "Home",
        "자소서템플릿": "Home",
        "표정연습": "Home",
        "실전연습": "모의면접",
    }

    # 하단 네비게이션 항목
    BOTTOM_NAV = [
        NavigationItem("홈", "Home", "home"),
        NavigationItem("면접", "모의면접", "mic"),
        NavigationItem("연습", "표정연습", "camera"),
        NavigationItem("자소서", "자소서첨삭", "document"),
        NavigationItem("진도", "진도관리", "chart"),
    ]

    def __init__(self):
        pass

    def get_config(self, current_page: str) -> NavigationConfig:
        """네비게이션 설정 조회"""
        parent = self.PAGE_HIERARCHY.get(current_page)

        # 브레드크럼 생성
        breadcrumb = [current_page]
        page = parent
        while page:
            breadcrumb.insert(0, page)
            page = self.PAGE_HIERARCHY.get(page)

        return NavigationConfig(
            show_back_button=parent is not None,
            back_destination=parent or "Home",
            show_home_button=current_page != "Home",
            breadcrumb=breadcrumb,
            bottom_nav_visible=True
        )

    def get_back_button_html(self, config: NavigationConfig) -> str:
        """뒤로가기 버튼 HTML"""
        if not config.show_back_button:
            return ""

        return f"""
        <div style="margin-bottom: 16px;">
            <button onclick="location.href='/{config.back_destination}'"
                    style="background: none; border: none; cursor: pointer;
                           display: flex; align-items: center; gap: 8px;
                           color: #666; font-size: 14px;">
                ← 돌아가기
            </button>
        </div>
        """

    def get_breadcrumb_html(self, config: NavigationConfig) -> str:
        """브레드크럼 HTML"""
        parts = []
        for i, page in enumerate(config.breadcrumb):
            if i == len(config.breadcrumb) - 1:
                parts.append(f"<strong>{page}</strong>")
            else:
                parts.append(f"<a href='/{page}'>{page}</a>")

        return " > ".join(parts)

    def get_bottom_nav_html(self) -> str:
        """하단 네비게이션 HTML"""
        items_html = ""
        for item in self.BOTTOM_NAV:
            active_class = "active" if item.is_active else ""
            items_html += f"""
            <a href="/{item.page}" class="bottom-nav-item {active_class}">
                <span class="icon">{item.icon}</span>
                <span class="label">{item.label}</span>
            </a>
            """

        return f"""
        <nav class="bottom-nav" style="
            position: fixed; bottom: 0; left: 0; right: 0;
            background: white; box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            display: flex; justify-content: space-around;
            padding: 8px 0; z-index: 100;">
            {items_html}
        </nav>
        <style>
            .bottom-nav-item {{
                display: flex; flex-direction: column; align-items: center;
                text-decoration: none; color: #666; font-size: 12px;
            }}
            .bottom-nav-item.active {{ color: #007bff; }}
            .bottom-nav-item .icon {{ font-size: 20px; }}
        </style>
        """


# ============================================================
# 33. 로딩 메시지
# ============================================================

@dataclass
class LoadingContent:
    """로딩 콘텐츠"""
    tip: str
    encouragement: str
    category: str


class LoadingMessageManager:
    """로딩 메시지 관리자"""

    # 팁 메시지
    TIPS = {
        "면접": [
            "면접관의 눈을 보며 대화하듯 답변하세요",
            "STAR 기법으로 경험을 구조화하세요",
            "답변 전 2초 정도 생각할 시간을 가져도 괜찮아요",
            "자신감 있는 첫인상이 중요해요",
            "구체적인 숫자와 사례가 설득력을 높여요",
        ],
        "영어": [
            "천천히, 또박또박 발음하세요",
            "완벽한 문법보다 자연스러운 소통이 중요해요",
            "모르는 단어가 있으면 쉬운 말로 바꿔 설명하세요",
            "발음이 어려운 단어는 미리 연습하세요",
        ],
        "롤플레이": [
            "승객의 감정에 먼저 공감하세요",
            "문제 해결과 함께 대안을 제시하세요",
            "항상 미소와 친절한 어투를 유지하세요",
            "불만 승객에게는 사과부터 시작하세요",
        ],
        "자소서": [
            "항공사의 인재상 키워드를 자연스럽게 녹여보세요",
            "구체적인 경험과 배운 점을 연결하세요",
            "지원동기와 미래 포부를 연결하세요",
            "너무 일반적인 표현은 피하세요",
        ],
        "일반": [
            "꾸준한 연습이 합격의 열쇠예요",
            "오늘 하루 연습이 미래를 바꿔요",
            "실수는 배움의 기회예요",
            "당신은 이미 충분히 노력하고 있어요",
        ],
    }

    # 격려 메시지
    ENCOURAGEMENTS = [
        "잘하고 있어요! 조금만 기다려주세요",
        "곧 결과가 나와요! 수고했어요",
        "AI가 열심히 분석하고 있어요",
        "거의 다 됐어요! 조금만요",
        "좋은 결과가 기다리고 있을 거예요",
    ]

    def __init__(self):
        pass

    def get_loading_content(self, category: str = "일반") -> LoadingContent:
        """로딩 콘텐츠 조회"""
        tips = self.TIPS.get(category, self.TIPS["일반"])
        tip = random.choice(tips)
        encouragement = random.choice(self.ENCOURAGEMENTS)

        return LoadingContent(
            tip=tip,
            encouragement=encouragement,
            category=category
        )

    def get_loading_html(self, content: LoadingContent, progress: int = None) -> str:
        """로딩 화면 HTML"""
        progress_bar = ""
        if progress is not None:
            progress_bar = f"""
            <div style="width: 200px; background: #e0e0e0; border-radius: 10px; height: 8px; margin: 16px 0;">
                <div style="width: {progress}%; background: #007bff; height: 100%; border-radius: 10px;
                            transition: width 0.3s;"></div>
            </div>
            """

        return f"""
        <div style="text-align: center; padding: 40px;">
            <div class="spinner" style="
                width: 50px; height: 50px; border: 4px solid #f3f3f3;
                border-top: 4px solid #007bff; border-radius: 50%;
                animation: spin 1s linear infinite; margin: 0 auto;">
            </div>
            {progress_bar}
            <p style="color: #666; margin-top: 16px;">{content.encouragement}</p>
            <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin-top: 24px;">
                <p style="color: #888; font-size: 14px;">TIP</p>
                <p style="color: #333;">{content.tip}</p>
            </div>
        </div>
        <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
        """

    def get_tips_by_category(self, category: str) -> List[str]:
        """카테고리별 팁 목록"""
        return self.TIPS.get(category, self.TIPS["일반"])


# ============================================================
# 편의 함수들
# ============================================================

_term_standardizer = TermStandardizer()
_progress_manager = ProgressBarManager()
_navigation_manager = NavigationManager()
_loading_manager = LoadingMessageManager()


def get_standard_term(term_id: str) -> str:
    """표준 용어 조회"""
    return _term_standardizer.get_term(term_id)


def standardize_term(text: str) -> str:
    """용어 표준화"""
    return _term_standardizer.standardize(text)


def get_all_standard_terms() -> Dict[str, List[Dict]]:
    """모든 표준 용어"""
    return _term_standardizer.get_term_reference()


def init_progress(page_name: str) -> ProgressState:
    """진행 상태 초기화"""
    return _progress_manager.init_progress(page_name)


def update_progress(page_name: str, step: int) -> ProgressState:
    """진행 상태 업데이트"""
    return _progress_manager.update_progress(page_name, step)


def get_progress_html(state: ProgressState) -> str:
    """진행 바 HTML"""
    return _progress_manager.get_progress_html(state)


def get_navigation_config(page_name: str) -> NavigationConfig:
    """네비게이션 설정"""
    return _navigation_manager.get_config(page_name)


def get_back_button_html(page_name: str) -> str:
    """뒤로가기 버튼 HTML"""
    config = _navigation_manager.get_config(page_name)
    return _navigation_manager.get_back_button_html(config)


def get_breadcrumb_html(page_name: str) -> str:
    """브레드크럼 HTML"""
    config = _navigation_manager.get_config(page_name)
    return _navigation_manager.get_breadcrumb_html(config)


def get_loading_content(category: str = "일반") -> LoadingContent:
    """로딩 콘텐츠"""
    return _loading_manager.get_loading_content(category)


def get_loading_html(category: str = "일반", progress: int = None) -> str:
    """로딩 화면 HTML"""
    content = _loading_manager.get_loading_content(category)
    return _loading_manager.get_loading_html(content, progress)
