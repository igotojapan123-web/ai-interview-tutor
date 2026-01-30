# admin_dashboard.py
# FlyReady Lab - 관리자 대시보드 백엔드 모듈
# 사용자 관리, 구독 관리, 통계, 수익 분석

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
import hashlib

# 로깅 설정
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# 경로 설정
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ADMIN_DIR = DATA_DIR / "admin"
ADMIN_DIR.mkdir(parents=True, exist_ok=True)

# 데이터 파일 경로
USERS_FILE = ADMIN_DIR / "users.json"
SUBSCRIPTIONS_FILE = ADMIN_DIR / "subscriptions.json"
REVENUE_FILE = ADMIN_DIR / "revenue.json"
USAGE_STATS_FILE = ADMIN_DIR / "usage_stats.json"
AUDIT_LOG_FILE = ADMIN_DIR / "audit_log.json"

# ============================================================
# 데이터 로드/저장 유틸리티
# ============================================================

def load_json(filepath: Path, default: Any = None) -> Any:
    """JSON 파일 로드"""
    if default is None:
        default = {}
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON 로드 실패 ({filepath}): {e}")
    return default

def save_json(filepath: Path, data: Any) -> bool:
    """JSON 파일 저장"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"JSON 저장 실패 ({filepath}): {e}")
        return False

# ============================================================
# 사용자 관리
# ============================================================

class UserManager:
    """사용자 관리 클래스"""

    def __init__(self):
        self.users = load_json(USERS_FILE, {"users": []})

    def _save(self):
        save_json(USERS_FILE, self.users)

    def get_all_users(self) -> List[Dict]:
        """모든 사용자 목록 반환"""
        return self.users.get("users", [])

    def get_user(self, user_id: str) -> Optional[Dict]:
        """특정 사용자 조회"""
        for user in self.users.get("users", []):
            if user.get("id") == user_id:
                return user
        return None

    def get_user_count(self) -> int:
        """총 사용자 수"""
        return len(self.users.get("users", []))

    def get_active_users(self, days: int = 7) -> List[Dict]:
        """최근 N일 내 활성 사용자"""
        cutoff = datetime.now() - timedelta(days=days)
        active = []
        for user in self.users.get("users", []):
            last_active = user.get("last_active")
            if last_active:
                try:
                    last_dt = datetime.fromisoformat(last_active)
                    if last_dt >= cutoff:
                        active.append(user)
                except:
                    pass
        return active

    def get_users_by_plan(self, plan: str) -> List[Dict]:
        """특정 플랜 사용자 목록"""
        return [u for u in self.users.get("users", []) if u.get("plan") == plan]

    def get_new_users(self, days: int = 7) -> List[Dict]:
        """최근 N일 내 신규 가입자"""
        cutoff = datetime.now() - timedelta(days=days)
        new_users = []
        for user in self.users.get("users", []):
            created = user.get("created_at")
            if created:
                try:
                    created_dt = datetime.fromisoformat(created)
                    if created_dt >= cutoff:
                        new_users.append(user)
                except:
                    pass
        return new_users

    def update_user(self, user_id: str, updates: Dict) -> bool:
        """사용자 정보 업데이트"""
        for i, user in enumerate(self.users.get("users", [])):
            if user.get("id") == user_id:
                self.users["users"][i].update(updates)
                self.users["users"][i]["updated_at"] = datetime.now().isoformat()
                self._save()
                return True
        return False

    def add_user(self, user_data: Dict) -> str:
        """새 사용자 추가"""
        user_id = user_data.get("id") or hashlib.md5(
            f"{user_data.get('email', '')}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        user = {
            "id": user_id,
            "email": user_data.get("email", ""),
            "name": user_data.get("name", ""),
            "plan": user_data.get("plan", "free"),
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "status": "active",
            **user_data
        }

        if "users" not in self.users:
            self.users["users"] = []
        self.users["users"].append(user)
        self._save()
        return user_id

    def deactivate_user(self, user_id: str, reason: str = "") -> bool:
        """사용자 비활성화"""
        return self.update_user(user_id, {
            "status": "deactivated",
            "deactivated_at": datetime.now().isoformat(),
            "deactivation_reason": reason
        })

    def get_user_statistics(self) -> Dict:
        """사용자 통계"""
        users = self.users.get("users", [])

        plan_counts = defaultdict(int)
        status_counts = defaultdict(int)

        for user in users:
            plan_counts[user.get("plan", "free")] += 1
            status_counts[user.get("status", "active")] += 1

        return {
            "total_users": len(users),
            "active_users_7d": len(self.get_active_users(7)),
            "active_users_30d": len(self.get_active_users(30)),
            "new_users_7d": len(self.get_new_users(7)),
            "new_users_30d": len(self.get_new_users(30)),
            "by_plan": dict(plan_counts),
            "by_status": dict(status_counts),
        }

# ============================================================
# 구독 관리
# ============================================================

class SubscriptionManager:
    """구독 관리 클래스"""

    PLANS = {
        "free": {"name": "FREE", "price": 0, "price_yearly": 0},
        "standard_monthly": {"name": "STANDARD 월간", "price": 19900, "price_yearly": None},
        "standard_yearly": {"name": "STANDARD 연간", "price": None, "price_yearly": 149000},
        "premium_monthly": {"name": "PREMIUM 월간", "price": 49900, "price_yearly": None},
        "premium_yearly": {"name": "PREMIUM 연간", "price": None, "price_yearly": 299000},
    }

    def __init__(self):
        self.subscriptions = load_json(SUBSCRIPTIONS_FILE, {"subscriptions": []})

    def _save(self):
        save_json(SUBSCRIPTIONS_FILE, self.subscriptions)

    def get_all_subscriptions(self) -> List[Dict]:
        """모든 구독 목록"""
        return self.subscriptions.get("subscriptions", [])

    def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """사용자 현재 구독"""
        for sub in self.subscriptions.get("subscriptions", []):
            if sub.get("user_id") == user_id and sub.get("status") == "active":
                return sub
        return None

    def get_active_subscriptions(self) -> List[Dict]:
        """활성 구독 목록"""
        return [s for s in self.subscriptions.get("subscriptions", [])
                if s.get("status") == "active"]

    def get_expiring_subscriptions(self, days: int = 7) -> List[Dict]:
        """곧 만료될 구독 (N일 이내)"""
        cutoff = datetime.now() + timedelta(days=days)
        expiring = []
        for sub in self.get_active_subscriptions():
            expires = sub.get("expires_at")
            if expires:
                try:
                    exp_dt = datetime.fromisoformat(expires)
                    if exp_dt <= cutoff:
                        expiring.append(sub)
                except:
                    pass
        return expiring

    def create_subscription(self, user_id: str, plan: str,
                           payment_id: str = None) -> Dict:
        """새 구독 생성"""
        now = datetime.now()

        # 기간 계산
        if "yearly" in plan:
            expires = now + timedelta(days=365)
        else:
            expires = now + timedelta(days=30)

        subscription = {
            "id": hashlib.md5(f"{user_id}{now.isoformat()}".encode()).hexdigest()[:12],
            "user_id": user_id,
            "plan": plan,
            "status": "active",
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "payment_id": payment_id,
            "auto_renew": True,
        }

        if "subscriptions" not in self.subscriptions:
            self.subscriptions["subscriptions"] = []
        self.subscriptions["subscriptions"].append(subscription)
        self._save()

        return subscription

    def cancel_subscription(self, subscription_id: str, reason: str = "") -> bool:
        """구독 취소"""
        for i, sub in enumerate(self.subscriptions.get("subscriptions", [])):
            if sub.get("id") == subscription_id:
                self.subscriptions["subscriptions"][i]["status"] = "cancelled"
                self.subscriptions["subscriptions"][i]["cancelled_at"] = datetime.now().isoformat()
                self.subscriptions["subscriptions"][i]["cancel_reason"] = reason
                self._save()
                return True
        return False

    def get_subscription_statistics(self) -> Dict:
        """구독 통계"""
        subs = self.subscriptions.get("subscriptions", [])

        plan_counts = defaultdict(int)
        status_counts = defaultdict(int)

        for sub in subs:
            plan_counts[sub.get("plan", "unknown")] += 1
            status_counts[sub.get("status", "unknown")] += 1

        active = self.get_active_subscriptions()

        return {
            "total_subscriptions": len(subs),
            "active_subscriptions": len(active),
            "expiring_7d": len(self.get_expiring_subscriptions(7)),
            "by_plan": dict(plan_counts),
            "by_status": dict(status_counts),
        }

    def get_churn_rate(self, days: int = 30) -> float:
        """이탈률 계산 (최근 N일)"""
        cutoff = datetime.now() - timedelta(days=days)

        cancelled = 0
        active_start = 0

        for sub in self.subscriptions.get("subscriptions", []):
            created = sub.get("created_at")
            if created:
                try:
                    created_dt = datetime.fromisoformat(created)
                    if created_dt < cutoff:
                        active_start += 1
                except:
                    pass

            cancelled_at = sub.get("cancelled_at")
            if cancelled_at:
                try:
                    cancel_dt = datetime.fromisoformat(cancelled_at)
                    if cancel_dt >= cutoff:
                        cancelled += 1
                except:
                    pass

        if active_start == 0:
            return 0.0
        return (cancelled / active_start) * 100

# ============================================================
# 수익 관리
# ============================================================

class RevenueManager:
    """수익 관리 클래스"""

    def __init__(self):
        self.revenue = load_json(REVENUE_FILE, {"transactions": []})

    def _save(self):
        save_json(REVENUE_FILE, self.revenue)

    def add_transaction(self, user_id: str, amount: int, plan: str,
                       payment_method: str = "", payment_id: str = "") -> Dict:
        """거래 추가"""
        transaction = {
            "id": hashlib.md5(f"{user_id}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            "user_id": user_id,
            "amount": amount,
            "plan": plan,
            "payment_method": payment_method,
            "payment_id": payment_id,
            "status": "completed",
            "created_at": datetime.now().isoformat(),
        }

        if "transactions" not in self.revenue:
            self.revenue["transactions"] = []
        self.revenue["transactions"].append(transaction)
        self._save()

        return transaction

    def get_transactions(self, days: int = None) -> List[Dict]:
        """거래 목록 조회"""
        transactions = self.revenue.get("transactions", [])

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for t in transactions:
                created = t.get("created_at")
                if created:
                    try:
                        if datetime.fromisoformat(created) >= cutoff:
                            filtered.append(t)
                    except:
                        pass
            return filtered

        return transactions

    def get_total_revenue(self, days: int = None) -> int:
        """총 수익"""
        transactions = self.get_transactions(days)
        return sum(t.get("amount", 0) for t in transactions if t.get("status") == "completed")

    def get_mrr(self) -> int:
        """월간 반복 수익 (MRR)"""
        # 활성 구독 기준 계산
        sub_manager = SubscriptionManager()
        active_subs = sub_manager.get_active_subscriptions()

        mrr = 0
        for sub in active_subs:
            plan = sub.get("plan", "")
            plan_info = sub_manager.PLANS.get(plan, {})

            if "yearly" in plan:
                yearly_price = plan_info.get("price_yearly", 0) or 0
                mrr += yearly_price // 12
            else:
                mrr += plan_info.get("price", 0) or 0

        return mrr

    def get_daily_revenue(self, days: int = 30) -> List[Dict]:
        """일별 수익"""
        transactions = self.get_transactions(days)

        daily = defaultdict(int)
        for t in transactions:
            if t.get("status") == "completed":
                created = t.get("created_at", "")[:10]  # YYYY-MM-DD
                daily[created] += t.get("amount", 0)

        # 정렬하여 반환
        result = []
        for date in sorted(daily.keys()):
            result.append({"date": date, "amount": daily[date]})

        return result

    def get_revenue_statistics(self) -> Dict:
        """수익 통계"""
        return {
            "total_revenue": self.get_total_revenue(),
            "revenue_30d": self.get_total_revenue(30),
            "revenue_7d": self.get_total_revenue(7),
            "mrr": self.get_mrr(),
            "transaction_count": len(self.get_transactions()),
            "daily_revenue": self.get_daily_revenue(30),
        }

# ============================================================
# 사용량 통계
# ============================================================

class UsageStatsManager:
    """사용량 통계 관리"""

    def __init__(self):
        self.stats = load_json(USAGE_STATS_FILE, {"daily": {}, "features": {}})

    def _save(self):
        save_json(USAGE_STATS_FILE, self.stats)

    def record_usage(self, user_id: str, feature: str, count: int = 1):
        """사용량 기록"""
        today = datetime.now().strftime("%Y-%m-%d")

        if "daily" not in self.stats:
            self.stats["daily"] = {}
        if today not in self.stats["daily"]:
            self.stats["daily"][today] = {"users": set(), "features": defaultdict(int)}

        # 일별 활성 사용자
        if isinstance(self.stats["daily"][today].get("users"), list):
            self.stats["daily"][today]["users"] = set(self.stats["daily"][today]["users"])
        elif not isinstance(self.stats["daily"][today].get("users"), set):
            self.stats["daily"][today]["users"] = set()

        self.stats["daily"][today]["users"].add(user_id)

        # 기능별 사용량
        if "features" not in self.stats["daily"][today]:
            self.stats["daily"][today]["features"] = {}
        if feature not in self.stats["daily"][today]["features"]:
            self.stats["daily"][today]["features"][feature] = 0
        self.stats["daily"][today]["features"][feature] += count

        # set을 list로 변환하여 저장
        self.stats["daily"][today]["users"] = list(self.stats["daily"][today]["users"])
        self._save()

    def get_daily_active_users(self, date: str = None) -> int:
        """일별 활성 사용자 수"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        day_data = self.stats.get("daily", {}).get(date, {})
        users = day_data.get("users", [])
        return len(users) if isinstance(users, (list, set)) else 0

    def get_feature_usage(self, feature: str, days: int = 7) -> int:
        """기능별 사용량"""
        total = 0
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = self.stats.get("daily", {}).get(date, {})
            total += day_data.get("features", {}).get(feature, 0)
        return total

    def get_usage_statistics(self) -> Dict:
        """사용량 통계 요약"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 최근 7일 DAU
        dau_7d = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            dau_7d.append({
                "date": date,
                "dau": self.get_daily_active_users(date)
            })

        # 기능별 사용량
        features = ["모의면접", "자소서첨삭", "퀴즈", "AI코칭", "그룹면접"]
        feature_stats = {}
        for f in features:
            feature_stats[f] = self.get_feature_usage(f, 7)

        return {
            "dau_today": self.get_daily_active_users(today),
            "dau_7d": dau_7d,
            "feature_usage_7d": feature_stats,
        }

# ============================================================
# 감사 로그
# ============================================================

class AuditLogger:
    """감사 로그 관리"""

    def __init__(self):
        self.logs = load_json(AUDIT_LOG_FILE, {"logs": []})

    def _save(self):
        save_json(AUDIT_LOG_FILE, self.logs)

    def log(self, action: str, admin_id: str, target_id: str = "",
            details: Dict = None, level: str = "info"):
        """감사 로그 기록"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "admin_id": admin_id,
            "target_id": target_id,
            "details": details or {},
            "level": level,
        }

        if "logs" not in self.logs:
            self.logs["logs"] = []
        self.logs["logs"].append(log_entry)

        # 최대 10000개 로그 유지
        if len(self.logs["logs"]) > 10000:
            self.logs["logs"] = self.logs["logs"][-10000:]

        self._save()

    def get_logs(self, days: int = 7, action: str = None,
                 admin_id: str = None) -> List[Dict]:
        """로그 조회"""
        cutoff = datetime.now() - timedelta(days=days)

        filtered = []
        for log in self.logs.get("logs", []):
            timestamp = log.get("timestamp")
            if timestamp:
                try:
                    log_dt = datetime.fromisoformat(timestamp)
                    if log_dt < cutoff:
                        continue
                except:
                    continue

            if action and log.get("action") != action:
                continue
            if admin_id and log.get("admin_id") != admin_id:
                continue

            filtered.append(log)

        return filtered

