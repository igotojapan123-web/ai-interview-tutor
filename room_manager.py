# room_manager.py
# FlyReady Lab 멀티플레이어 모의면접 방 관리 시스템

import json
import random
import string
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from logging_config import get_logger

# 로거 설정
logger = get_logger(__name__)

# 데이터 디렉토리 설정
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ROOMS_FILE = DATA_DIR / "rooms.json"
MESSAGES_FILE = DATA_DIR / "room_messages.json"

# 방 비활성 시간 제한 (24시간)
ROOM_INACTIVE_TIMEOUT = timedelta(hours=24)


class RoomType(str, Enum):
    """방 유형"""
    GROUP_INTERVIEW = "group_interview"
    DEBATE = "debate"
    STUDY_GROUP = "study_group"


class RoomStatus(str, Enum):
    """방 상태"""
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ParticipantStatus(str, Enum):
    """참가자 상태"""
    READY = "ready"
    NOT_READY = "not_ready"
    ANSWERING = "answering"
    WAITING = "waiting"


# 방 유형별 기본 설정 템플릿
ROOM_TEMPLATES: Dict[str, Dict[str, Any]] = {
    RoomType.GROUP_INTERVIEW: {
        "name": "그룹 면접",
        "description": "AI가 출제하는 질문에 순서대로 답변하는 그룹 면접입니다.",
        "turn_based": True,
        "ai_questions": True,
        "time_limit_per_answer": 120,  # 초 단위
        "max_questions": 5,
        "allow_feedback": True,
        "show_other_answers": True,
        "default_max_participants": 4,
    },
    RoomType.DEBATE: {
        "name": "토론",
        "description": "찬성/반대 팀으로 나뉘어 주제에 대해 토론합니다.",
        "topics_enabled": True,
        "pro_con_sides": True,
        "rebuttal_rounds": 2,
        "time_limit_per_turn": 180,  # 초 단위
        "opening_statement_time": 60,
        "closing_statement_time": 60,
        "default_max_participants": 6,
    },
    RoomType.STUDY_GROUP: {
        "name": "스터디 그룹",
        "description": "자유롭게 토론하고 자료를 공유하는 스터디 그룹입니다.",
        "free_discussion": True,
        "shared_resources": True,
        "voice_enabled": True,
        "screen_share_enabled": True,
        "note_sharing": True,
        "default_max_participants": 6,
    },
}


@dataclass
class Participant:
    """참가자 정보"""
    user_id: str
    user_name: str
    status: str = ParticipantStatus.NOT_READY
    joined_at: str = field(default_factory=lambda: datetime.now().isoformat())
    side: Optional[str] = None  # 토론용: "pro" 또는 "con"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Participant":
        return cls(**data)


@dataclass
class Answer:
    """답변 정보"""
    user_id: str
    user_name: str
    question_idx: int
    answer_text: str
    audio_data: Optional[str] = None  # base64 인코딩된 오디오
    submitted_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Answer":
        return cls(**data)


@dataclass
class Message:
    """채팅 메시지"""
    room_id: str
    user_id: str
    user_name: str
    message: str
    message_type: str = "chat"  # "chat", "system", "reaction"
    target_user_id: Optional[str] = None  # 리액션용
    reaction: Optional[str] = None  # 리액션 종류
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(**data)


@dataclass
class RoomState:
    """방 진행 상태"""
    current_question_idx: int = 0
    current_speaker_id: Optional[str] = None
    turn_order: List[str] = field(default_factory=list)
    current_turn_idx: int = 0
    round_number: int = 1
    phase: str = "waiting"  # waiting, questioning, answering, reviewing, completed

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoomState":
        return cls(**data)


@dataclass
class Room:
    """방 정보"""
    room_id: str
    room_name: str
    host_id: str
    room_type: str
    max_participants: int
    participants: List[Dict[str, Any]] = field(default_factory=list)
    status: str = RoomStatus.WAITING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    settings: Dict[str, Any] = field(default_factory=dict)
    questions: List[str] = field(default_factory=list)
    answers: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=lambda: RoomState().to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Room":
        return cls(**data)


