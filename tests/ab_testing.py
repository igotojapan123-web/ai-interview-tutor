# ab_testing.py
# A/B 테스트 프레임워크 - 기능 실험 및 최적화

import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

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
EXPERIMENTS_DIR = DATA_DIR / "experiments"
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

EXPERIMENTS_FILE = EXPERIMENTS_DIR / "experiments.json"


# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class Variant:
    """실험 변형"""
    name: str
    weight: float = 1.0
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class Experiment:
    """A/B 테스트 실험"""
    id: str
    name: str
    description: str
    variants: List[Variant]
    status: str = "draft"
    start_date: str = None
    end_date: str = None
    target_sample_size: int = 1000
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


# ============================================================
# A/B 테스트 엔진
# ============================================================

class ABTestingEngine:
    """A/B 테스트 엔진"""

    def __init__(self):
        self._lock = threading.Lock()
        self._experiments: Dict[str, Experiment] = {}
        self._user_assignments: Dict[str, Dict[str, str]] = {}
        self._results: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self) -> None:
        """저장된 데이터 로드"""
        try:
            if EXPERIMENTS_FILE.exists():
                with open(EXPERIMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for exp_data in data.get("experiments", []):
                        variants = [Variant(**v) for v in exp_data.pop("variants", [])]
                        exp = Experiment(**exp_data, variants=variants)
                        self._experiments[exp.id] = exp
                    self._user_assignments = data.get("assignments", {})
        except Exception as e:
            logger.error(f"A/B 테스트 데이터 로드 실패: {e}")

    def _save_data(self) -> None:
        """데이터 저장"""
        try:
            experiments_data = {
                "experiments": [],
                "assignments": self._user_assignments
            }
            for exp in self._experiments.values():
                exp_dict = asdict(exp)
                experiments_data["experiments"].append(exp_dict)

            with open(EXPERIMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(experiments_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"A/B 테스트 데이터 저장 실패: {e}")

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        target_sample_size: int = 1000
    ) -> Experiment:
        """새 실험 생성"""
        with self._lock:
            if experiment_id in self._experiments:
                raise ValueError(f"실험 ID가 이미 존재합니다: {experiment_id}")

            variant_objects = [Variant(**v) for v in variants]
            experiment = Experiment(
                id=experiment_id,
                name=name,
                description=description,
                variants=variant_objects,
                target_sample_size=target_sample_size
            )
            self._experiments[experiment_id] = experiment
            self._save_data()
            logger.info(f"실험 생성: {experiment_id}")
            return experiment

    def start_experiment(self, experiment_id: str) -> None:
        """실험 시작"""
        with self._lock:
            if experiment_id not in self._experiments:
                raise ValueError(f"실험을 찾을 수 없습니다: {experiment_id}")
            exp = self._experiments[experiment_id]
            exp.status = "running"
            exp.start_date = datetime.now().isoformat()
            self._save_data()
            logger.info(f"실험 시작: {experiment_id}")

    def stop_experiment(self, experiment_id: str) -> None:
        """실험 종료"""
        with self._lock:
            if experiment_id not in self._experiments:
                raise ValueError(f"실험을 찾을 수 없습니다: {experiment_id}")
            exp = self._experiments[experiment_id]
            exp.status = "completed"
            exp.end_date = datetime.now().isoformat()
            self._save_data()
            logger.info(f"실험 종료: {experiment_id}")

    def get_variant(self, experiment_id: str, user_id: str) -> Optional[Variant]:
        """사용자에게 변형 할당/조회"""
        with self._lock:
            exp = self._experiments.get(experiment_id)
            if not exp or exp.status != "running":
                return None

            # 이미 할당된 경우
            if user_id in self._user_assignments:
                if experiment_id in self._user_assignments[user_id]:
                    variant_name = self._user_assignments[user_id][experiment_id]
                    for v in exp.variants:
                        if v.name == variant_name:
                            return v

            # 새로 할당 (일관된 해시 기반)
            variant = self._assign_variant(exp, user_id)

            if user_id not in self._user_assignments:
                self._user_assignments[user_id] = {}
            self._user_assignments[user_id][experiment_id] = variant.name
            self._save_data()
            return variant

    def _assign_variant(self, experiment: Experiment, user_id: str) -> Variant:
        """변형 할당 (일관된 해시 기반)"""
        hash_input = f"{user_id}:{experiment.id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        total_weight = sum(v.weight for v in experiment.variants)
        normalized = hash_value % 10000 / 10000.0 * total_weight

        cumulative = 0
        for variant in experiment.variants:
            cumulative += variant.weight
            if normalized < cumulative:
                return variant
        return experiment.variants[-1]

    def track_event(
        self,
        experiment_id: str,
        user_id: str,
        event: str,
        value: float = None
    ) -> None:
        """이벤트 기록"""
        with self._lock:
            variant_name = None
            if user_id in self._user_assignments:
                variant_name = self._user_assignments[user_id].get(experiment_id)

            if not variant_name:
                return

            self._results.append({
                "experiment_id": experiment_id,
                "variant_name": variant_name,
                "user_id": user_id,
                "event": event,
                "value": value,
                "timestamp": datetime.now().isoformat()
            })

    def track_conversion(self, experiment_id: str, user_id: str, value: float = 1.0) -> None:
        """전환 추적"""
        self.track_event(experiment_id, user_id, "conversion", value)

    def get_results(self, experiment_id: str) -> Dict[str, Any]:
        """실험 결과 분석"""
        with self._lock:
            exp = self._experiments.get(experiment_id)
            if not exp:
                return {}

            variant_stats = {}
            for variant in exp.variants:
                variant_stats[variant.name] = {
                    "participants": 0,
                    "conversions": 0,
                    "conversion_rate": 0.0
                }

            # 참여자 수
            for user_id, assignments in self._user_assignments.items():
                if experiment_id in assignments:
                    variant_name = assignments[experiment_id]
                    if variant_name in variant_stats:
                        variant_stats[variant_name]["participants"] += 1

            # 전환 수
            for result in self._results:
                if result["experiment_id"] == experiment_id and result["event"] == "conversion":
                    if result["variant_name"] in variant_stats:
                        variant_stats[result["variant_name"]]["conversions"] += 1

            # 전환율 계산
            winner = None
            best_rate = -1
            for name, stats in variant_stats.items():
                if stats["participants"] > 0:
                    stats["conversion_rate"] = stats["conversions"] / stats["participants"]
                if stats["conversion_rate"] > best_rate:
                    best_rate = stats["conversion_rate"]
                    winner = name

            return {
                "experiment_id": experiment_id,
                "name": exp.name,
                "status": exp.status,
                "variants": variant_stats,
                "winner": winner,
                "total_participants": sum(s["participants"] for s in variant_stats.values())
            }

    def list_experiments(self, status: str = None) -> List[Experiment]:
        """실험 목록"""
        experiments = list(self._experiments.values())
        if status:
            experiments = [e for e in experiments if e.status == status]
        return experiments


# 전역 인스턴스
ab_engine = ABTestingEngine()


# ============================================================
# 간편 함수
# ============================================================

def create_experiment(
    experiment_id: str,
    name: str,
    variants: List[Dict[str, Any]],
    description: str = ""
) -> Experiment:
    """실험 생성"""
    return ab_engine.create_experiment(experiment_id, name, description, variants)


def get_variant(experiment_id: str, user_id: str) -> Optional[Variant]:
    """변형 가져오기"""
    return ab_engine.get_variant(experiment_id, user_id)


def track_conversion(experiment_id: str, user_id: str, value: float = 1.0) -> None:
    """전환 추적"""
    ab_engine.track_conversion(experiment_id, user_id, value)


def get_experiment_results(experiment_id: str) -> Dict[str, Any]:
    """실험 결과"""
    return ab_engine.get_results(experiment_id)


# ============================================================
# Streamlit 컴포넌트
# ============================================================

def render_ab_dashboard():
    """A/B 테스트 대시보드"""
    import streamlit as st

    st.markdown("### A/B 테스트 현황")

    experiments = ab_engine.list_experiments()

    if not experiments:
        st.info("진행 중인 실험이 없습니다.")
        return

    for exp in experiments:
        with st.expander(f"{exp.name} ({exp.status})"):
            results = ab_engine.get_results(exp.id)

            for name, stats in results.get("variants", {}).items():
                st.text(f"{name}: {stats['participants']}명, 전환율 {stats['conversion_rate']:.1%}")


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== A/B Testing Framework ===")
    print("Ready!")
