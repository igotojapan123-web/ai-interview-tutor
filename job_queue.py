# job_queue.py
# 백그라운드 작업 큐 시스템 - 비동기 작업 처리

import json
import uuid
import threading
import queue
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

JOBS_FILE = JOBS_DIR / "jobs.json"
MAX_WORKERS = 4
MAX_RETRIES = 3
JOB_TIMEOUT_SECONDS = 300


# ============================================================
# 데이터 클래스
# ============================================================

class JobStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """작업 우선순위"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Job:
    """작업 정의"""
    id: str
    name: str
    func_name: str
    args: tuple = None
    kwargs: Dict[str, Any] = None
    status: str = "pending"
    priority: int = 1
    result: Any = None
    error: str = None
    retries: int = 0
    max_retries: int = MAX_RETRIES
    created_at: str = None
    started_at: str = None
    completed_at: str = None
    scheduled_at: str = None

    def __post_init__(self):
        if self.args is None:
            self.args = ()
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


# ============================================================
# 작업 레지스트리
# ============================================================

class JobRegistry:
    """등록된 작업 함수 관리"""

    def __init__(self):
        self._functions: Dict[str, Callable] = {}

    def register(self, name: str = None):
        """작업 함수 등록 데코레이터"""
        def decorator(func: Callable):
            func_name = name or func.__name__
            self._functions[func_name] = func
            return func
        return decorator

    def get(self, name: str) -> Optional[Callable]:
        """등록된 함수 조회"""
        return self._functions.get(name)

    def list_functions(self) -> List[str]:
        """등록된 함수 목록"""
        return list(self._functions.keys())


# 전역 레지스트리
job_registry = JobRegistry()


# ============================================================
# 작업 큐
# ============================================================

class JobQueue:
    """백그라운드 작업 큐"""

    def __init__(self, max_workers: int = MAX_WORKERS):
        self.max_workers = max_workers
        self._queue = queue.PriorityQueue()
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

        # 저장된 작업 로드
        self._load_jobs()

    def _load_jobs(self) -> None:
        """저장된 작업 로드"""
        try:
            if JOBS_FILE.exists():
                with open(JOBS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for job_data in data.get("jobs", []):
                        # pending 작업만 복원
                        if job_data.get("status") == "pending":
                            job = Job(**job_data)
                            self._jobs[job.id] = job
                            self._queue.put((-job.priority, job.created_at, job.id))
        except Exception as e:
            logger.error(f"작업 로드 실패: {e}")

    def _save_jobs(self) -> None:
        """작업 저장"""
        try:
            with open(JOBS_FILE, "w", encoding="utf-8") as f:
                jobs_data = {"jobs": []}
                for job in self._jobs.values():
                    job_dict = asdict(job)
                    # result는 직렬화 불가할 수 있음
                    if job_dict.get("result") is not None:
                        try:
                            json.dumps(job_dict["result"])
                        except:
                            job_dict["result"] = str(job_dict["result"])
                    jobs_data["jobs"].append(job_dict)
                json.dump(jobs_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"작업 저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 작업 관리
    # -------------------------------------------------------------------------

    def enqueue(
        self,
        func_name: str,
        args: tuple = None,
        kwargs: Dict[str, Any] = None,
        name: str = None,
        priority: JobPriority = JobPriority.NORMAL,
        scheduled_at: datetime = None
    ) -> str:
        """
        작업 추가

        Args:
            func_name: 등록된 함수 이름
            args: 위치 인자
            kwargs: 키워드 인자
            name: 작업 표시 이름
            priority: 우선순위
            scheduled_at: 예약 실행 시간

        Returns:
            작업 ID
        """
        with self._lock:
            job_id = str(uuid.uuid4())[:8]

            job = Job(
                id=job_id,
                name=name or func_name,
                func_name=func_name,
                args=args or (),
                kwargs=kwargs or {},
                priority=priority.value,
                scheduled_at=scheduled_at.isoformat() if scheduled_at else None
            )

            self._jobs[job_id] = job
            self._queue.put((-job.priority, job.created_at, job_id))
            self._save_jobs()

            logger.info(f"작업 추가: {job_id} ({func_name})")
            return job_id

    def cancel(self, job_id: str) -> bool:
        """작업 취소"""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if job.status == "pending":
                job.status = "cancelled"
                self._save_jobs()
                logger.info(f"작업 취소: {job_id}")
                return True

            return False

    def get_job(self, job_id: str) -> Optional[Job]:
        """작업 조회"""
        return self._jobs.get(job_id)

    def get_status(self, job_id: str) -> Optional[str]:
        """작업 상태 조회"""
        job = self._jobs.get(job_id)
        return job.status if job else None

    def get_result(self, job_id: str) -> Optional[Any]:
        """작업 결과 조회"""
        job = self._jobs.get(job_id)
        return job.result if job else None

    def list_jobs(self, status: str = None, limit: int = 100) -> List[Job]:
        """작업 목록"""
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    # -------------------------------------------------------------------------
    # 작업 실행
    # -------------------------------------------------------------------------

    def start(self) -> None:
        """작업 처리 시작"""
        if self._running:
            return

        self._running = True
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info(f"작업 큐 시작 (workers: {self.max_workers})")

    def stop(self) -> None:
        """작업 처리 중지"""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        logger.info("작업 큐 중지")

    def _process_queue(self) -> None:
        """큐 처리 루프"""
        while self._running:
            try:
                # 타임아웃으로 큐에서 작업 가져오기
                try:
                    _, _, job_id = self._queue.get(timeout=1)
                except queue.Empty:
                    continue

                job = self._jobs.get(job_id)
                if not job or job.status != "pending":
                    continue

                # 예약 시간 확인
                if job.scheduled_at:
                    scheduled = datetime.fromisoformat(job.scheduled_at)
                    if datetime.now() < scheduled:
                        # 아직 시간 안됨, 다시 큐에 넣기
                        self._queue.put((-job.priority, job.created_at, job_id))
                        time.sleep(1)
                        continue

                # 작업 실행
                self._execute_job(job)

            except Exception as e:
                logger.error(f"큐 처리 오류: {e}")

    def _execute_job(self, job: Job) -> None:
        """작업 실행"""
        func = job_registry.get(job.func_name)
        if not func:
            job.status = "failed"
            job.error = f"함수를 찾을 수 없음: {job.func_name}"
            self._save_jobs()
            return

        job.status = "running"
        job.started_at = datetime.now().isoformat()
        self._save_jobs()

        try:
            # 실행
            result = func(*job.args, **job.kwargs)
            job.status = "completed"
            job.result = result
            job.completed_at = datetime.now().isoformat()
            logger.info(f"작업 완료: {job.id}")

        except Exception as e:
            job.retries += 1
            if job.retries < job.max_retries:
                # 재시도
                job.status = "pending"
                job.error = str(e)
                self._queue.put((-job.priority, job.created_at, job.id))
                logger.warning(f"작업 재시도 ({job.retries}/{job.max_retries}): {job.id}")
            else:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.now().isoformat()
                logger.error(f"작업 실패: {job.id} - {e}")

        self._save_jobs()

    # -------------------------------------------------------------------------
    # 통계
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """큐 통계"""
        with self._lock:
            jobs = list(self._jobs.values())

            by_status = {}
            for status in ["pending", "running", "completed", "failed", "cancelled"]:
                by_status[status] = sum(1 for j in jobs if j.status == status)

            return {
                "total_jobs": len(jobs),
                "by_status": by_status,
                "queue_size": self._queue.qsize(),
                "running": self._running,
                "max_workers": self.max_workers
            }


# 전역 큐 인스턴스
job_queue = JobQueue()


# ============================================================
# 기본 작업 등록
# ============================================================

@job_registry.register("send_email")
def send_email_job(to: str, subject: str, body: str) -> Dict[str, Any]:
    """이메일 발송 작업"""
    # 실제 구현에서는 이메일 발송 로직
    time.sleep(1)  # 시뮬레이션
    return {"sent_to": to, "subject": subject}


@job_registry.register("generate_report")
def generate_report_job(user_id: str, report_type: str) -> Dict[str, Any]:
    """리포트 생성 작업"""
    time.sleep(2)  # 시뮬레이션
    return {"user_id": user_id, "report_type": report_type, "status": "generated"}


@job_registry.register("process_audio")
def process_audio_job(file_path: str) -> Dict[str, Any]:
    """오디오 처리 작업"""
    time.sleep(3)  # 시뮬레이션
    return {"file_path": file_path, "processed": True}


@job_registry.register("cleanup_data")
def cleanup_data_job(days: int = 30) -> Dict[str, Any]:
    """데이터 정리 작업"""
    time.sleep(1)
    return {"days": days, "cleaned": True}


# ============================================================
# 간편 함수
# ============================================================

def enqueue(
    func_name: str,
    args: tuple = None,
    kwargs: Dict[str, Any] = None,
    priority: str = "normal"
) -> str:
    """작업 추가"""
    priority_map = {
        "low": JobPriority.LOW,
        "normal": JobPriority.NORMAL,
        "high": JobPriority.HIGH,
        "critical": JobPriority.CRITICAL
    }
    return job_queue.enqueue(
        func_name,
        args,
        kwargs,
        priority=priority_map.get(priority, JobPriority.NORMAL)
    )


def get_job_status(job_id: str) -> Optional[str]:
    """작업 상태 조회"""
    return job_queue.get_status(job_id)


def get_job_result(job_id: str) -> Optional[Any]:
    """작업 결과 조회"""
    return job_queue.get_result(job_id)


def start_worker() -> None:
    """워커 시작"""
    job_queue.start()


def stop_worker() -> None:
    """워커 중지"""
    job_queue.stop()


# ============================================================
# Streamlit 컴포넌트
# ============================================================

def render_job_queue_dashboard():
    """작업 큐 대시보드"""
    import streamlit as st

    st.markdown("### 작업 큐 현황")

    stats = job_queue.get_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("대기중", stats["by_status"].get("pending", 0))
    with col2:
        st.metric("실행중", stats["by_status"].get("running", 0))
    with col3:
        st.metric("완료", stats["by_status"].get("completed", 0))
    with col4:
        st.metric("실패", stats["by_status"].get("failed", 0))

    # 최근 작업
    st.markdown("#### 최근 작업")
    jobs = job_queue.list_jobs(limit=10)

    for job in jobs:
        status_icon = {
            "pending": "🕐",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫"
        }.get(job.status, "❓")

        st.text(f"{status_icon} {job.id}: {job.name} ({job.status})")


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Job Queue System ===")

    # 워커 시작
    start_worker()

    # 테스트 작업 추가
    job_id = enqueue("cleanup_data", kwargs={"days": 7})
    print(f"작업 추가: {job_id}")

    # 상태 확인
    time.sleep(2)
    print(f"상태: {get_job_status(job_id)}")

    # 통계
    print(f"통계: {job_queue.get_stats()}")

    # 워커 중지
    stop_worker()
    print("\nReady!")
