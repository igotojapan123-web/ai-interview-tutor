# admin_alerts.py
# FlyReady Lab - 관리자 알림 시스템
# 텔레그램, 슬랙, 이메일 알림 지원

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
import threading

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
ALERT_DIR = DATA_DIR / "alerts"
ALERT_DIR.mkdir(parents=True, exist_ok=True)

ALERT_CONFIG_FILE = ALERT_DIR / "config.json"
ALERT_HISTORY_FILE = ALERT_DIR / "history.json"

# ============================================================
# 환경 변수
# ============================================================

# 텔레그램
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 슬랙
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# 이메일 (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# ============================================================
# 알림 타입
# ============================================================

class AlertType(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    CRITICAL = "critical"
    USAGE = "usage"
    PAYMENT = "payment"
    USER = "user"
    SYSTEM = "system"

class AlertChannel(Enum):
    TELEGRAM = "telegram"
    SLACK = "slack"
    EMAIL = "email"
    ALL = "all"

# ============================================================
# 유틸리티
# ============================================================

def load_json(filepath: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(filepath: Path, data: Any) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except:
        return False

# ============================================================
# 텔레그램 알림
# ============================================================

class TelegramAlert:
    """텔레그램 알림 클래스"""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot_token and self.chat_id)

    def send(self, message: str, parse_mode: str = "HTML") -> bool:
        """메시지 전송"""
        if not self.enabled:
            logger.debug("텔레그램 미설정 - 알림 건너뜀")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"텔레그램 전송 실패: {e}")
            return False

    def send_formatted(self, title: str, content: str,
                      alert_type: AlertType = AlertType.INFO) -> bool:
        """포맷된 메시지 전송"""
        emoji_map = {
            AlertType.ERROR: "🚨",
            AlertType.WARNING: "⚠️",
            AlertType.INFO: "ℹ️",
            AlertType.CRITICAL: "🔴",
            AlertType.USAGE: "📊",
            AlertType.PAYMENT: "💳",
            AlertType.USER: "👤",
            AlertType.SYSTEM: "🔧",
        }

        emoji = emoji_map.get(alert_type, "📢")
        message = f"{emoji} <b>{title}</b>\n\n{content}\n\n<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"

        return self.send(message)

# ============================================================
# 슬랙 알림
# ============================================================

class SlackAlert:
    """슬랙 알림 클래스"""

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or SLACK_WEBHOOK_URL
        self.enabled = bool(self.webhook_url)

    def send(self, message: str) -> bool:
        """메시지 전송"""
        if not self.enabled:
            logger.debug("슬랙 미설정 - 알림 건너뜀")
            return False

        try:
            payload = {"text": message}
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"슬랙 전송 실패: {e}")
            return False

    def send_formatted(self, title: str, content: str,
                      alert_type: AlertType = AlertType.INFO,
                      fields: List[Dict] = None) -> bool:
        """포맷된 메시지 전송 (블록 형식)"""
        if not self.enabled:
            return False

        color_map = {
            AlertType.ERROR: "#FF0000",
            AlertType.WARNING: "#FFA500",
            AlertType.INFO: "#36A64F",
            AlertType.CRITICAL: "#8B0000",
            AlertType.USAGE: "#4169E1",
            AlertType.PAYMENT: "#32CD32",
            AlertType.USER: "#9370DB",
            AlertType.SYSTEM: "#708090",
        }

        attachment = {
            "color": color_map.get(alert_type, "#808080"),
            "title": title,
            "text": content,
            "footer": "FlyReady Lab Admin",
            "ts": datetime.now().timestamp()
        }

        if fields:
            attachment["fields"] = fields

        try:
            payload = {"attachments": [attachment]}
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"슬랙 전송 실패: {e}")
            return False

# ============================================================
# 이메일 알림
# ============================================================

