# notification_system.py
# FlyReady Lab - 알림 시스템 (카카오 알림톡 + 이메일 + 웹 푸시)

import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import streamlit as st

from logging_config import get_logger
logger = get_logger(__name__)

# ============================================
# 환경 변수 설정
# ============================================

# 카카오 알림톡 설정
KAKAO_ALIMTALK_API_KEY = os.getenv("KAKAO_ALIMTALK_API_KEY", "")
KAKAO_ALIMTALK_SENDER_KEY = os.getenv("KAKAO_ALIMTALK_SENDER_KEY", "")
KAKAO_ALIMTALK_TEMPLATE_ID = os.getenv("KAKAO_ALIMTALK_TEMPLATE_ID", "")

# 이메일 설정 (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@flyready.kr")

# 웹 푸시 설정 (Firebase Cloud Messaging)
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")

# ============================================
# 데이터 저장소
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, "notifications.json")
NOTIFICATION_SETTINGS_FILE = os.path.join(DATA_DIR, "notification_settings.json")
PUSH_TOKENS_FILE = os.path.join(DATA_DIR, "push_tokens.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_notifications() -> List[Dict]:
    """알림 내역 로드"""
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            with open(NOTIFICATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"알림 내역 로드 실패: {e}")
    return []


def save_notifications(notifications: List[Dict]):
    """알림 내역 저장"""
    try:
        with open(NOTIFICATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(notifications, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"알림 내역 저장 실패: {e}")


def load_notification_settings() -> Dict:
    """알림 설정 로드"""
    if os.path.exists(NOTIFICATION_SETTINGS_FILE):
        try:
            with open(NOTIFICATION_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"알림 설정 로드 실패: {e}")
    return {}


def save_notification_settings(settings: Dict):
    """알림 설정 저장"""
    try:
        with open(NOTIFICATION_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"알림 설정 저장 실패: {e}")


def load_push_tokens() -> Dict:
    """푸시 토큰 로드"""
    if os.path.exists(PUSH_TOKENS_FILE):
        try:
            with open(PUSH_TOKENS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"푸시 토큰 로드 실패: {e}")
    return {}


def save_push_tokens(tokens: Dict):
    """푸시 토큰 저장"""
    try:
        with open(PUSH_TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"푸시 토큰 저장 실패: {e}")


# ============================================
# 알림 템플릿
# ============================================
NOTIFICATION_TEMPLATES = {
    "hiring_alert": {
        "title": "새로운 채용 공고",
        "template": "[FlyReady Lab]\n\n{airline} 채용 공고가 올라왔어요!\n\n{position}\n마감일: {deadline}\n\n지금 바로 확인하세요 👉 {link}",
        "alimtalk_template": "KA001",
    },
    "dday_reminder": {
        "title": "D-Day 알림",
        "template": "[FlyReady Lab]\n\n{event_name}까지 D-{days}!\n\n날짜: {date}\n\n마지막 점검 잊지 마세요!\n{link}",
        "alimtalk_template": "KA002",
    },
    "study_reminder": {
        "title": "학습 리마인더",
        "template": "[FlyReady Lab]\n\n오늘 학습 완료하셨나요?\n\n연속 학습 {streak}일째!\n놓치지 말고 계속 이어가세요 💪\n\n{link}",
        "alimtalk_template": "KA003",
    },
    "subscription_expiry": {
        "title": "구독 만료 예정",
        "template": "[FlyReady Lab]\n\n{user_name}님의 {tier} 구독이 {days}일 후 만료됩니다.\n\n지금 갱신하시면 20% 할인!\n{link}",
        "alimtalk_template": "KA004",
    },
    "mentor_match": {
        "title": "멘토 매칭 완료",
        "template": "[FlyReady Lab]\n\n{user_name}님, 멘토 매칭이 완료되었습니다!\n\n멘토: {mentor_name}\n항공사: {airline}\n\n첫 상담을 예약하세요 👉 {link}",
        "alimtalk_template": "KA005",
    },
    "feedback_ready": {
        "title": "피드백 도착",
        "template": "[FlyReady Lab]\n\n{user_name}님의 면접 연습 피드백이 도착했습니다!\n\n점수: {score}점\n\n자세한 내용 확인하기 👉 {link}",
        "alimtalk_template": "KA006",
    },
}


# ============================================
# 알림 설정 클래스
# ============================================
class NotificationSettings:
    def __init__(self, data: Dict):
        self.user_id = data.get("user_id", "")
        self.phone = data.get("phone", "")
        self.email = data.get("email", "")

        # 알림 채널 활성화
        self.kakao_enabled = data.get("kakao_enabled", False)
        self.email_enabled = data.get("email_enabled", True)
        self.push_enabled = data.get("push_enabled", False)

        # 알림 유형별 설정
        self.hiring_alert = data.get("hiring_alert", True)
        self.dday_reminder = data.get("dday_reminder", True)
        self.study_reminder = data.get("study_reminder", False)
        self.subscription_expiry = data.get("subscription_expiry", True)
        self.mentor_match = data.get("mentor_match", True)
        self.feedback_ready = data.get("feedback_ready", True)

        # D-Day 알림 시점
        self.dday_remind_days = data.get("dday_remind_days", [7, 3, 1])

        # 학습 리마인더 시간
        self.study_reminder_time = data.get("study_reminder_time", "20:00")

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "phone": self.phone,
            "email": self.email,
            "kakao_enabled": self.kakao_enabled,
            "email_enabled": self.email_enabled,
            "push_enabled": self.push_enabled,
            "hiring_alert": self.hiring_alert,
            "dday_reminder": self.dday_reminder,
            "study_reminder": self.study_reminder,
            "subscription_expiry": self.subscription_expiry,
            "mentor_match": self.mentor_match,
            "feedback_ready": self.feedback_ready,
            "dday_remind_days": self.dday_remind_days,
            "study_reminder_time": self.study_reminder_time,
        }


def get_user_notification_settings(user_id: str) -> NotificationSettings:
    """사용자 알림 설정 조회"""
    settings = load_notification_settings()
    if user_id in settings:
        return NotificationSettings(settings[user_id])
    return NotificationSettings({"user_id": user_id})


def save_user_notification_settings(settings: NotificationSettings):
    """사용자 알림 설정 저장"""
    all_settings = load_notification_settings()
    all_settings[settings.user_id] = settings.to_dict()
    save_notification_settings(all_settings)


# ============================================
# 카카오 알림톡 API
# ============================================
class KakaoAlimtalkAPI:
    BASE_URL = "https://alimtalk-api.kakao.com/v2"

    def __init__(self):
        self.api_key = KAKAO_ALIMTALK_API_KEY
        self.sender_key = KAKAO_ALIMTALK_SENDER_KEY

    def _get_headers(self) -> Dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def send(
        self,
        phone: str,
        template_code: str,
        template_params: Dict,
    ) -> bool:
        """알림톡 발송"""
        if not self.api_key or not self.sender_key:
            logger.warning("카카오 알림톡 API 키가 설정되지 않았습니다.")
            return False

        url = f"{self.BASE_URL}/messages/send"

        # 전화번호 포맷 정리
        phone = phone.replace("-", "").replace(" ", "")
        if not phone.startswith("82"):
            phone = "82" + phone[1:] if phone.startswith("0") else "82" + phone

        data = {
            "senderKey": self.sender_key,
            "templateCode": template_code,
            "messages": [
                {
                    "to": phone,
                    "templateParams": template_params,
                }
            ],
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=data)
            result = response.json()

            if result.get("success"):
                logger.info(f"알림톡 발송 성공: {phone}")
                return True
            else:
                logger.error(f"알림톡 발송 실패: {result}")
                return False

        except Exception as e:
            logger.error(f"알림톡 API 오류: {e}")
            return False


# ============================================
# 이메일 발송
# ============================================
class EmailSender:
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.from_email = EMAIL_FROM

    def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
    ) -> bool:
        """이메일 발송"""
        if not self.user or not self.password:
            logger.warning("SMTP 설정이 완료되지 않았습니다.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type, "utf-8"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"이메일 발송 성공: {to_email}")
            return True

        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False

    def send_html_template(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        params: Dict,
    ) -> bool:
        """HTML 템플릿 이메일 발송"""
        html_content = self._render_html_template(template_name, params)
        return self.send(to_email, subject, html_content, is_html=True)

    def _render_html_template(self, template_name: str, params: Dict) -> str:
        """HTML 템플릿 렌더링"""
        # 기본 이메일 템플릿
        base_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 0; background: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; }}
                .header {{ background: linear-gradient(135deg, #1e3a5f, #3b82f6); padding: 32px; text-align: center; }}
                .header img {{ height: 40px; }}
                .header h1 {{ color: white; margin: 16px 0 0 0; font-size: 24px; }}
                .content {{ padding: 32px; }}
                .content h2 {{ color: #1e3a5f; margin-top: 0; }}
                .content p {{ color: #475569; line-height: 1.6; }}
                .button {{ display: inline-block; background: #3b82f6; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 16px 0; }}
                .footer {{ background: #f8fafc; padding: 24px; text-align: center; color: #64748b; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>FlyReady Lab</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>FlyReady Lab | 당신의 꿈을 응원합니다</p>
                    <p><a href="{{unsubscribe_url}}">수신 거부</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        # 템플릿별 내용
        templates = {
            "hiring_alert": """
                <h2>새로운 채용 공고가 올라왔어요!</h2>
                <p><strong>{airline}</strong>에서 채용을 시작했습니다.</p>
                <p>포지션: {position}</p>
                <p>마감일: {deadline}</p>
                <a href="{link}" class="button">자세히 보기</a>
            """,
            "dday_reminder": """
                <h2>{event_name}까지 D-{days}!</h2>
                <p>중요한 일정이 다가오고 있어요.</p>
                <p>날짜: {date}</p>
                <p>마지막 점검, 잊지 마세요!</p>
                <a href="{link}" class="button">준비 상태 확인하기</a>
            """,
            "study_reminder": """
                <h2>오늘 학습 완료하셨나요?</h2>
                <p>연속 학습 <strong>{streak}일째</strong>!</p>
                <p>놓치지 말고 계속 이어가세요 💪</p>
                <a href="{link}" class="button">오늘 학습하기</a>
            """,
            "subscription_expiry": """
                <h2>구독이 곧 만료됩니다</h2>
                <p>{user_name}님의 <strong>{tier}</strong> 구독이 {days}일 후 만료됩니다.</p>
                <p>지금 갱신하시면 <strong>20% 할인</strong>!</p>
                <a href="{link}" class="button">구독 갱신하기</a>
            """,
            "feedback_ready": """
                <h2>피드백이 도착했습니다!</h2>
                <p>{user_name}님의 면접 연습 결과입니다.</p>
                <p>점수: <strong>{score}점</strong></p>
                <a href="{link}" class="button">자세한 피드백 보기</a>
            """,
        }

        content = templates.get(template_name, "<p>{message}</p>")
        content = content.format(**params)

        return base_template.format(content=content, **params)


# ============================================
# 웹 푸시 (FCM)
# ============================================
class FCMPushSender:
    FCM_URL = "https://fcm.googleapis.com/fcm/send"

    def __init__(self):
        self.server_key = FCM_SERVER_KEY

    def send(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
    ) -> bool:
        """FCM 푸시 발송"""
        if not self.server_key:
            logger.warning("FCM 서버 키가 설정되지 않았습니다.")
            return False

        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "to": token,
            "notification": {
                "title": title,
                "body": body,
                "icon": "/logo.png",
                "click_action": data.get("link", "/") if data else "/",
            },
        }

        if data:
            payload["data"] = data

        try:
            response = requests.post(self.FCM_URL, headers=headers, json=payload)
            result = response.json()

            if result.get("success") == 1:
                logger.info(f"FCM 푸시 발송 성공")
                return True
            else:
                logger.error(f"FCM 푸시 발송 실패: {result}")
                return False

        except Exception as e:
            logger.error(f"FCM API 오류: {e}")
            return False


def register_push_token(user_id: str, token: str):
    """푸시 토큰 등록"""
    tokens = load_push_tokens()
    tokens[user_id] = {
        "token": token,
        "registered_at": datetime.now().isoformat(),
    }
    save_push_tokens(tokens)


def get_push_token(user_id: str) -> Optional[str]:
    """푸시 토큰 조회"""
    tokens = load_push_tokens()
    if user_id in tokens:
        return tokens[user_id].get("token")
    return None


# ============================================
# 통합 알림 발송
# ============================================
def send_notification(
    user_id: str,
    notification_type: str,
    params: Dict,
) -> Dict[str, bool]:
    """통합 알림 발송"""
    results = {
        "kakao": False,
        "email": False,
        "push": False,
    }

    settings = get_user_notification_settings(user_id)

    # 알림 유형 체크
    if not getattr(settings, notification_type, True):
        logger.info(f"사용자가 {notification_type} 알림을 비활성화했습니다.")
        return results

    template = NOTIFICATION_TEMPLATES.get(notification_type, {})
    title = template.get("title", "FlyReady Lab 알림")
    message = template.get("template", "{message}").format(**params)

    # 카카오 알림톡
    if settings.kakao_enabled and settings.phone:
        kakao_api = KakaoAlimtalkAPI()
        results["kakao"] = kakao_api.send(
            phone=settings.phone,
            template_code=template.get("alimtalk_template", ""),
            template_params=params,
        )

    # 이메일
    if settings.email_enabled and settings.email:
        email_sender = EmailSender()
        results["email"] = email_sender.send_html_template(
            to_email=settings.email,
            subject=f"[FlyReady Lab] {title}",
            template_name=notification_type,
            params={**params, "unsubscribe_url": f"https://flyready.kr/unsubscribe?user={user_id}"},
        )

    # 웹 푸시
    if settings.push_enabled:
        token = get_push_token(user_id)
        if token:
            push_sender = FCMPushSender()
            results["push"] = push_sender.send(
                token=token,
                title=title,
                body=message[:100],
                data={"link": params.get("link", "/")},
            )

    # 알림 기록 저장
    notifications = load_notifications()
    notifications.append({
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "params": params,
        "results": results,
        "sent_at": datetime.now().isoformat(),
    })
    save_notifications(notifications[-1000:])  # 최근 1000개만 유지

    return results


# ============================================
# 예약 알림 (스케줄러용)
# ============================================
def send_hiring_alerts(airline: str, position: str, deadline: str, link: str):
    """채용 공고 알림 (전체 사용자)"""
    settings = load_notification_settings()

    for user_id, user_settings in settings.items():
        if user_settings.get("hiring_alert", True):
            send_notification(user_id, "hiring_alert", {
                "airline": airline,
                "position": position,
                "deadline": deadline,
                "link": link,
            })


def send_dday_reminders():
    """D-Day 알림 체크 및 발송"""
    try:
        from auth_system import load_users
        users = load_users()
    except ImportError:
        return

    calendar_file = os.path.join(DATA_DIR, "my_calendar.json")
    if not os.path.exists(calendar_file):
        return

    with open(calendar_file, "r", encoding="utf-8") as f:
        calendar_data = json.load(f)

    events = calendar_data.get("events", [])
    today = datetime.now().date()

    for event in events:
        try:
            event_date = datetime.strptime(event.get("date", ""), "%Y-%m-%d").date()
            days_left = (event_date - today).days

            # 모든 사용자에게 D-Day 알림
            for user_id in users.keys():
                settings = get_user_notification_settings(user_id)

                if settings.dday_reminder and days_left in settings.dday_remind_days:
                    send_notification(user_id, "dday_reminder", {
                        "event_name": event.get("title", "일정"),
                        "days": days_left,
                        "date": event.get("date", ""),
                        "link": "https://flyready.kr/D-Day캘린더",
                    })

        except (ValueError, TypeError):
            continue


def send_subscription_expiry_reminders():
    """구독 만료 예정 알림"""
    try:
        from payment_system import load_subscriptions
        subscriptions = load_subscriptions()
    except ImportError:
        return

    today = datetime.now()

    for user_id, sub in subscriptions.items():
        if not sub.get("is_active"):
            continue

        try:
            end_date = datetime.fromisoformat(sub.get("end_date", ""))
            days_left = (end_date.date() - today.date()).days

            if days_left in [7, 3, 1]:
                send_notification(user_id, "subscription_expiry", {
                    "user_name": user_id.split("_")[-1],
                    "tier": sub.get("tier", ""),
                    "days": days_left,
                    "link": "https://flyready.kr/pricing",
                })

        except (ValueError, TypeError):
            continue


# ============================================
# UI 컴포넌트
# ============================================
def render_notification_settings():
    """알림 설정 UI"""
    user = st.session_state.get("user")
    if not user:
        st.warning("로그인이 필요합니다.")
        return

    settings = get_user_notification_settings(user.user_id)

    st.markdown("### 알림 설정")

    st.markdown("#### 연락처 정보")
    col1, col2 = st.columns(2)

    with col1:
        phone = st.text_input("휴대폰 번호", value=settings.phone, placeholder="010-1234-5678")

    with col2:
        email = st.text_input("이메일", value=settings.email or user.email, placeholder="example@email.com")

    st.markdown("#### 알림 채널")
    col1, col2, col3 = st.columns(3)

    with col1:
        kakao_enabled = st.checkbox("카카오 알림톡", value=settings.kakao_enabled)

    with col2:
        email_enabled = st.checkbox("이메일", value=settings.email_enabled)

    with col3:
        push_enabled = st.checkbox("웹 푸시", value=settings.push_enabled)

    st.markdown("#### 알림 유형")

    col1, col2 = st.columns(2)

    with col1:
        hiring_alert = st.checkbox("채용 공고 알림", value=settings.hiring_alert)
        dday_reminder = st.checkbox("D-Day 리마인더", value=settings.dday_reminder)
        study_reminder = st.checkbox("학습 리마인더", value=settings.study_reminder)

    with col2:
        subscription_expiry = st.checkbox("구독 만료 알림", value=settings.subscription_expiry)
        mentor_match = st.checkbox("멘토 매칭 알림", value=settings.mentor_match)
        feedback_ready = st.checkbox("피드백 도착 알림", value=settings.feedback_ready)

    st.markdown("#### 세부 설정")

    if dday_reminder:
        dday_days = st.multiselect(
            "D-Day 알림 시점",
            options=[14, 7, 3, 1, 0],
            default=settings.dday_remind_days,
            format_func=lambda x: f"D-{x}" if x > 0 else "당일",
        )
    else:
        dday_days = settings.dday_remind_days

    if study_reminder:
        study_time = st.time_input(
            "학습 리마인더 시간",
            value=datetime.strptime(settings.study_reminder_time, "%H:%M").time(),
        )
        study_time_str = study_time.strftime("%H:%M")
    else:
        study_time_str = settings.study_reminder_time

    if st.button("설정 저장", type="primary"):
        new_settings = NotificationSettings({
            "user_id": user.user_id,
            "phone": phone,
            "email": email,
            "kakao_enabled": kakao_enabled,
            "email_enabled": email_enabled,
            "push_enabled": push_enabled,
            "hiring_alert": hiring_alert,
            "dday_reminder": dday_reminder,
            "study_reminder": study_reminder,
            "subscription_expiry": subscription_expiry,
            "mentor_match": mentor_match,
            "feedback_ready": feedback_ready,
            "dday_remind_days": dday_days,
            "study_reminder_time": study_time_str,
        })

        save_user_notification_settings(new_settings)
        st.success("알림 설정이 저장되었습니다!")


def render_notification_history():
    """알림 내역 표시"""
    user = st.session_state.get("user")
    if not user:
        return

    notifications = load_notifications()
    user_notifications = [n for n in notifications if n["user_id"] == user.user_id][-20:]

    if not user_notifications:
        st.info("알림 내역이 없습니다.")
        return

    st.markdown("### 최근 알림")

    for notif in reversed(user_notifications):
        sent_at = notif.get("sent_at", "")[:10]
        title = notif.get("title", "알림")

        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:12px 16px; margin-bottom:8px; border-left:3px solid #3b82f6;">
            <div style="font-weight:600; color:#1e3a5f;">{title}</div>
            <div style="font-size:0.85rem; color:#64748b; margin-top:4px;">{sent_at}</div>
        </div>
        """, unsafe_allow_html=True)