class RoomManager:
    """방 관리 시스템"""

    def __init__(self):
        """초기화"""
        self._ensure_data_files()
        self._cleanup_old_rooms()
        logger.info("방 관리 시스템 초기화 완료")

    def _ensure_data_files(self) -> None:
        """데이터 파일 초기화"""
        if not ROOMS_FILE.exists():
            self._save_rooms({})
            logger.info(f"방 데이터 파일 생성: {ROOMS_FILE}")

        if not MESSAGES_FILE.exists():
            self._save_messages([])
            logger.info(f"메시지 데이터 파일 생성: {MESSAGES_FILE}")

    def _load_rooms(self) -> Dict[str, Dict[str, Any]]:
        """방 데이터 로드"""
        try:
            with open(ROOMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("방 데이터 로드 실패, 빈 데이터로 초기화")
            return {}

    def _save_rooms(self, rooms: Dict[str, Dict[str, Any]]) -> None:
        """방 데이터 저장"""
        with open(ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(rooms, f, ensure_ascii=False, indent=2)

    def _load_messages(self) -> List[Dict[str, Any]]:
        """메시지 데이터 로드"""
        try:
            with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("메시지 데이터 로드 실패, 빈 리스트로 초기화")
            return []

    def _save_messages(self, messages: List[Dict[str, Any]]) -> None:
        """메시지 데이터 저장"""
        with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def _generate_room_id(self) -> str:
        """고유한 6자리 방 코드 생성"""
        rooms = self._load_rooms()
        while True:
            room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if room_id not in rooms:
                return room_id

    def _update_last_activity(self, room_id: str) -> None:
        """방 마지막 활동 시간 업데이트"""
        rooms = self._load_rooms()
        if room_id in rooms:
            rooms[room_id]["last_activity"] = datetime.now().isoformat()
            self._save_rooms(rooms)

    def _cleanup_old_rooms(self) -> None:
        """24시간 이상 비활성 방 정리"""
        rooms = self._load_rooms()
        messages = self._load_messages()

        now = datetime.now()
        rooms_to_delete = []

        for room_id, room_data in rooms.items():
            last_activity = datetime.fromisoformat(room_data.get("last_activity", room_data["created_at"]))
            if now - last_activity > ROOM_INACTIVE_TIMEOUT:
                rooms_to_delete.append(room_id)

        if rooms_to_delete:
            for room_id in rooms_to_delete:
                del rooms[room_id]
                logger.info(f"비활성 방 삭제: {room_id}")

            # 삭제된 방의 메시지도 정리
            messages = [m for m in messages if m["room_id"] not in rooms_to_delete]

            self._save_rooms(rooms)
            self._save_messages(messages)
            logger.info(f"총 {len(rooms_to_delete)}개의 비활성 방 정리 완료")

    # ========== 방 생성 및 관리 ==========

    def create_room(
        self,
        host_id: str,
        room_name: str,
        room_type: str,
        max_participants: int = 4,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """새 방 생성

        Args:
            host_id: 호스트 사용자 ID
            room_name: 방 이름
            room_type: 방 유형 (group_interview, debate, study_group)
            max_participants: 최대 참가자 수 (2-6)
            settings: 추가 설정

        Returns:
            생성된 방 정보
        """
        # 유효성 검사
        if room_type not in [rt.value for rt in RoomType]:
            logger.error(f"잘못된 방 유형: {room_type}")
            raise ValueError(f"잘못된 방 유형입니다: {room_type}")

        if not 2 <= max_participants <= 6:
            logger.error(f"잘못된 최대 참가자 수: {max_participants}")
            raise ValueError("최대 참가자 수는 2-6명 사이여야 합니다.")

        # 기본 설정 적용
        template = ROOM_TEMPLATES.get(room_type, {}).copy()
        if settings:
            template.update(settings)

        room_id = self._generate_room_id()

        # 호스트를 첫 참가자로 추가
        host_participant = Participant(
            user_id=host_id,
            user_name=f"호스트_{host_id[:4]}",
            status=ParticipantStatus.READY
        )

        room = Room(
            room_id=room_id,
            room_name=room_name,
            host_id=host_id,
            room_type=room_type,
            max_participants=max_participants,
            participants=[host_participant.to_dict()],
            settings=template
        )

        rooms = self._load_rooms()
        rooms[room_id] = room.to_dict()
        self._save_rooms(rooms)

        logger.info(f"방 생성 완료: {room_id} ({room_name}), 호스트: {host_id}")
        return room.to_dict()

    def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """방 정보 조회

        Args:
            room_id: 방 ID

        Returns:
            방 정보 또는 None
        """
        rooms = self._load_rooms()
        room = rooms.get(room_id)

        if room:
            logger.debug(f"방 조회: {room_id}")
        else:
            logger.warning(f"존재하지 않는 방: {room_id}")

        return room

    def delete_room(self, room_id: str, user_id: str) -> bool:
        """방 삭제 (호스트만 가능)

        Args:
            room_id: 방 ID
            user_id: 요청 사용자 ID

        Returns:
            삭제 성공 여부
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.warning(f"삭제할 방이 존재하지 않음: {room_id}")
            return False

        room = rooms[room_id]
        if room["host_id"] != user_id:
            logger.warning(f"방 삭제 권한 없음: {user_id}는 호스트가 아님")
            raise PermissionError("호스트만 방을 삭제할 수 있습니다.")

        del rooms[room_id]
        self._save_rooms(rooms)

        # 관련 메시지도 삭제
        messages = self._load_messages()
        messages = [m for m in messages if m["room_id"] != room_id]
        self._save_messages(messages)

        logger.info(f"방 삭제 완료: {room_id}")
        return True

    def update_room_settings(
        self,
        room_id: str,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """방 설정 업데이트 (호스트만 가능)

        Args:
            room_id: 방 ID
            user_id: 요청 사용자 ID
            settings: 업데이트할 설정

        Returns:
            업데이트된 방 정보
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.error(f"방이 존재하지 않음: {room_id}")
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]
        if room["host_id"] != user_id:
            logger.warning(f"설정 변경 권한 없음: {user_id}는 호스트가 아님")
            raise PermissionError("호스트만 설정을 변경할 수 있습니다.")

        room["settings"].update(settings)
        room["last_activity"] = datetime.now().isoformat()
        self._save_rooms(rooms)

        logger.info(f"방 설정 업데이트: {room_id}")
        return room

    def list_available_rooms(
        self,
        room_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """참가 가능한 방 목록 조회

        Args:
            room_type: 필터링할 방 유형 (선택)

        Returns:
            참가 가능한 방 목록
        """
        rooms = self._load_rooms()
        available = []

        for room_id, room in rooms.items():
            # 대기 중인 방만
            if room["status"] != RoomStatus.WAITING:
                continue

            # 자리가 있는 방만
            if len(room["participants"]) >= room["max_participants"]:
                continue

            # 유형 필터
            if room_type and room["room_type"] != room_type:
                continue

            # 공개 정보만 포함
            available.append({
                "room_id": room["room_id"],
                "room_name": room["room_name"],
                "room_type": room["room_type"],
                "host_id": room["host_id"],
                "current_participants": len(room["participants"]),
                "max_participants": room["max_participants"],
                "created_at": room["created_at"],
            })

        logger.debug(f"참가 가능한 방 {len(available)}개 조회")
        return available

    # ========== 참가자 관리 ==========

    def join_room(
        self,
        room_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """방 참가

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            user_name: 사용자 이름

        Returns:
            업데이트된 방 정보
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.error(f"방이 존재하지 않음: {room_id}")
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]

        # 이미 참가한 경우
        for p in room["participants"]:
            if p["user_id"] == user_id:
                logger.info(f"이미 참가 중: {user_id} in {room_id}")
                return room

        # 인원 제한 확인
        if len(room["participants"]) >= room["max_participants"]:
            logger.warning(f"방이 가득 참: {room_id}")
            raise ValueError("방이 가득 찼습니다.")

        # 진행 중인 방 참가 불가
        if room["status"] != RoomStatus.WAITING:
            logger.warning(f"진행 중인 방 참가 시도: {room_id}")
            raise ValueError("이미 진행 중인 방에는 참가할 수 없습니다.")

        # 참가자 추가
        participant = Participant(
            user_id=user_id,
            user_name=user_name,
            status=ParticipantStatus.NOT_READY
        )
        room["participants"].append(participant.to_dict())
        room["last_activity"] = datetime.now().isoformat()

        self._save_rooms(rooms)

        # 시스템 메시지 전송
        self._add_system_message(room_id, f"{user_name}님이 입장했습니다.")

        logger.info(f"방 참가: {user_id} -> {room_id}")
        return room

    def leave_room(self, room_id: str, user_id: str) -> bool:
        """방 나가기

        Args:
            room_id: 방 ID
            user_id: 사용자 ID

        Returns:
            성공 여부
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.warning(f"방이 존재하지 않음: {room_id}")
            return False

        room = rooms[room_id]

        # 참가자 찾기
        participant = None
        for i, p in enumerate(room["participants"]):
            if p["user_id"] == user_id:
                participant = room["participants"].pop(i)
                break

        if not participant:
            logger.warning(f"참가자가 아님: {user_id} in {room_id}")
            return False

        user_name = participant.get("user_name", user_id)

        # 호스트가 나가면 방 삭제 또는 호스트 이전
        if room["host_id"] == user_id:
            if room["participants"]:
                # 첫 번째 참가자를 새 호스트로
                new_host = room["participants"][0]
                room["host_id"] = new_host["user_id"]
                logger.info(f"호스트 변경: {new_host['user_id']}")
                self._add_system_message(
                    room_id,
                    f"호스트가 나갔습니다. {new_host['user_name']}님이 새 호스트입니다."
                )
            else:
                # 참가자가 없으면 방 삭제
                del rooms[room_id]
                self._save_rooms(rooms)
                logger.info(f"빈 방 삭제: {room_id}")
                return True

        room["last_activity"] = datetime.now().isoformat()
        self._save_rooms(rooms)

        self._add_system_message(room_id, f"{user_name}님이 퇴장했습니다.")

        logger.info(f"방 퇴장: {user_id} from {room_id}")
        return True

    def kick_participant(
        self,
        room_id: str,
        host_id: str,
        target_user_id: str
    ) -> bool:
        """참가자 강퇴 (호스트만 가능)

        Args:
            room_id: 방 ID
            host_id: 호스트 사용자 ID
            target_user_id: 강퇴할 사용자 ID

        Returns:
            성공 여부
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.error(f"방이 존재하지 않음: {room_id}")
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]

        if room["host_id"] != host_id:
            logger.warning(f"강퇴 권한 없음: {host_id}는 호스트가 아님")
            raise PermissionError("호스트만 참가자를 강퇴할 수 있습니다.")

        if host_id == target_user_id:
            logger.warning("호스트 자신 강퇴 시도")
            raise ValueError("자기 자신을 강퇴할 수 없습니다.")

        # 참가자 찾기 및 제거
        for i, p in enumerate(room["participants"]):
            if p["user_id"] == target_user_id:
                kicked = room["participants"].pop(i)
                room["last_activity"] = datetime.now().isoformat()
                self._save_rooms(rooms)

                self._add_system_message(
                    room_id,
                    f"{kicked['user_name']}님이 강퇴되었습니다."
                )

                logger.info(f"참가자 강퇴: {target_user_id} from {room_id}")
                return True

        logger.warning(f"강퇴 대상이 참가자가 아님: {target_user_id}")
        return False

    def get_participants(self, room_id: str) -> List[Dict[str, Any]]:
        """방 참가자 목록 조회

        Args:
            room_id: 방 ID

        Returns:
            참가자 목록
        """
        room = self.get_room(room_id)
        if not room:
            return []
        return room["participants"]

    def update_participant_status(
        self,
        room_id: str,
        user_id: str,
        status: str
    ) -> Dict[str, Any]:
        """참가자 상태 업데이트

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            status: 새 상태 (ready, not_ready, answering, waiting)

        Returns:
            업데이트된 참가자 정보
        """
        if status not in [ps.value for ps in ParticipantStatus]:
            logger.error(f"잘못된 상태: {status}")
            raise ValueError(f"잘못된 상태입니다: {status}")

        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.error(f"방이 존재하지 않음: {room_id}")
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]

        for p in room["participants"]:
            if p["user_id"] == user_id:
                p["status"] = status
                room["last_activity"] = datetime.now().isoformat()
                self._save_rooms(rooms)

                logger.debug(f"참가자 상태 변경: {user_id} -> {status}")
                return p

        logger.warning(f"참가자가 아님: {user_id} in {room_id}")
        raise ValueError("방에 참가하지 않은 사용자입니다.")

    # ========== 방 상태 관리 ==========

    def start_session(self, room_id: str, host_id: str) -> Dict[str, Any]:
        """세션 시작 (호스트만 가능)

        Args:
            room_id: 방 ID
            host_id: 호스트 사용자 ID

        Returns:
            업데이트된 방 정보
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.error(f"방이 존재하지 않음: {room_id}")
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]

        if room["host_id"] != host_id:
            logger.warning(f"세션 시작 권한 없음: {host_id}는 호스트가 아님")
            raise PermissionError("호스트만 세션을 시작할 수 있습니다.")

        if room["status"] != RoomStatus.WAITING:
            logger.warning(f"이미 시작된 세션: {room_id}")
            raise ValueError("세션이 이미 시작되었거나 종료되었습니다.")

        # 최소 2명 필요
        if len(room["participants"]) < 2:
            logger.warning(f"참가자 부족: {room_id}")
            raise ValueError("세션 시작을 위해 최소 2명의 참가자가 필요합니다.")

        # 상태 업데이트
        room["status"] = RoomStatus.IN_PROGRESS

        # 순서 설정
        turn_order = [p["user_id"] for p in room["participants"]]
        random.shuffle(turn_order)

        room["state"] = {
            "current_question_idx": 0,
            "current_speaker_id": turn_order[0] if turn_order else None,
            "turn_order": turn_order,
            "current_turn_idx": 0,
            "round_number": 1,
            "phase": "questioning"
        }

        # 모든 참가자 상태를 대기로
        for p in room["participants"]:
            p["status"] = ParticipantStatus.WAITING

        # 첫 번째 발언자 상태 변경
        if turn_order:
            for p in room["participants"]:
                if p["user_id"] == turn_order[0]:
                    p["status"] = ParticipantStatus.ANSWERING
                    break

        room["last_activity"] = datetime.now().isoformat()
        self._save_rooms(rooms)

        self._add_system_message(room_id, "세션이 시작되었습니다!")

        logger.info(f"세션 시작: {room_id}")
        return room

    def end_session(self, room_id: str) -> Dict[str, Any]:
        """세션 종료

        Args:
            room_id: 방 ID

        Returns:
            업데이트된 방 정보
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            logger.error(f"방이 존재하지 않음: {room_id}")
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]
        room["status"] = RoomStatus.COMPLETED
        room["state"]["phase"] = "completed"
        room["last_activity"] = datetime.now().isoformat()

        self._save_rooms(rooms)

        self._add_system_message(room_id, "세션이 종료되었습니다. 수고하셨습니다!")

        logger.info(f"세션 종료: {room_id}")
        return room

    def get_room_state(self, room_id: str) -> Dict[str, Any]:
        """방 현재 상태 조회

        Args:
            room_id: 방 ID

        Returns:
            현재 상태 정보
        """
        room = self.get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        state = room.get("state", {})

        # 현재 질문 포함
        questions = room.get("questions", [])
        current_idx = state.get("current_question_idx", 0)
        current_question = questions[current_idx] if current_idx < len(questions) else None

        return {
            **state,
            "room_status": room["status"],
            "current_question": current_question,
            "total_questions": len(questions),
            "participants_count": len(room["participants"])
        }

    def set_current_speaker(self, room_id: str, user_id: str) -> Dict[str, Any]:
        """현재 발언자 설정

        Args:
            room_id: 방 ID
            user_id: 발언자 사용자 ID

        Returns:
            업데이트된 상태
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]

        # 참가자 확인
        is_participant = any(p["user_id"] == user_id for p in room["participants"])
        if not is_participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")

        # 이전 발언자 상태 변경
        old_speaker_id = room["state"].get("current_speaker_id")
        for p in room["participants"]:
            if p["user_id"] == old_speaker_id:
                p["status"] = ParticipantStatus.WAITING
            elif p["user_id"] == user_id:
                p["status"] = ParticipantStatus.ANSWERING

        room["state"]["current_speaker_id"] = user_id
        room["last_activity"] = datetime.now().isoformat()

        self._save_rooms(rooms)

        logger.debug(f"발언자 변경: {user_id} in {room_id}")
        return room["state"]

    def next_turn(self, room_id: str) -> Dict[str, Any]:
        """다음 차례로 이동

        Args:
            room_id: 방 ID

        Returns:
            업데이트된 상태
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]
        state = room["state"]

        turn_order = state.get("turn_order", [])
        if not turn_order:
            raise ValueError("순서가 설정되지 않았습니다.")

        # 다음 순서
        current_idx = state.get("current_turn_idx", 0)
        next_idx = (current_idx + 1) % len(turn_order)

        # 한 바퀴 돌면 라운드 증가
        if next_idx == 0:
            state["round_number"] = state.get("round_number", 1) + 1

        state["current_turn_idx"] = next_idx
        state["current_speaker_id"] = turn_order[next_idx]

        # 참가자 상태 업데이트
        for p in room["participants"]:
            if p["user_id"] == turn_order[next_idx]:
                p["status"] = ParticipantStatus.ANSWERING
            else:
                p["status"] = ParticipantStatus.WAITING

        room["last_activity"] = datetime.now().isoformat()
        self._save_rooms(rooms)

        logger.debug(f"다음 차례: {turn_order[next_idx]} in {room_id}")
        return state

    # ========== 면접 흐름 관리 ==========

    def set_questions(self, room_id: str, questions: List[str]) -> Dict[str, Any]:
        """면접 질문 설정

        Args:
            room_id: 방 ID
            questions: 질문 목록

        Returns:
            업데이트된 방 정보
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]
        room["questions"] = questions
        room["state"]["current_question_idx"] = 0
        room["last_activity"] = datetime.now().isoformat()

        self._save_rooms(rooms)

        logger.info(f"질문 {len(questions)}개 설정: {room_id}")
        return room

    def get_current_question(self, room_id: str) -> Optional[str]:
        """현재 질문 조회

        Args:
            room_id: 방 ID

        Returns:
            현재 질문 또는 None
        """
        room = self.get_room(room_id)
        if not room:
            return None

        questions = room.get("questions", [])
        current_idx = room.get("state", {}).get("current_question_idx", 0)

        if current_idx < len(questions):
            return questions[current_idx]
        return None

    def next_question(self, room_id: str) -> Optional[str]:
        """다음 질문으로 이동

        Args:
            room_id: 방 ID

        Returns:
            다음 질문 또는 None (모든 질문 완료 시)
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]
        questions = room.get("questions", [])
        current_idx = room.get("state", {}).get("current_question_idx", 0)

        next_idx = current_idx + 1

        if next_idx >= len(questions):
            # 모든 질문 완료
            room["state"]["phase"] = "reviewing"
            self._save_rooms(rooms)

            self._add_system_message(room_id, "모든 질문이 완료되었습니다.")
            logger.info(f"모든 질문 완료: {room_id}")
            return None

        room["state"]["current_question_idx"] = next_idx
        room["state"]["current_turn_idx"] = 0

        # 순서 초기화
        turn_order = room["state"].get("turn_order", [])
        if turn_order:
            room["state"]["current_speaker_id"] = turn_order[0]
            for p in room["participants"]:
                if p["user_id"] == turn_order[0]:
                    p["status"] = ParticipantStatus.ANSWERING
                else:
                    p["status"] = ParticipantStatus.WAITING

        room["last_activity"] = datetime.now().isoformat()
        self._save_rooms(rooms)

        self._add_system_message(room_id, f"질문 {next_idx + 1}: {questions[next_idx]}")
        logger.debug(f"다음 질문: {next_idx + 1}/{len(questions)} in {room_id}")

        return questions[next_idx]

    def submit_answer(
        self,
        room_id: str,
        user_id: str,
        answer: str,
        audio_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """답변 제출

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            answer: 답변 텍스트
            audio_bytes: 음성 데이터 (선택)

        Returns:
            제출된 답변 정보
        """
        rooms = self._load_rooms()

        if room_id not in rooms:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        room = rooms[room_id]

        # 참가자 확인
        participant = None
        for p in room["participants"]:
            if p["user_id"] == user_id:
                participant = p
                break

        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")

        current_idx = room.get("state", {}).get("current_question_idx", 0)

        # 오디오 데이터 인코딩
        audio_data = None
        if audio_bytes:
            audio_data = base64.b64encode(audio_bytes).decode("utf-8")

        answer_data = Answer(
            user_id=user_id,
            user_name=participant["user_name"],
            question_idx=current_idx,
            answer_text=answer,
            audio_data=audio_data
        )

        room["answers"].append(answer_data.to_dict())
        room["last_activity"] = datetime.now().isoformat()

        self._save_rooms(rooms)

        logger.info(f"답변 제출: {user_id} for Q{current_idx + 1} in {room_id}")
        return answer_data.to_dict()

    def get_all_answers(
        self,
        room_id: str,
        question_idx: int
    ) -> List[Dict[str, Any]]:
        """특정 질문에 대한 모든 답변 조회

        Args:
            room_id: 방 ID
            question_idx: 질문 인덱스

        Returns:
            답변 목록
        """
        room = self.get_room(room_id)
        if not room:
            return []

        answers = room.get("answers", [])
        return [a for a in answers if a["question_idx"] == question_idx]

    # ========== 채팅/커뮤니케이션 ==========

    def _add_system_message(self, room_id: str, message: str) -> None:
        """시스템 메시지 추가"""
        msg = Message(
            room_id=room_id,
            user_id="system",
            user_name="시스템",
            message=message,
            message_type="system"
        )

        messages = self._load_messages()
        messages.append(msg.to_dict())
        self._save_messages(messages)

    def send_message(
        self,
        room_id: str,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """채팅 메시지 전송

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            message: 메시지 내용

        Returns:
            전송된 메시지 정보
        """
        room = self.get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        # 참가자 확인
        participant = None
        for p in room["participants"]:
            if p["user_id"] == user_id:
                participant = p
                break

        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")

        msg = Message(
            room_id=room_id,
            user_id=user_id,
            user_name=participant["user_name"],
            message=message,
            message_type="chat"
        )

        messages = self._load_messages()
        messages.append(msg.to_dict())
        self._save_messages(messages)

        self._update_last_activity(room_id)

        logger.debug(f"메시지 전송: {user_id} in {room_id}")
        return msg.to_dict()

    def get_messages(
        self,
        room_id: str,
        since_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """채팅 메시지 조회

        Args:
            room_id: 방 ID
            since_timestamp: 이 시간 이후 메시지만 조회 (ISO 형식)

        Returns:
            메시지 목록
        """
        messages = self._load_messages()

        room_messages = [m for m in messages if m["room_id"] == room_id]

        if since_timestamp:
            since = datetime.fromisoformat(since_timestamp)
            room_messages = [
                m for m in room_messages
                if datetime.fromisoformat(m["timestamp"]) > since
            ]

        return sorted(room_messages, key=lambda m: m["timestamp"])

    def send_reaction(
        self,
        room_id: str,
        user_id: str,
        target_user_id: str,
        reaction: str
    ) -> Dict[str, Any]:
        """리액션 전송

        Args:
            room_id: 방 ID
            user_id: 보내는 사용자 ID
            target_user_id: 받는 사용자 ID
            reaction: 리액션 종류 (thumbs_up, clap, heart, fire, thinking)

        Returns:
            전송된 리액션 정보
        """
        valid_reactions = ["thumbs_up", "clap", "heart", "fire", "thinking"]
        if reaction not in valid_reactions:
            raise ValueError(f"유효하지 않은 리액션입니다. 가능한 리액션: {valid_reactions}")

        room = self.get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        # 참가자 확인
        sender = None
        target = None
        for p in room["participants"]:
            if p["user_id"] == user_id:
                sender = p
            if p["user_id"] == target_user_id:
                target = p

        if not sender:
            raise ValueError("방에 참가하지 않은 사용자입니다.")
        if not target:
            raise ValueError("대상 사용자가 방에 없습니다.")

        reaction_names = {
            "thumbs_up": "좋아요",
            "clap": "박수",
            "heart": "하트",
            "fire": "불꽃",
            "thinking": "생각중"
        }

        msg = Message(
            room_id=room_id,
            user_id=user_id,
            user_name=sender["user_name"],
            message=f"{sender['user_name']}님이 {target['user_name']}님에게 {reaction_names.get(reaction, reaction)}를 보냈습니다.",
            message_type="reaction",
            target_user_id=target_user_id,
            reaction=reaction
        )

        messages = self._load_messages()
        messages.append(msg.to_dict())
        self._save_messages(messages)

        self._update_last_activity(room_id)

        logger.debug(f"리액션 전송: {user_id} -> {target_user_id} ({reaction}) in {room_id}")
        return msg.to_dict()


# 싱글톤 인스턴스
_room_manager: Optional[RoomManager] = None


def get_room_manager() -> RoomManager:
    """RoomManager 싱글톤 인스턴스 반환"""
    global _room_manager
    if _room_manager is None:
        _room_manager = RoomManager()
    return _room_manager


# 편의 함수들 (모듈 레벨에서 직접 호출 가능)

def create_room(
    host_id: str,
    room_name: str,
    room_type: str,
    max_participants: int = 4,
    settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """새 방 생성"""
    return get_room_manager().create_room(
        host_id, room_name, room_type, max_participants, settings
    )


def get_room(room_id: str) -> Optional[Dict[str, Any]]:
    """방 정보 조회"""
    return get_room_manager().get_room(room_id)


def delete_room(room_id: str, user_id: str) -> bool:
    """방 삭제"""
    return get_room_manager().delete_room(room_id, user_id)


def update_room_settings(
    room_id: str,
    user_id: str,
    settings: Dict[str, Any]
) -> Dict[str, Any]:
    """방 설정 업데이트"""
    return get_room_manager().update_room_settings(room_id, user_id, settings)


def list_available_rooms(room_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """참가 가능한 방 목록"""
    return get_room_manager().list_available_rooms(room_type)


def join_room(room_id: str, user_id: str, user_name: str) -> Dict[str, Any]:
    """방 참가"""
    return get_room_manager().join_room(room_id, user_id, user_name)


def leave_room(room_id: str, user_id: str) -> bool:
    """방 나가기"""
    return get_room_manager().leave_room(room_id, user_id)


def kick_participant(room_id: str, host_id: str, target_user_id: str) -> bool:
    """참가자 강퇴"""
    return get_room_manager().kick_participant(room_id, host_id, target_user_id)


def get_participants(room_id: str) -> List[Dict[str, Any]]:
    """참가자 목록"""
    return get_room_manager().get_participants(room_id)


def update_participant_status(room_id: str, user_id: str, status: str) -> Dict[str, Any]:
    """참가자 상태 업데이트"""
    return get_room_manager().update_participant_status(room_id, user_id, status)


def start_session(room_id: str, host_id: str) -> Dict[str, Any]:
    """세션 시작"""
    return get_room_manager().start_session(room_id, host_id)


def end_session(room_id: str) -> Dict[str, Any]:
    """세션 종료"""
    return get_room_manager().end_session(room_id)


def get_room_state(room_id: str) -> Dict[str, Any]:
    """방 상태 조회"""
    return get_room_manager().get_room_state(room_id)


def set_current_speaker(room_id: str, user_id: str) -> Dict[str, Any]:
    """현재 발언자 설정"""
    return get_room_manager().set_current_speaker(room_id, user_id)


def next_turn(room_id: str) -> Dict[str, Any]:
    """다음 차례"""
    return get_room_manager().next_turn(room_id)


def set_questions(room_id: str, questions: List[str]) -> Dict[str, Any]:
    """질문 설정"""
    return get_room_manager().set_questions(room_id, questions)


def get_current_question(room_id: str) -> Optional[str]:
    """현재 질문"""
    return get_room_manager().get_current_question(room_id)


def next_question(room_id: str) -> Optional[str]:
    """다음 질문"""
    return get_room_manager().next_question(room_id)


def submit_answer(
    room_id: str,
    user_id: str,
    answer: str,
    audio_bytes: Optional[bytes] = None
) -> Dict[str, Any]:
    """답변 제출"""
    return get_room_manager().submit_answer(room_id, user_id, answer, audio_bytes)


def get_all_answers(room_id: str, question_idx: int) -> List[Dict[str, Any]]:
    """질문별 답변 조회"""
    return get_room_manager().get_all_answers(room_id, question_idx)


def send_message(room_id: str, user_id: str, message: str) -> Dict[str, Any]:
    """채팅 메시지 전송"""
    return get_room_manager().send_message(room_id, user_id, message)


def get_messages(
    room_id: str,
    since_timestamp: Optional[str] = None
) -> List[Dict[str, Any]]:
    """채팅 메시지 조회"""
    return get_room_manager().get_messages(room_id, since_timestamp)


def send_reaction(
    room_id: str,
    user_id: str,
    target_user_id: str,
    reaction: str
) -> Dict[str, Any]:
    """리액션 전송"""
    return get_room_manager().send_reaction(room_id, user_id, target_user_id, reaction)