class EmailAlert:
    """이메일 알림 클래스"""

    def __init__(self, smtp_host: str = None, smtp_port: int = None,
                 smtp_user: str = None, smtp_password: str = None,
                 admin_email: str = None):
        self.smtp_host = smtp_host or SMTP_HOST
        self.smtp_port = smtp_port or SMTP_PORT
        self.smtp_user = smtp_user or SMTP_USER
        self.smtp_password = smtp_password or SMTP_PASSWORD
        self.admin_email = admin_email or ADMIN_EMAIL
        self.enabled = bool(self.smtp_user and self.smtp_password and self.admin_email)

    def send(self, subject: str, body: str, html: bool = False) -> bool:
        """이메일 전송"""
        if not self.enabled:
            logger.debug("이메일 미설정 - 알림 건너뜀")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[FlyReady Lab] {subject}"
            msg["From"] = self.smtp_user
            msg["To"] = self.admin_email

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.admin_email, msg.as_string())

            return True
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")
            return False

    def send_formatted(self, title: str, content: str,
                      alert_type: AlertType = AlertType.INFO) -> bool:
        """포맷된 이메일 전송"""
        color_map = {
            AlertType.ERROR: "#dc3545",
            AlertType.WARNING: "#ffc107",
            AlertType.INFO: "#17a2b8",
            AlertType.CRITICAL: "#721c24",
            AlertType.USAGE: "#007bff",
            AlertType.PAYMENT: "#28a745",
            AlertType.USER: "#6f42c1",
            AlertType.SYSTEM: "#6c757d",
        }

        color = color_map.get(alert_type, "#6c757d")

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert-box {{ border-left: 4px solid {color}; padding: 15px; background: #f8f9fa; margin: 10px 0; }}
                .title {{ color: {color}; font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .content {{ color: #333; line-height: 1.6; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <div class="title">{title}</div>
                <div class="content">{content.replace(chr(10), '<br>')}</div>
            </div>
            <div class="footer">
                FlyReady Lab Admin System<br>
                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """

        return self.send(title, html_body, html=True)

# ============================================================
# 통합 알림 매니저
# ============================================================

class AlertManager:
    """통합 알림 관리 클래스"""

    def __init__(self):
        self.telegram = TelegramAlert()
        self.slack = SlackAlert()
        self.email = EmailAlert()
        self.history = load_json(ALERT_HISTORY_FILE, {"alerts": []})
        self.config = load_json(ALERT_CONFIG_FILE, {
            "enabled": True,
            "channels": {
                "error": ["telegram", "slack", "email"],
                "warning": ["telegram", "slack"],
                "info": ["telegram"],
                "critical": ["telegram", "slack", "email"],
                "usage": ["telegram"],
                "payment": ["telegram", "slack", "email"],
                "user": ["telegram"],
                "system": ["telegram", "slack"],
            },
            "rate_limit": {
                "enabled": True,
                "max_per_hour": 20,
                "cooldown_seconds": 60
            }
        })

    def _save_history(self):
        save_json(ALERT_HISTORY_FILE, self.history)

    def _save_config(self):
        save_json(ALERT_CONFIG_FILE, self.config)

    def _should_send(self, alert_type: AlertType) -> bool:
        """알림 전송 여부 결정 (레이트 리밋)"""
        if not self.config.get("enabled", True):
            return False

        rate_config = self.config.get("rate_limit", {})
        if not rate_config.get("enabled", True):
            return True

        # 최근 1시간 알림 수 체크
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_count = 0

        for alert in self.history.get("alerts", []):
            sent_at = alert.get("sent_at")
            if sent_at:
                try:
                    sent_dt = datetime.fromisoformat(sent_at)
                    if sent_dt >= one_hour_ago:
                        recent_count += 1
                except:
                    pass

        max_per_hour = rate_config.get("max_per_hour", 20)
        if recent_count >= max_per_hour:
            logger.warning(f"알림 레이트 리밋 초과: {recent_count}/{max_per_hour}")
            return False

        # 쿨다운 체크
        if self.history.get("alerts"):
            last_alert = self.history["alerts"][-1]
            last_sent = last_alert.get("sent_at")
            if last_sent:
                try:
                    last_dt = datetime.fromisoformat(last_sent)
                    cooldown = rate_config.get("cooldown_seconds", 60)
                    if (datetime.now() - last_dt).total_seconds() < cooldown:
                        # CRITICAL은 쿨다운 무시
                        if alert_type != AlertType.CRITICAL:
                            return False
                except:
                    pass

        return True

    def _record_alert(self, title: str, alert_type: AlertType,
                     channels_sent: List[str]):
        """알림 기록"""
        alert_record = {
            "title": title,
            "type": alert_type.value,
            "channels": channels_sent,
            "sent_at": datetime.now().isoformat()
        }

        if "alerts" not in self.history:
            self.history["alerts"] = []
        self.history["alerts"].append(alert_record)

        # 최대 1000개 유지
        if len(self.history["alerts"]) > 1000:
            self.history["alerts"] = self.history["alerts"][-1000:]

        self._save_history()

    def send(self, title: str, content: str,
             alert_type: AlertType = AlertType.INFO,
             channels: List[str] = None) -> Dict:
        """알림 전송"""
        if not self._should_send(alert_type):
            return {"success": False, "reason": "rate_limited"}

        # 채널 결정
        if channels is None:
            channels = self.config.get("channels", {}).get(alert_type.value, ["telegram"])

        results = {}
        channels_sent = []

        for channel in channels:
            if channel == "telegram":
                success = self.telegram.send_formatted(title, content, alert_type)
            elif channel == "slack":
                success = self.slack.send_formatted(title, content, alert_type)
            elif channel == "email":
                success = self.email.send_formatted(title, content, alert_type)
            else:
                success = False

            results[channel] = success
            if success:
                channels_sent.append(channel)

        # 기록
        self._record_alert(title, alert_type, channels_sent)

        return {
            "success": len(channels_sent) > 0,
            "channels_sent": channels_sent,
            "results": results
        }

    def send_async(self, title: str, content: str,
                   alert_type: AlertType = AlertType.INFO):
        """비동기 알림 전송"""
        thread = threading.Thread(
            target=self.send,
            args=(title, content, alert_type)
        )
        thread.daemon = True
        thread.start()

    # ============================================================
    # 특화된 알림 메서드
    # ============================================================

    def send_error_alert(self, error_info: Dict) -> Dict:
        """에러 알림"""
        title = f"에러 발생: {error_info.get('type', 'Unknown')}"
        content = f"""
페이지: {error_info.get('page', 'N/A')}
메시지: {error_info.get('message', 'N/A')}
시간: {error_info.get('timestamp', 'N/A')}

상세:
{error_info.get('traceback', '')[:500]}
        """.strip()

        level = error_info.get('level', 'error')
        alert_type = AlertType.CRITICAL if level == 'critical' else AlertType.ERROR

        return self.send(title, content, alert_type)

    def send_usage_alert(self, api_name: str, current: int, limit: int) -> Dict:
        """API 사용량 경고"""
        percentage = (current / limit * 100) if limit > 0 else 0
        title = f"API 사용량 경고: {api_name}"
        content = f"""
API: {api_name}
현재 사용량: {current:,}
일일 한도: {limit:,}
사용률: {percentage:.1f}%

한도 초과 시 서비스가 중단될 수 있습니다.
        """.strip()

        return self.send(title, content, AlertType.USAGE)

    def send_payment_alert(self, event_type: str, data: Dict) -> Dict:
        """결제 관련 알림"""
        title_map = {
            "new_subscription": "새 구독",
            "subscription_cancelled": "구독 취소",
            "payment_failed": "결제 실패",
            "subscription_expiring": "구독 만료 임박",
        }

        title = title_map.get(event_type, "결제 알림")
        content = f"""
이벤트: {event_type}
사용자: {data.get('user_id', 'N/A')}
플랜: {data.get('plan', 'N/A')}
금액: {data.get('amount', 0):,}원
        """.strip()

        alert_type = AlertType.WARNING if 'failed' in event_type else AlertType.PAYMENT
        return self.send(title, content, alert_type)

    def send_user_alert(self, event_type: str, data: Dict) -> Dict:
        """사용자 관련 알림"""
        title_map = {
            "new_signup": "신규 가입",
            "user_deactivated": "사용자 비활성화",
            "milestone_reached": "마일스톤 달성",
        }

        title = title_map.get(event_type, "사용자 알림")
        content = f"""
이벤트: {event_type}
사용자: {data.get('user_id', 'N/A')}
이메일: {data.get('email', 'N/A')}
        """.strip()

        return self.send(title, content, AlertType.USER)

    def send_system_alert(self, title: str, content: str,
                         is_critical: bool = False) -> Dict:
        """시스템 알림"""
        alert_type = AlertType.CRITICAL if is_critical else AlertType.SYSTEM
        return self.send(title, content, alert_type)

    def send_daily_summary(self, summary: Dict) -> Dict:
        """일일 요약 알림"""
        content = f"""
📊 일일 요약 리포트

👤 사용자
- 총 사용자: {summary.get('total_users', 0):,}명
- 오늘 활성: {summary.get('dau', 0):,}명
- 신규 가입: {summary.get('new_users', 0):,}명

💰 수익
- 오늘 매출: {summary.get('revenue_today', 0):,}원
- 이번 달 MRR: {summary.get('mrr', 0):,}원

🔧 시스템
- 에러: {summary.get('errors_today', 0)}건
- API 사용량: 정상
        """.strip()

        return self.send("일일 운영 요약", content, AlertType.INFO)

    def send_weekly_report(self, report: Dict) -> Dict:
        """주간 리포트 알림"""
        content = f"""
📈 주간 운영 리포트

기간: {report.get('period', 'N/A')}

👤 사용자 지표
- WAU: {report.get('wau', 0):,}명
- 신규 가입: {report.get('new_users_week', 0):,}명
- 이탈률: {report.get('churn_rate', 0):.1f}%

💰 수익 지표
- 주간 매출: {report.get('revenue_week', 0):,}원
- 전주 대비: {report.get('revenue_change', 0):+.1f}%

🔧 안정성
- 총 에러: {report.get('errors_week', 0)}건
- 해결률: {report.get('resolution_rate', 0):.1f}%

자세한 내용은 관리자 대시보드에서 확인하세요.
        """.strip()

        return self.send("주간 운영 리포트", content, AlertType.INFO,
                        channels=["telegram", "slack", "email"])

# ============================================================
# 전역 인스턴스
# ============================================================

_alert_manager = None

def get_alert_manager() -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager

# ============================================================
# 간편 함수
# ============================================================

def send_alert(title: str, content: str,
               alert_type: AlertType = AlertType.INFO) -> Dict:
    """알림 전송 간편 함수"""
    return get_alert_manager().send(title, content, alert_type)

def send_error_alert(error_info: Dict) -> Dict:
    """에러 알림 간편 함수"""
    return get_alert_manager().send_error_alert(error_info)

def send_system_alert(title: str, content: str, is_critical: bool = False) -> Dict:
    """시스템 알림 간편 함수"""
    return get_alert_manager().send_system_alert(title, content, is_critical)
