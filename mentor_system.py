"""
FlyReady Lab - 멘토 매칭 시스템
현직 승무원/합격자와 예비 승무원 연결
"""

import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import hashlib
import random


class MentorStatus(Enum):
    """멘토 상태"""
    PENDING = "pending"           # 승인 대기
    ACTIVE = "active"             # 활동중
    INACTIVE = "inactive"         # 휴면
    SUSPENDED = "suspended"       # 정지


class MentorType(Enum):
    """멘토 유형"""
    CURRENT_CREW = "current_crew"         # 현직 승무원
    FORMER_CREW = "former_crew"           # 전직 승무원
    RECENT_PASS = "recent_pass"           # 최근 합격자
    INSTRUCTOR = "instructor"             # 학원 강사
    GROUND_STAFF = "ground_staff"         # 지상직


class SessionType(Enum):
    """멘토링 세션 유형"""
    VIDEO_CALL = "video_call"         # 화상 상담
    CHAT = "chat"                     # 채팅 상담
    DOCUMENT_REVIEW = "document_review"  # 서류 첨삭
    MOCK_INTERVIEW = "mock_interview"    # 모의 면접
    CAREER_CONSULT = "career_consult"    # 커리어 상담


class SessionStatus(Enum):
    """세션 상태"""
    PENDING = "pending"           # 예약 대기
    CONFIRMED = "confirmed"       # 확정
    COMPLETED = "completed"       # 완료
    CANCELLED = "cancelled"       # 취소
    NO_SHOW = "no_show"           # 노쇼


@dataclass
class MentorProfile:
    """멘토 프로필"""
    id: str
    user_id: str
    name: str
    mentor_type: str
    status: str = MentorStatus.PENDING.value

    # 경력 정보
    airlines: List[str] = field(default_factory=list)      # 근무 항공사
    current_airline: Optional[str] = None                   # 현 소속
    position: Optional[str] = None                          # 직급
    years_experience: int = 0                               # 경력 연수
    hire_year: Optional[int] = None                         # 입사년도

    # 전문 분야
    specialties: List[str] = field(default_factory=list)   # 전문 분야
    languages: List[str] = field(default_factory=list)     # 가능 언어
    session_types: List[str] = field(default_factory=list) # 제공 세션 유형

    # 프로필 정보
    bio: str = ""                                           # 자기소개
    profile_image: Optional[str] = None                     # 프로필 이미지
    verified: bool = False                                  # 인증 여부

    # 활동 정보
    rating: float = 0.0                                     # 평균 평점
    total_sessions: int = 0                                 # 총 세션 수
    total_reviews: int = 0                                  # 리뷰 수

    # 요금
    hourly_rate: int = 0                                    # 시간당 요금 (원)
    discount_rate: int = 0                                  # 할인율 (%)

    # 스케줄
    available_days: List[str] = field(default_factory=list)  # 가능 요일
    available_times: List[str] = field(default_factory=list) # 가능 시간대

    created_at: str = ""
    updated_at: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class MentoringSession:
    """멘토링 세션"""
    id: str
    mentor_id: str
    mentee_id: str
    session_type: str
    status: str = SessionStatus.PENDING.value

    # 일정
    scheduled_date: str = ""          # 예약 날짜
    scheduled_time: str = ""          # 예약 시간
    duration_minutes: int = 60        # 세션 시간 (분)

    # 상세 정보
    topic: str = ""                   # 상담 주제
    mentee_questions: List[str] = field(default_factory=list)  # 사전 질문
    mentor_notes: str = ""            # 멘토 메모
    meeting_link: Optional[str] = None  # 화상회의 링크

    # 결제
    price: int = 0                    # 결제 금액
    payment_id: Optional[str] = None  # 결제 ID
    paid: bool = False

    # 리뷰
    rating: Optional[float] = None    # 평점 (1-5)
    review: Optional[str] = None      # 리뷰 내용

    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class MatchingCriteria:
    """매칭 기준"""
    mentee_id: str
    target_airlines: List[str] = field(default_factory=list)  # 희망 항공사
    session_type: Optional[str] = None                         # 원하는 세션 유형
    budget_max: Optional[int] = None                           # 최대 예산
    preferred_language: str = "ko"                             # 선호 언어
    specialties_needed: List[str] = field(default_factory=list)  # 필요 분야