# ============================================================
# 대시보드 요약
# ============================================================

def get_dashboard_summary() -> Dict:
    """대시보드 전체 요약"""
    user_mgr = UserManager()
    sub_mgr = SubscriptionManager()
    rev_mgr = RevenueManager()
    usage_mgr = UsageStatsManager()

    return {
        "users": user_mgr.get_user_statistics(),
        "subscriptions": sub_mgr.get_subscription_statistics(),
        "revenue": rev_mgr.get_revenue_statistics(),
        "usage": usage_mgr.get_usage_statistics(),
        "churn_rate": sub_mgr.get_churn_rate(30),
        "generated_at": datetime.now().isoformat(),
    }

# ============================================================
# 초기화
# ============================================================

def initialize():
    """관리자 시스템 초기화"""
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)

    # 기본 파일 생성
    if not USERS_FILE.exists():
        save_json(USERS_FILE, {"users": []})
    if not SUBSCRIPTIONS_FILE.exists():
        save_json(SUBSCRIPTIONS_FILE, {"subscriptions": []})
    if not REVENUE_FILE.exists():
        save_json(REVENUE_FILE, {"transactions": []})
    if not USAGE_STATS_FILE.exists():
        save_json(USAGE_STATS_FILE, {"daily": {}, "features": {}})
    if not AUDIT_LOG_FILE.exists():
        save_json(AUDIT_LOG_FILE, {"logs": []})

    logger.info("관리자 시스템 초기화 완료")

# 모듈 로드 시 초기화
initialize()
