# payment_system.py
# FlyReady Lab - 결제 시스템 (카카오페이 + 토스페이먼츠)

import os
import json
import uuid
import hmac
import hashlib
import base64
import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from logging_config import get_logger
logger = get_logger(__name__)

# ============================================
# 환경 변수 설정
# ============================================

# 카카오페이 설정
KAKAOPAY_CID = os.getenv("KAKAOPAY_CID", "TC0ONETIME")  # 테스트용 CID
KAKAOPAY_SECRET_KEY = os.getenv("KAKAOPAY_SECRET_KEY", "")
KAKAOPAY_ADMIN_KEY = os.getenv("KAKAOPAY_ADMIN_KEY", "")

# 토스페이먼츠 설정
TOSS_CLIENT_KEY = os.getenv("TOSS_CLIENT_KEY", "")
TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY", "")

# 콜백 URL
BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")
PAYMENT_SUCCESS_URL = f"{BASE_URL}/payment/success"
PAYMENT_FAIL_URL = f"{BASE_URL}/payment/fail"
PAYMENT_CANCEL_URL = f"{BASE_URL}/payment/cancel"

# ============================================
# 데이터 저장소
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.json")
SUBSCRIPTIONS_FILE = os.path.join(DATA_DIR, "subscriptions.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_payments() -> List[Dict]:
    """결제 내역 로드"""
    if os.path.exists(PAYMENTS_FILE):
        try:
            with open(PAYMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"결제 내역 로드 실패: {e}")
    return []


def save_payments(payments: List[Dict]):
    """결제 내역 저장"""
    try:
        with open(PAYMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(payments, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"결제 내역 저장 실패: {e}")


def load_subscriptions() -> Dict:
    """구독 정보 로드"""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"구독 정보 로드 실패: {e}")
    return {}


def save_subscriptions(subscriptions: Dict):
    """구독 정보 저장"""
    try:
        with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(subscriptions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"구독 정보 저장 실패: {e}")


# ============================================
# 상품 정의
# ============================================
PRODUCTS = {
    "standard_monthly": {
        "name": "스탠다드 월간",
        "tier": "standard",
        "price": 19900,
        "duration_days": 30,
        "description": "AI 면접 연습 30회/일, 자소서 첨삭 무제한",
    },
    "standard_yearly": {
        "name": "스탠다드 연간",
        "tier": "standard",
        "price": 149000,
        "duration_days": 365,
        "description": "AI 면접 연습 30회/일, 자소서 첨삭 무제한 (37% 할인)",
    },
    "premium_monthly": {
        "name": "프리미엄 월간",
        "tier": "premium",
        "price": 39900,
        "duration_days": 30,
        "description": "모든 기능 무제한 + 1:1 멘토 매칭",
    },
    "premium_yearly": {
        "name": "프리미엄 연간",
        "tier": "premium",
        "price": 299000,
        "duration_days": 365,
        "description": "모든 기능 무제한 + 1:1 멘토 매칭 (37% 할인)",
    },
}


# ============================================
# 결제 모델
# ============================================
class Payment:
    def __init__(self, data: Dict):
        self.payment_id = data.get("payment_id", "")
        self.user_id = data.get("user_id", "")
        self.product_id = data.get("product_id", "")
        self.amount = data.get("amount", 0)
        self.status = data.get("status", "pending")  # pending, completed, failed, refunded
        self.payment_method = data.get("payment_method", "")  # kakaopay, toss
        self.pg_transaction_id = data.get("pg_transaction_id", "")
        self.created_at = data.get("created_at", "")
        self.completed_at = data.get("completed_at", "")
        self.metadata = data.get("metadata", {})

    def to_dict(self) -> Dict:
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "amount": self.amount,
            "status": self.status,
            "payment_method": self.payment_method,
            "pg_transaction_id": self.pg_transaction_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


# ============================================
# 카카오페이 API
# ============================================
class KakaoPayAPI:
    BASE_URL = "https://kapi.kakao.com/v1/payment"

    def __init__(self):
        self.admin_key = KAKAOPAY_ADMIN_KEY
        self.cid = KAKAOPAY_CID

    def _get_headers(self) -> Dict:
        return {
            "Authorization": f"KakaoAK {self.admin_key}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }

    def ready(
        self,
        partner_order_id: str,
        partner_user_id: str,
        item_name: str,
        quantity: int,
        total_amount: int,
    ) -> Optional[Dict]:
        """결제 준비 요청"""
        url = f"{self.BASE_URL}/ready"

        data = {
            "cid": self.cid,
            "partner_order_id": partner_order_id,
            "partner_user_id": partner_user_id,
            "item_name": item_name,
            "quantity": quantity,
            "total_amount": total_amount,
            "vat_amount": int(total_amount / 11),
            "tax_free_amount": 0,
            "approval_url": PAYMENT_SUCCESS_URL + f"?method=kakaopay&order_id={partner_order_id}",
            "cancel_url": PAYMENT_CANCEL_URL + f"?method=kakaopay&order_id={partner_order_id}",
            "fail_url": PAYMENT_FAIL_URL + f"?method=kakaopay&order_id={partner_order_id}",
        }

        try:
            response = requests.post(url, headers=self._get_headers(), data=data)
            result = response.json()

            if "tid" in result:
                return {
                    "tid": result["tid"],
                    "redirect_url": result.get("next_redirect_pc_url", ""),
                    "redirect_url_mobile": result.get("next_redirect_mobile_url", ""),
                    "created_at": result.get("created_at", ""),
                }
            else:
                logger.error(f"카카오페이 준비 실패: {result}")
                return None

        except Exception as e:
            logger.error(f"카카오페이 API 오류: {e}")
            return None

    def approve(
        self,
        tid: str,
        partner_order_id: str,
        partner_user_id: str,
        pg_token: str,
    ) -> Optional[Dict]:
        """결제 승인 요청"""
        url = f"{self.BASE_URL}/approve"

        data = {
            "cid": self.cid,
            "tid": tid,
            "partner_order_id": partner_order_id,
            "partner_user_id": partner_user_id,
            "pg_token": pg_token,
        }

        try:
            response = requests.post(url, headers=self._get_headers(), data=data)
            result = response.json()

            if "aid" in result:
                return {
                    "aid": result["aid"],
                    "tid": result["tid"],
                    "payment_method_type": result.get("payment_method_type", ""),
                    "amount": result.get("amount", {}),
                    "approved_at": result.get("approved_at", ""),
                }
            else:
                logger.error(f"카카오페이 승인 실패: {result}")
                return None

        except Exception as e:
            logger.error(f"카카오페이 API 오류: {e}")
            return None

    def cancel(
        self,
        tid: str,
        cancel_amount: int,
        cancel_tax_free_amount: int = 0,
    ) -> Optional[Dict]:
        """결제 취소 요청"""
        url = f"{self.BASE_URL}/cancel"

        data = {
            "cid": self.cid,
            "tid": tid,
            "cancel_amount": cancel_amount,
            "cancel_tax_free_amount": cancel_tax_free_amount,
        }

        try:
            response = requests.post(url, headers=self._get_headers(), data=data)
            result = response.json()

            if "aid" in result:
                return result
            else:
                logger.error(f"카카오페이 취소 실패: {result}")
                return None

        except Exception as e:
            logger.error(f"카카오페이 API 오류: {e}")
            return None


# ============================================
# 토스페이먼츠 API
# ============================================
class TossPaymentsAPI:
    BASE_URL = "https://api.tosspayments.com/v1"

    def __init__(self):
        self.client_key = TOSS_CLIENT_KEY
        self.secret_key = TOSS_SECRET_KEY

    def _get_headers(self) -> Dict:
        auth_string = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        return {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
        }

    def confirm(
        self,
        payment_key: str,
        order_id: str,
        amount: int,
    ) -> Optional[Dict]:
        """결제 승인 요청"""
        url = f"{self.BASE_URL}/payments/confirm"

        data = {
            "paymentKey": payment_key,
            "orderId": order_id,
            "amount": amount,
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=data)
            result = response.json()

            if "paymentKey" in result:
                return {
                    "payment_key": result["paymentKey"],
                    "order_id": result["orderId"],
                    "status": result["status"],
                    "method": result.get("method", ""),
                    "total_amount": result.get("totalAmount", 0),
                    "approved_at": result.get("approvedAt", ""),
                }
            else:
                logger.error(f"토스 결제 승인 실패: {result}")
                return None

        except Exception as e:
            logger.error(f"토스 API 오류: {e}")
            return None

    def cancel(
        self,
        payment_key: str,
        cancel_reason: str,
        cancel_amount: Optional[int] = None,
    ) -> Optional[Dict]:
        """결제 취소 요청"""
        url = f"{self.BASE_URL}/payments/{payment_key}/cancel"

        data = {
            "cancelReason": cancel_reason,
        }
        if cancel_amount:
            data["cancelAmount"] = cancel_amount

        try:
            response = requests.post(url, headers=self._get_headers(), json=data)
            result = response.json()

            if "paymentKey" in result:
                return result
            else:
                logger.error(f"토스 결제 취소 실패: {result}")
                return None

        except Exception as e:
            logger.error(f"토스 API 오류: {e}")
            return None

    def get_client_key(self) -> str:
        """클라이언트 키 반환 (프론트엔드용)"""
        return self.client_key


# ============================================
# 결제 처리 함수
# ============================================
def create_payment(
    user_id: str,
    product_id: str,
    payment_method: str,
) -> Optional[Payment]:
    """결제 생성"""
    if product_id not in PRODUCTS:
        logger.error(f"존재하지 않는 상품: {product_id}")
        return None

    product = PRODUCTS[product_id]
    payment_id = f"pay_{uuid.uuid4().hex[:16]}"

    payment = Payment({
        "payment_id": payment_id,
        "user_id": user_id,
        "product_id": product_id,
        "amount": product["price"],
        "status": "pending",
        "payment_method": payment_method,
        "created_at": datetime.now().isoformat(),
    })

    # 저장
    payments = load_payments()
    payments.append(payment.to_dict())
    save_payments(payments)

    return payment


def get_payment(payment_id: str) -> Optional[Payment]:
    """결제 조회"""
    payments = load_payments()
    for p in payments:
        if p["payment_id"] == payment_id:
            return Payment(p)
    return None


def update_payment_status(payment_id: str, status: str, pg_transaction_id: str = ""):
    """결제 상태 업데이트"""
    payments = load_payments()
    for p in payments:
        if p["payment_id"] == payment_id:
            p["status"] = status
            if pg_transaction_id:
                p["pg_transaction_id"] = pg_transaction_id
            if status == "completed":
                p["completed_at"] = datetime.now().isoformat()
            break
    save_payments(payments)


def activate_subscription(user_id: str, product_id: str):
    """구독 활성화"""
    if product_id not in PRODUCTS:
        return False

    product = PRODUCTS[product_id]
    subscriptions = load_subscriptions()

    end_date = datetime.now() + timedelta(days=product["duration_days"])

    subscriptions[user_id] = {
        "tier": product["tier"],
        "product_id": product_id,
        "start_date": datetime.now().isoformat(),
        "end_date": end_date.isoformat(),
        "is_active": True,
    }

    save_subscriptions(subscriptions)

    # auth_system의 사용자 정보도 업데이트
    try:
        from auth_system import update_subscription
        update_subscription(user_id, product["tier"], product["duration_days"] // 30)
    except ImportError:
        pass

    return True


def get_user_subscription(user_id: str) -> Optional[Dict]:
    """사용자 구독 정보 조회"""
    subscriptions = load_subscriptions()
    sub = subscriptions.get(user_id)

    if sub:
        # 만료 확인
        end_date = datetime.fromisoformat(sub["end_date"])
        if datetime.now() > end_date:
            sub["is_active"] = False
            subscriptions[user_id] = sub
            save_subscriptions(subscriptions)

    return sub


def get_user_payments(user_id: str) -> List[Payment]:
    """사용자 결제 내역 조회"""
    payments = load_payments()
    return [Payment(p) for p in payments if p["user_id"] == user_id]


# ============================================
# 카카오페이 결제 플로우
# ============================================
def initiate_kakaopay_payment(user_id: str, product_id: str) -> Optional[str]:
    """카카오페이 결제 시작"""
    payment = create_payment(user_id, product_id, "kakaopay")
    if not payment:
        return None

    product = PRODUCTS[product_id]
    api = KakaoPayAPI()

    result = api.ready(
        partner_order_id=payment.payment_id,
        partner_user_id=user_id,
        item_name=product["name"],
        quantity=1,
        total_amount=product["price"],
    )

    if result:
        # TID 저장
        payments = load_payments()
        for p in payments:
            if p["payment_id"] == payment.payment_id:
                p["metadata"] = {"tid": result["tid"]}
                break
        save_payments(payments)

        return result["redirect_url"]

    return None


def complete_kakaopay_payment(payment_id: str, pg_token: str) -> bool:
    """카카오페이 결제 완료"""
    payment = get_payment(payment_id)
    if not payment or payment.status != "pending":
        return False

    tid = payment.metadata.get("tid", "")
    if not tid:
        return False

    api = KakaoPayAPI()
    result = api.approve(
        tid=tid,
        partner_order_id=payment_id,
        partner_user_id=payment.user_id,
        pg_token=pg_token,
    )

    if result:
        update_payment_status(payment_id, "completed", result["tid"])
        activate_subscription(payment.user_id, payment.product_id)
        return True

    update_payment_status(payment_id, "failed")
    return False


# ============================================
# 토스페이먼츠 결제 플로우
# ============================================
def get_toss_payment_widget_config(user_id: str, product_id: str) -> Optional[Dict]:
    """토스 결제 위젯 설정 반환"""
    payment = create_payment(user_id, product_id, "toss")
    if not payment:
        return None

    product = PRODUCTS[product_id]
    api = TossPaymentsAPI()

    return {
        "client_key": api.get_client_key(),
        "order_id": payment.payment_id,
        "order_name": product["name"],
        "amount": product["price"],
        "customer_name": user_id,
        "success_url": PAYMENT_SUCCESS_URL,
        "fail_url": PAYMENT_FAIL_URL,
    }


def complete_toss_payment(payment_key: str, order_id: str, amount: int) -> bool:
    """토스 결제 완료"""
    payment = get_payment(order_id)
    if not payment or payment.status != "pending":
        return False

    if payment.amount != amount:
        logger.error(f"결제 금액 불일치: {payment.amount} != {amount}")
        return False

    api = TossPaymentsAPI()
    result = api.confirm(
        payment_key=payment_key,
        order_id=order_id,
        amount=amount,
    )

    if result and result["status"] == "DONE":
        update_payment_status(order_id, "completed", payment_key)
        activate_subscription(payment.user_id, payment.product_id)
        return True

    update_payment_status(order_id, "failed")
    return False


# ============================================
# UI 컴포넌트
# ============================================
def render_pricing_page():
    """가격 페이지 렌더링"""
    st.markdown("""
    <style>
    .pricing-container {
        display: flex;
        gap: 24px;
        justify-content: center;
        flex-wrap: wrap;
        margin: 40px 0;
    }
    .pricing-card {
        background: white;
        border-radius: 20px;
        padding: 32px;
        width: 320px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        text-align: center;
        position: relative;
        transition: all 0.3s;
    }
    .pricing-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    .pricing-card.popular {
        border: 2px solid #3b82f6;
    }
    .popular-badge {
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #3b82f6;
        color: white;
        padding: 4px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .pricing-name {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 8px;
    }
    .pricing-price {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1e3a5f;
        margin: 16px 0;
    }
    .pricing-price span {
        font-size: 1rem;
        font-weight: 400;
        color: #64748b;
    }
    .pricing-features {
        list-style: none;
        padding: 0;
        margin: 24px 0;
        text-align: left;
    }
    .pricing-features li {
        padding: 8px 0;
        color: #475569;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .pricing-features li::before {
        content: "✓";
        color: #10b981;
        font-weight: bold;
    }
    .pricing-btn {
        display: block;
        width: 100%;
        padding: 14px;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        text-decoration: none;
        text-align: center;
        transition: all 0.2s;
        cursor: pointer;
        border: none;
    }
    .btn-primary {
        background: #3b82f6;
        color: white;
    }
    .btn-primary:hover {
        background: #2563eb;
    }
    .btn-secondary {
        background: #f1f5f9;
        color: #1e3a5f;
    }
    .btn-secondary:hover {
        background: #e2e8f0;
    }
    .yearly-toggle {
        text-align: center;
        margin-bottom: 24px;
    }
    .yearly-toggle label {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        font-size: 0.9rem;
        color: #475569;
    }
    .yearly-discount {
        background: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center; color:#1e3a5f;'>요금제 선택</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b;'>목표 달성에 맞는 플랜을 선택하세요</p>", unsafe_allow_html=True)

    # 월간/연간 토글
    is_yearly = st.toggle("연간 결제 (37% 할인)", value=False)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="pricing-card">
            <div class="pricing-name">무료</div>
            <div class="pricing-price">₩0<span>/월</span></div>
            <ul class="pricing-features">
                <li>일일 AI 면접 연습 3회</li>
                <li>기본 피드백</li>
                <li>진도 관리</li>
                <li>항공사 퀴즈</li>
            </ul>
            <div class="pricing-btn btn-secondary">현재 플랜</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        price = "₩149,000<span>/년</span>" if is_yearly else "₩19,900<span>/월</span>"
        product_id = "standard_yearly" if is_yearly else "standard_monthly"

        st.markdown(f"""
        <div class="pricing-card popular">
            <div class="popular-badge">가장 인기</div>
            <div class="pricing-name">스탠다드</div>
            <div class="pricing-price">{price}</div>
            <ul class="pricing-features">
                <li>일일 AI 면접 연습 30회</li>
                <li>심층 AI 피드백</li>
                <li>자소서 첨삭 무제한</li>
                <li>음성 분석</li>
                <li>합격자 DB 열람</li>
                <li>우선 고객 지원</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("스탠다드 시작하기", key="btn_standard", use_container_width=True):
            st.session_state["selected_product"] = product_id
            st.session_state["show_payment_modal"] = True

    with col3:
        price = "₩299,000<span>/년</span>" if is_yearly else "₩39,900<span>/월</span>"
        product_id = "premium_yearly" if is_yearly else "premium_monthly"

        st.markdown(f"""
        <div class="pricing-card">
            <div class="pricing-name">프리미엄</div>
            <div class="pricing-price">{price}</div>
            <ul class="pricing-features">
                <li>모든 기능 무제한</li>
                <li>1:1 멘토 매칭</li>
                <li>자소서 완전 첨삭</li>
                <li>영상 면접 분석</li>
                <li>표정/음성 종합 분석</li>
                <li>합격 보장 프로그램</li>
                <li>전담 매니저 배정</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("프리미엄 시작하기", key="btn_premium", use_container_width=True):
            st.session_state["selected_product"] = product_id
            st.session_state["show_payment_modal"] = True


def render_payment_modal():
    """결제 모달 렌더링"""
    if not st.session_state.get("show_payment_modal"):
        return

    product_id = st.session_state.get("selected_product", "")
    if product_id not in PRODUCTS:
        return

    product = PRODUCTS[product_id]

    st.markdown("""
    <style>
    .payment-modal {
        background: white;
        border-radius: 20px;
        padding: 32px;
        max-width: 500px;
        margin: 0 auto;
        box-shadow: 0 8px 40px rgba(0,0,0,0.15);
    }
    .payment-header {
        text-align: center;
        margin-bottom: 24px;
    }
    .payment-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    .payment-amount {
        font-size: 2rem;
        font-weight: 800;
        color: #3b82f6;
        margin: 16px 0;
    }
    .payment-method-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;
        padding: 16px;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.2s;
        border: 2px solid #e2e8f0;
        background: white;
    }
    .payment-method-btn:hover {
        border-color: #3b82f6;
        background: #f8fafc;
    }
    .kakao-btn {
        background: #FEE500;
        border-color: #FEE500;
        color: #000;
    }
    .toss-btn {
        background: #0064FF;
        border-color: #0064FF;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown(f"""
        <div class="payment-modal">
            <div class="payment-header">
                <div class="payment-title">결제하기</div>
                <div style="color:#64748b; margin-top:8px;">{product['name']}</div>
                <div class="payment-amount">₩{product['price']:,}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 결제 수단 선택")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("카카오페이", key="pay_kakao", use_container_width=True):
                user = st.session_state.get("user")
                if user:
                    redirect_url = initiate_kakaopay_payment(user.user_id, product_id)
                    if redirect_url:
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={redirect_url}">', unsafe_allow_html=True)
                else:
                    st.error("로그인이 필요합니다.")

        with col2:
            if st.button("토스페이먼츠", key="pay_toss", use_container_width=True):
                user = st.session_state.get("user")
                if user:
                    config = get_toss_payment_widget_config(user.user_id, product_id)
                    if config:
                        st.session_state["toss_config"] = config
                        st.info("토스 결제 위젯이 로드됩니다...")
                else:
                    st.error("로그인이 필요합니다.")

        if st.button("취소", use_container_width=True):
            st.session_state["show_payment_modal"] = False
            st.rerun()


def render_toss_payment_widget():
    """토스 결제 위젯 렌더링"""
    config = st.session_state.get("toss_config")
    if not config:
        return

    toss_widget_html = f"""
    <script src="https://js.tosspayments.com/v1/payment-widget"></script>
    <div id="payment-widget"></div>
    <script>
        const clientKey = "{config['client_key']}";
        const paymentWidget = PaymentWidget(clientKey, PaymentWidget.ANONYMOUS);

        paymentWidget.renderPaymentMethods("#payment-widget", {{
            value: {config['amount']},
            currency: "KRW"
        }});

        async function requestPayment() {{
            await paymentWidget.requestPayment({{
                orderId: "{config['order_id']}",
                orderName: "{config['order_name']}",
                successUrl: "{config['success_url']}",
                failUrl: "{config['fail_url']}",
            }});
        }}
    </script>
    <button onclick="requestPayment()" style="
        background: #0064FF;
        color: white;
        padding: 14px 32px;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        margin-top: 16px;
    ">결제하기</button>
    """

    st.components.v1.html(toss_widget_html, height=500)


def render_payment_history():
    """결제 내역 렌더링"""
    user = st.session_state.get("user")
    if not user:
        st.warning("로그인이 필요합니다.")
        return

    payments = get_user_payments(user.user_id)

    if not payments:
        st.info("결제 내역이 없습니다.")
        return

    st.markdown("### 결제 내역")

    for payment in reversed(payments):
        product = PRODUCTS.get(payment.product_id, {})
        status_color = "#10b981" if payment.status == "completed" else "#ef4444" if payment.status == "failed" else "#f59e0b"
        status_text = "완료" if payment.status == "completed" else "실패" if payment.status == "failed" else "대기중"

        st.markdown(f"""
        <div style="background:white; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:600; color:#1e3a5f;">{product.get('name', '상품')}</div>
                    <div style="font-size:0.85rem; color:#64748b;">{payment.created_at[:10]}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700; color:#1e3a5f;">₩{payment.amount:,}</div>
                    <div style="font-size:0.85rem; color:{status_color}; font-weight:600;">{status_text}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================
# 콜백 핸들러
# ============================================
def handle_payment_callback():
    """결제 콜백 처리"""
    query_params = st.query_params

    # 카카오페이 콜백
    if query_params.get("method") == "kakaopay":
        pg_token = query_params.get("pg_token")
        order_id = query_params.get("order_id")

        if pg_token and order_id:
            if complete_kakaopay_payment(order_id, pg_token):
                st.success("결제가 완료되었습니다!")
                st.balloons()
            else:
                st.error("결제 처리 중 오류가 발생했습니다.")

            st.query_params.clear()
            return True

    # 토스 콜백
    payment_key = query_params.get("paymentKey")
    order_id = query_params.get("orderId")
    amount = query_params.get("amount")

    if payment_key and order_id and amount:
        if complete_toss_payment(payment_key, order_id, int(amount)):
            st.success("결제가 완료되었습니다!")
            st.balloons()
        else:
            st.error("결제 처리 중 오류가 발생했습니다.")

        st.query_params.clear()
        return True

    return False