class MentorRepository:
    """멘토 데이터 저장소"""

    def __init__(self, data_dir: str = "data/mentors"):
        self.data_dir = data_dir
        self.mentors_file = os.path.join(data_dir, "mentors.json")
        self.sessions_file = os.path.join(data_dir, "sessions.json")
        os.makedirs(data_dir, exist_ok=True)

        # 샘플 데이터 초기화
        if not os.path.exists(self.mentors_file):
            self._init_sample_mentors()

    def _init_sample_mentors(self):
        """샘플 멘토 데이터"""
        sample_mentors = [
            MentorProfile(
                id="mentor_001",
                user_id="user_m001",
                name="김수현",
                mentor_type=MentorType.CURRENT_CREW.value,
                status=MentorStatus.ACTIVE.value,
                airlines=["KE"],
                current_airline="KE",
                position="부사무장",
                years_experience=8,
                hire_year=2016,
                specialties=["영어면접", "자기소개", "이미지메이킹"],
                languages=["ko", "en", "jp"],
                session_types=[SessionType.VIDEO_CALL.value, SessionType.MOCK_INTERVIEW.value],
                bio="대한항공 8년차 부사무장입니다. 면접 준비의 A to Z를 함께 하겠습니다.",
                verified=True,
                rating=4.9,
                total_sessions=156,
                total_reviews=142,
                hourly_rate=50000,
                available_days=["토", "일"],
                available_times=["10:00", "11:00", "14:00", "15:00"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            MentorProfile(
                id="mentor_002",
                user_id="user_m002",
                name="이지원",
                mentor_type=MentorType.RECENT_PASS.value,
                status=MentorStatus.ACTIVE.value,
                airlines=["OZ"],
                current_airline="OZ",
                position="승무원",
                years_experience=1,
                hire_year=2023,
                specialties=["자소서첨삭", "지원동기", "최신면접동향"],
                languages=["ko", "en", "zh"],
                session_types=[SessionType.DOCUMENT_REVIEW.value, SessionType.CHAT.value],
                bio="2023년 아시아나 합격! 최신 면접 경험을 공유합니다.",
                verified=True,
                rating=4.8,
                total_sessions=45,
                total_reviews=38,
                hourly_rate=30000,
                available_days=["월", "화", "수", "목", "금"],
                available_times=["20:00", "21:00"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            MentorProfile(
                id="mentor_003",
                user_id="user_m003",
                name="박서연",
                mentor_type=MentorType.CURRENT_CREW.value,
                status=MentorStatus.ACTIVE.value,
                airlines=["EK", "SQ"],
                current_airline="EK",
                position="Senior Cabin Crew",
                years_experience=6,
                hire_year=2018,
                specialties=["외항사면접", "영어스피킹", "오픈데이"],
                languages=["ko", "en"],
                session_types=[SessionType.VIDEO_CALL.value, SessionType.MOCK_INTERVIEW.value, SessionType.CAREER_CONSULT.value],
                bio="싱가포르항공 3년, 에미레이트 3년 경력. 외항사 합격 전략을 알려드립니다.",
                verified=True,
                rating=4.95,
                total_sessions=203,
                total_reviews=189,
                hourly_rate=70000,
                available_days=["토", "일"],
                available_times=["09:00", "10:00", "16:00", "17:00"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            MentorProfile(
                id="mentor_004",
                user_id="user_m004",
                name="정하늘",
                mentor_type=MentorType.INSTRUCTOR.value,
                status=MentorStatus.ACTIVE.value,
                airlines=["KE", "OZ", "7C"],
                position="수석강사",
                years_experience=12,
                specialties=["종합면접", "상황대처", "그룹토론"],
                languages=["ko", "en"],
                session_types=[SessionType.VIDEO_CALL.value, SessionType.MOCK_INTERVIEW.value, SessionType.DOCUMENT_REVIEW.value],
                bio="12년 경력 승무원 전문 강사. 1,000명 이상 합격 배출.",
                verified=True,
                rating=4.85,
                total_sessions=520,
                total_reviews=480,
                hourly_rate=80000,
                available_days=["월", "화", "수", "목", "금", "토"],
                available_times=["10:00", "11:00", "14:00", "15:00", "16:00"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
        ]

        self.save_all_mentors([m.to_dict() for m in sample_mentors])

    def save_all_mentors(self, mentors: List[Dict]):
        """전체 멘토 저장"""
        with open(self.mentors_file, 'w', encoding='utf-8') as f:
            json.dump(mentors, f, ensure_ascii=False, indent=2)

    def load_all_mentors(self) -> List[Dict]:
        """전체 멘토 로드"""
        if not os.path.exists(self.mentors_file):
            return []
        try:
            with open(self.mentors_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

    def get_mentor_by_id(self, mentor_id: str) -> Optional[MentorProfile]:
        """멘토 조회"""
        mentors = self.load_all_mentors()
        for m in mentors:
            if m.get('id') == mentor_id:
                return MentorProfile.from_dict(m)
        return None

    def save_mentor(self, mentor: MentorProfile):
        """멘토 저장/업데이트"""
        mentors = self.load_all_mentors()
        mentor.updated_at = datetime.now().isoformat()

        # 기존 멘토 업데이트 또는 새로 추가
        found = False
        for i, m in enumerate(mentors):
            if m.get('id') == mentor.id:
                mentors[i] = mentor.to_dict()
                found = True
                break

        if not found:
            if not mentor.created_at:
                mentor.created_at = datetime.now().isoformat()
            mentors.append(mentor.to_dict())

        self.save_all_mentors(mentors)

    def search_mentors(self, query: str = "",
                      airline: Optional[str] = None,
                      mentor_type: Optional[str] = None,
                      session_type: Optional[str] = None,
                      max_rate: Optional[int] = None) -> List[MentorProfile]:
        """멘토 검색"""
        mentors = self.load_all_mentors()
        results = []

        for m in mentors:
            if m.get('status') != MentorStatus.ACTIVE.value:
                continue

            # 검색어 필터
            if query:
                searchable = f"{m.get('name', '')} {m.get('bio', '')} {' '.join(m.get('specialties', []))}".lower()
                if query.lower() not in searchable:
                    continue

            # 항공사 필터
            if airline and airline not in m.get('airlines', []):
                continue

            # 멘토 유형 필터
            if mentor_type and m.get('mentor_type') != mentor_type:
                continue

            # 세션 유형 필터
            if session_type and session_type not in m.get('session_types', []):
                continue

            # 요금 필터
            if max_rate and m.get('hourly_rate', 0) > max_rate:
                continue

            results.append(MentorProfile.from_dict(m))

        # 평점순 정렬
        results.sort(key=lambda x: (x.rating, x.total_sessions), reverse=True)

        return results

    # 세션 관련 메서드
    def save_session(self, session: MentoringSession):
        """세션 저장"""
        sessions = self.load_all_sessions()
        session.updated_at = datetime.now().isoformat()

        found = False
        for i, s in enumerate(sessions):
            if s.get('id') == session.id:
                sessions[i] = session.to_dict()
                found = True
                break

        if not found:
            if not session.created_at:
                session.created_at = datetime.now().isoformat()
            sessions.append(session.to_dict())

        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)

    def load_all_sessions(self) -> List[Dict]:
        """전체 세션 로드"""
        if not os.path.exists(self.sessions_file):
            return []
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

    def get_mentor_sessions(self, mentor_id: str, status: Optional[str] = None) -> List[MentoringSession]:
        """멘토의 세션 조회"""
        sessions = self.load_all_sessions()
        results = []

        for s in sessions:
            if s.get('mentor_id') == mentor_id:
                if status is None or s.get('status') == status:
                    results.append(MentoringSession.from_dict(s))

        return results

    def get_mentee_sessions(self, mentee_id: str, status: Optional[str] = None) -> List[MentoringSession]:
        """멘티의 세션 조회"""
        sessions = self.load_all_sessions()
        results = []

        for s in sessions:
            if s.get('mentee_id') == mentee_id:
                if status is None or s.get('status') == status:
                    results.append(MentoringSession.from_dict(s))

        return results


class MentorMatchingEngine:
    """멘토 매칭 엔진"""

    # 항공사 코드 -> 이름
    AIRLINE_NAMES = {
        "KE": "대한항공",
        "OZ": "아시아나항공",
        "7C": "제주항공",
        "LJ": "진에어",
        "TW": "티웨이항공",
        "BX": "에어부산",
        "RS": "에어서울",
        "EK": "에미레이트항공",
        "SQ": "싱가포르항공",
        "CX": "캐세이퍼시픽",
        "QR": "카타르항공",
        "EY": "에티하드항공",
    }

    # 멘토 유형 한글
    MENTOR_TYPE_NAMES = {
        MentorType.CURRENT_CREW.value: "현직 승무원",
        MentorType.FORMER_CREW.value: "전직 승무원",
        MentorType.RECENT_PASS.value: "최근 합격자",
        MentorType.INSTRUCTOR.value: "전문 강사",
        MentorType.GROUND_STAFF.value: "지상직",
    }

    # 세션 유형 한글
    SESSION_TYPE_NAMES = {
        SessionType.VIDEO_CALL.value: "화상 상담",
        SessionType.CHAT.value: "채팅 상담",
        SessionType.DOCUMENT_REVIEW.value: "서류 첨삭",
        SessionType.MOCK_INTERVIEW.value: "모의 면접",
        SessionType.CAREER_CONSULT.value: "커리어 상담",
    }

    def __init__(self, data_dir: str = "data/mentors"):
        self.repo = MentorRepository(data_dir)

    def calculate_match_score(self, mentor: MentorProfile, criteria: MatchingCriteria) -> float:
        """멘토-멘티 매칭 점수 계산"""
        score = 0.0

        # 1. 항공사 매칭 (40점)
        if criteria.target_airlines:
            matched_airlines = set(mentor.airlines) & set(criteria.target_airlines)
            if matched_airlines:
                score += 40 * (len(matched_airlines) / len(criteria.target_airlines))

            # 현 소속이 타겟 항공사면 보너스
            if mentor.current_airline in criteria.target_airlines:
                score += 10

        # 2. 세션 유형 매칭 (20점)
        if criteria.session_type:
            if criteria.session_type in mentor.session_types:
                score += 20

        # 3. 전문 분야 매칭 (20점)
        if criteria.specialties_needed:
            matched_specs = set(mentor.specialties) & set(criteria.specialties_needed)
            if matched_specs:
                score += 20 * (len(matched_specs) / len(criteria.specialties_needed))

        # 4. 평점 가중치 (10점)
        score += mentor.rating * 2

        # 5. 경험 가중치 (10점)
        experience_score = min(10, mentor.total_sessions / 50 * 10)
        score += experience_score

        # 6. 예산 적합성 (감점 요소)
        if criteria.budget_max and mentor.hourly_rate > criteria.budget_max:
            score *= 0.5  # 예산 초과시 50% 감점

        # 7. 언어 매칭 (보너스)
        if criteria.preferred_language in mentor.languages:
            score += 5

        return min(100, score)

    def find_matches(self, criteria: MatchingCriteria, limit: int = 5) -> List[Tuple[MentorProfile, float]]:
        """매칭 멘토 찾기"""
        all_mentors = self.repo.search_mentors()

        matches = []
        for mentor in all_mentors:
            score = self.calculate_match_score(mentor, criteria)
            if score > 0:
                matches.append((mentor, score))

        # 점수순 정렬
        matches.sort(key=lambda x: x[1], reverse=True)

        return matches[:limit]

    def get_recommended_mentors(self, mentee_id: str, limit: int = 3) -> List[MentorProfile]:
        """추천 멘토 (간단 버전)"""
        # 기본 추천: 평점 높고 활동 많은 멘토
        mentors = self.repo.search_mentors()
        return mentors[:limit]


class MentorBookingService:
    """멘토링 예약 서비스"""

    def __init__(self, data_dir: str = "data/mentors"):
        self.repo = MentorRepository(data_dir)

    def generate_session_id(self) -> str:
        """세션 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(str(random.random()).encode()).hexdigest()[:6]
        return f"session_{timestamp}_{random_suffix}"

    def get_available_slots(self, mentor_id: str, date: str) -> List[str]:
        """멘토의 가용 시간대 조회"""
        mentor = self.repo.get_mentor_by_id(mentor_id)
        if not mentor:
            return []

        # 해당 날짜의 요일 확인
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            weekday = ["월", "화", "수", "목", "금", "토", "일"][dt.weekday()]
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

        if weekday not in mentor.available_days:
            return []

        # 이미 예약된 시간 제외
        existing_sessions = self.repo.get_mentor_sessions(mentor_id)
        booked_times = {
            s.scheduled_time for s in existing_sessions
            if s.scheduled_date == date and s.status in [SessionStatus.PENDING.value, SessionStatus.CONFIRMED.value]
        }

        available = [t for t in mentor.available_times if t not in booked_times]

        return available

    def create_booking(self, mentor_id: str, mentee_id: str,
                      session_type: str, date: str, time: str,
                      topic: str = "", questions: List[str] = None) -> Optional[MentoringSession]:
        """예약 생성"""
        mentor = self.repo.get_mentor_by_id(mentor_id)
        if not mentor:
            return None

        # 가용 시간 확인
        available = self.get_available_slots(mentor_id, date)
        if time not in available:
            return None

        session = MentoringSession(
            id=self.generate_session_id(),
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            session_type=session_type,
            status=SessionStatus.PENDING.value,
            scheduled_date=date,
            scheduled_time=time,
            duration_minutes=60,
            topic=topic,
            mentee_questions=questions or [],
            price=mentor.hourly_rate,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self.repo.save_session(session)

        return session

    def confirm_booking(self, session_id: str, payment_id: str) -> bool:
        """예약 확정 (결제 완료 후)"""
        sessions = self.repo.load_all_sessions()

        for i, s in enumerate(sessions):
            if s.get('id') == session_id:
                session = MentoringSession.from_dict(s)
                session.status = SessionStatus.CONFIRMED.value
                session.payment_id = payment_id
                session.paid = True
                session.meeting_link = self._generate_meeting_link(session_id)
                self.repo.save_session(session)
                return True

        return False

    def _generate_meeting_link(self, session_id: str) -> str:
        """화상회의 링크 생성 (placeholder)"""
        # 실제로는 Zoom, Google Meet API 연동
        return f"https://meet.flyready.kr/{session_id}"

    def cancel_booking(self, session_id: str, cancelled_by: str) -> bool:
        """예약 취소"""
        sessions = self.repo.load_all_sessions()

        for s in sessions:
            if s.get('id') == session_id:
                session = MentoringSession.from_dict(s)

                # 24시간 전까지만 취소 가능 체크 (실제 구현시)
                session.status = SessionStatus.CANCELLED.value
                self.repo.save_session(session)
                return True

        return False

    def complete_session(self, session_id: str) -> bool:
        """세션 완료 처리"""
        sessions = self.repo.load_all_sessions()

        for s in sessions:
            if s.get('id') == session_id:
                session = MentoringSession.from_dict(s)
                session.status = SessionStatus.COMPLETED.value
                session.completed_at = datetime.now().isoformat()
                self.repo.save_session(session)
                return True

        return False

    def submit_review(self, session_id: str, rating: float, review: str) -> bool:
        """리뷰 제출"""
        sessions = self.repo.load_all_sessions()

        for s in sessions:
            if s.get('id') == session_id:
                session = MentoringSession.from_dict(s)

                if session.status != SessionStatus.COMPLETED.value:
                    return False

                session.rating = rating
                session.review = review
                self.repo.save_session(session)

                # 멘토 평점 업데이트
                self._update_mentor_rating(session.mentor_id)

                return True

        return False

    def _update_mentor_rating(self, mentor_id: str):
        """멘토 평점 업데이트"""
        mentor = self.repo.get_mentor_by_id(mentor_id)
        if not mentor:
            return

        sessions = self.repo.get_mentor_sessions(mentor_id, status=SessionStatus.COMPLETED.value)
        ratings = [s.rating for s in sessions if s.rating is not None]

        if ratings:
            mentor.rating = round(sum(ratings) / len(ratings), 2)
            mentor.total_reviews = len(ratings)
            mentor.total_sessions = len(sessions)
            self.repo.save_mentor(mentor)


class MentorApplicationService:
    """멘토 지원 서비스"""

    def __init__(self, data_dir: str = "data/mentors"):
        self.repo = MentorRepository(data_dir)

    def generate_mentor_id(self) -> str:
        """멘토 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(str(random.random()).encode()).hexdigest()[:4]
        return f"mentor_{timestamp}_{random_suffix}"

    def apply_as_mentor(self, user_id: str, profile_data: Dict) -> MentorProfile:
        """멘토 지원"""
        mentor = MentorProfile(
            id=self.generate_mentor_id(),
            user_id=user_id,
            name=profile_data.get('name', ''),
            mentor_type=profile_data.get('mentor_type', MentorType.RECENT_PASS.value),
            status=MentorStatus.PENDING.value,
            airlines=profile_data.get('airlines', []),
            current_airline=profile_data.get('current_airline'),
            position=profile_data.get('position'),
            years_experience=profile_data.get('years_experience', 0),
            hire_year=profile_data.get('hire_year'),
            specialties=profile_data.get('specialties', []),
            languages=profile_data.get('languages', ['ko']),
            session_types=profile_data.get('session_types', []),
            bio=profile_data.get('bio', ''),
            hourly_rate=profile_data.get('hourly_rate', 30000),
            available_days=profile_data.get('available_days', []),
            available_times=profile_data.get('available_times', []),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self.repo.save_mentor(mentor)

        return mentor

    def approve_mentor(self, mentor_id: str) -> bool:
        """멘토 승인"""
        mentor = self.repo.get_mentor_by_id(mentor_id)
        if not mentor:
            return False

        mentor.status = MentorStatus.ACTIVE.value
        mentor.verified = True
        self.repo.save_mentor(mentor)

        return True

    def reject_mentor(self, mentor_id: str, reason: str = "") -> bool:
        """멘토 반려"""
        mentor = self.repo.get_mentor_by_id(mentor_id)
        if not mentor:
            return False

        mentor.status = MentorStatus.SUSPENDED.value
        self.repo.save_mentor(mentor)

        return True


# Streamlit 통합용 함수들
def render_mentor_list_page():
    """멘토 목록 페이지"""
    import streamlit as st

    st.title("멘토 찾기")

    engine = MentorMatchingEngine()

    # 필터
    col1, col2, col3 = st.columns(3)

    with col1:
        airline_filter = st.selectbox(
            "항공사",
            ["전체"] + list(engine.AIRLINE_NAMES.keys()),
            format_func=lambda x: "전체" if x == "전체" else engine.AIRLINE_NAMES.get(x, x)
        )

    with col2:
        type_filter = st.selectbox(
            "멘토 유형",
            ["전체"] + list(engine.MENTOR_TYPE_NAMES.keys()),
            format_func=lambda x: "전체" if x == "전체" else engine.MENTOR_TYPE_NAMES.get(x, x)
        )

    with col3:
        session_filter = st.selectbox(
            "상담 유형",
            ["전체"] + list(engine.SESSION_TYPE_NAMES.keys()),
            format_func=lambda x: "전체" if x == "전체" else engine.SESSION_TYPE_NAMES.get(x, x)
        )

    # 멘토 목록
    mentors = engine.repo.search_mentors(
        airline=None if airline_filter == "전체" else airline_filter,
        mentor_type=None if type_filter == "전체" else type_filter,
        session_type=None if session_filter == "전체" else session_filter
    )

    if not mentors:
        st.info("조건에 맞는 멘토가 없습니다.")
        return

    for mentor in mentors:
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                st.image("https://via.placeholder.com/100", width=100)

            with col2:
                st.markdown(f"### {mentor.name}")

                type_name = engine.MENTOR_TYPE_NAMES.get(mentor.mentor_type, mentor.mentor_type)
                airlines = [engine.AIRLINE_NAMES.get(a, a) for a in mentor.airlines]

                st.markdown(f"**{type_name}** | {', '.join(airlines)}")
                st.markdown(f"경력 {mentor.years_experience}년 | ⭐ {mentor.rating} ({mentor.total_reviews}개 리뷰)")
                st.markdown(f"전문: {', '.join(mentor.specialties[:3])}")
                st.caption(mentor.bio[:100] + "..." if len(mentor.bio) > 100 else mentor.bio)

            with col3:
                st.markdown(f"### ₩{mentor.hourly_rate:,}")
                st.caption("/시간")
                if st.button("상담 신청", key=f"book_{mentor.id}"):
                    st.session_state['selected_mentor'] = mentor.id
                    st.rerun()

            st.divider()


def render_mentor_profile_page(mentor_id: str):
    """멘토 프로필 상세 페이지"""
    import streamlit as st

    engine = MentorMatchingEngine()
    mentor = engine.repo.get_mentor_by_id(mentor_id)

    if not mentor:
        st.error("멘토를 찾을 수 없습니다.")
        return

    st.title(f"{mentor.name} 멘토")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.image("https://via.placeholder.com/200", width=200)
        if mentor.verified:
            st.success("✓ 인증된 멘토")

    with col2:
        type_name = engine.MENTOR_TYPE_NAMES.get(mentor.mentor_type, mentor.mentor_type)
        airlines = [engine.AIRLINE_NAMES.get(a, a) for a in mentor.airlines]

        st.markdown(f"**{type_name}** | {mentor.position or ''}")
        st.markdown(f"**소속**: {', '.join(airlines)}")
        st.markdown(f"**경력**: {mentor.years_experience}년 (입사 {mentor.hire_year}년)")
        st.markdown(f"**평점**: ⭐ {mentor.rating} ({mentor.total_reviews}개 리뷰)")
        st.markdown(f"**총 상담**: {mentor.total_sessions}회")

    st.markdown("---")
    st.subheader("소개")
    st.write(mentor.bio)

    st.subheader("전문 분야")
    st.write(", ".join(mentor.specialties))

    st.subheader("제공 서비스")
    for st_type in mentor.session_types:
        st.write(f"- {engine.SESSION_TYPE_NAMES.get(st_type, st_type)}")

    st.subheader("상담 가능 시간")
    st.write(f"**요일**: {', '.join(mentor.available_days)}")
    st.write(f"**시간**: {', '.join(mentor.available_times)}")

    st.markdown("---")
    st.subheader("상담 예약")
    st.markdown(f"### ₩{mentor.hourly_rate:,}/시간")

    if st.button("예약하기", type="primary"):
        st.session_state['booking_mentor'] = mentor_id


def render_booking_page(mentor_id: str):
    """예약 페이지"""
    import streamlit as st

    engine = MentorMatchingEngine()
    booking_service = MentorBookingService()

    mentor = engine.repo.get_mentor_by_id(mentor_id)
    if not mentor:
        st.error("멘토를 찾을 수 없습니다.")
        return

    st.title(f"{mentor.name} 멘토 상담 예약")

    # 세션 유형 선택
    session_type = st.selectbox(
        "상담 유형",
        mentor.session_types,
        format_func=lambda x: engine.SESSION_TYPE_NAMES.get(x, x)
    )

    # 날짜 선택
    min_date = datetime.now().date() + timedelta(days=1)
    max_date = datetime.now().date() + timedelta(days=30)
    selected_date = st.date_input("날짜 선택", min_value=min_date, max_value=max_date)

    # 시간 선택
    date_str = selected_date.strftime("%Y-%m-%d")
    available_times = booking_service.get_available_slots(mentor_id, date_str)

    if available_times:
        selected_time = st.selectbox("시간 선택", available_times)
    else:
        st.warning("해당 날짜에 예약 가능한 시간이 없습니다.")
        return

    # 상담 주제
    topic = st.text_input("상담 주제")
    questions = st.text_area("사전 질문 (선택사항)")

    # 결제 금액
    st.markdown(f"### 결제 금액: ₩{mentor.hourly_rate:,}")

    if st.button("예약 및 결제", type="primary"):
        user_id = st.session_state.get("user_id", "guest")

        session = booking_service.create_booking(
            mentor_id=mentor_id,
            mentee_id=user_id,
            session_type=session_type,
            date=date_str,
            time=selected_time,
            topic=topic,
            questions=[q.strip() for q in questions.split('\n') if q.strip()]
        )

        if session:
            st.success("예약이 생성되었습니다! 결제 페이지로 이동합니다.")
            st.session_state['pending_session'] = session.id
        else:
            st.error("예약에 실패했습니다. 다시 시도해주세요.")


def render_my_mentoring_page():
    """내 멘토링 내역 페이지"""
    import streamlit as st

    st.title("내 멘토링")

    user_id = st.session_state.get("user_id", "guest")
    booking_service = MentorBookingService()
    engine = MentorMatchingEngine()

    sessions = booking_service.repo.get_mentee_sessions(user_id)

    if not sessions:
        st.info("예약된 멘토링이 없습니다.")
        return

    tab1, tab2, tab3 = st.tabs(["예정된 상담", "완료된 상담", "취소된 상담"])

    with tab1:
        upcoming = [s for s in sessions if s.status in [SessionStatus.PENDING.value, SessionStatus.CONFIRMED.value]]
        for session in upcoming:
            mentor = engine.repo.get_mentor_by_id(session.mentor_id)
            mentor_name = mentor.name if mentor else "알 수 없음"

            with st.expander(f"{mentor_name} 멘토 - {session.scheduled_date} {session.scheduled_time}"):
                st.markdown(f"**상담 유형**: {engine.SESSION_TYPE_NAMES.get(session.session_type, session.session_type)}")
                st.markdown(f"**주제**: {session.topic or '미정'}")
                st.markdown(f"**상태**: {session.status}")

                if session.meeting_link:
                    st.link_button("입장하기", session.meeting_link)

                if st.button("취소", key=f"cancel_{session.id}"):
                    booking_service.cancel_booking(session.id, user_id)
                    st.rerun()

    with tab2:
        completed = [s for s in sessions if s.status == SessionStatus.COMPLETED.value]
        for session in completed:
            mentor = engine.repo.get_mentor_by_id(session.mentor_id)
            mentor_name = mentor.name if mentor else "알 수 없음"

            with st.expander(f"{mentor_name} 멘토 - {session.scheduled_date}"):
                st.markdown(f"**주제**: {session.topic or '미정'}")

                if session.rating:
                    st.markdown(f"**내 평점**: {'⭐' * int(session.rating)}")
                    st.markdown(f"**리뷰**: {session.review}")
                else:
                    rating = st.slider("평점", 1, 5, 5, key=f"rate_{session.id}")
                    review = st.text_area("리뷰", key=f"review_{session.id}")

                    if st.button("리뷰 제출", key=f"submit_{session.id}"):
                        booking_service.submit_review(session.id, float(rating), review)
                        st.success("리뷰가 등록되었습니다!")
                        st.rerun()

    with tab3:
        cancelled = [s for s in sessions if s.status == SessionStatus.CANCELLED.value]
        for session in cancelled:
            mentor = engine.repo.get_mentor_by_id(session.mentor_id)
            mentor_name = mentor.name if mentor else "알 수 없음"
            st.write(f"- {mentor_name} 멘토 - {session.scheduled_date} (취소됨)")


if __name__ == "__main__":
    # 테스트
    print("=== 멘토 매칭 시스템 테스트 ===\n")

    engine = MentorMatchingEngine()
    booking = MentorBookingService()

    # 멘토 검색
    print("1. 활성 멘토 목록:")
    mentors = engine.repo.search_mentors()
    for m in mentors:
        print(f"   - {m.name} ({engine.MENTOR_TYPE_NAMES.get(m.mentor_type)})")
        print(f"     항공사: {[engine.AIRLINE_NAMES.get(a, a) for a in m.airlines]}")
        print(f"     평점: {m.rating} ({m.total_reviews}리뷰)")
        print(f"     요금: ₩{m.hourly_rate:,}/시간")

    # 매칭 테스트
    print("\n2. 대한항공 지원자를 위한 멘토 매칭:")
    criteria = MatchingCriteria(
        mentee_id="test_user",
        target_airlines=["KE"],
        session_type=SessionType.MOCK_INTERVIEW.value,
        specialties_needed=["자기소개", "영어면접"],
        budget_max=60000
    )

    matches = engine.find_matches(criteria, limit=3)
    for mentor, score in matches:
        print(f"   - {mentor.name}: 매칭 점수 {score:.1f}점")

    # 예약 테스트
    print("\n3. 예약 가능 시간 조회 (내일):")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    slots = booking.get_available_slots("mentor_001", tomorrow)
    print(f"   {tomorrow}: {slots}")
