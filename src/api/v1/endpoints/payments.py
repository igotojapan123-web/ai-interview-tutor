"""
Payment endpoints.

Handles payments and subscriptions.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.api.v1.deps import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    payment_service
)
from src.services.payment_service import PaymentService
from src.core.models.payment import PaymentMethod, PaymentCreate, PaymentCallback
from src.core.models.user import User
from src.core.exceptions import NotFoundError, PaymentError, RefundError

router = APIRouter()


# =====================
# Request/Response Schemas
# =====================

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: float
    original_price: Optional[float]
    features: List[str]
    tier: str
    billing_cycle: str


class PaymentInitiateRequest(BaseModel):
    product_id: str
    payment_method: str


class PaymentInitiateResponse(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    redirect_url: str


class PaymentCallbackRequest(BaseModel):
    order_id: str
    status: str
    provider_transaction_id: Optional[str] = None
    receipt_url: Optional[str] = None
    raw_data: Optional[dict] = None


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    product_id: str
    amount: float
    status: str
    payment_method: str
    created_at: str
    receipt_url: Optional[str]


class SubscriptionResponse(BaseModel):
    id: str
    tier: str
    billing_cycle: str
    starts_at: str
    expires_at: str
    is_active: bool
    auto_renew: bool


class RefundRequest(BaseModel):
    amount: Optional[float] = None
    reason: str = "Customer request"


# =====================
# Endpoints
# =====================

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    payment_svc: PaymentService = Depends(payment_service)
):
    """List all available products."""
    products = payment_svc.get_products()
    return [
        ProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            price=float(p.price),
            original_price=float(p.original_price) if p.original_price else None,
            features=p.features,
            tier=p.tier.value,
            billing_cycle=p.billing_cycle.value
        )
        for p in products.values()
    ]


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    payment_svc: PaymentService = Depends(payment_service)
):
    """Get product details."""
    try:
        product = payment_svc.get_product(product_id)
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=float(product.price),
            original_price=float(product.original_price) if product.original_price else None,
            features=product.features,
            tier=product.tier.value,
            billing_cycle=product.billing_cycle.value
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: PaymentInitiateRequest,
    current_user: User = Depends(get_current_active_user),
    payment_svc: PaymentService = Depends(payment_service)
):
    """Initiate a payment."""
    try:
        payment_method = PaymentMethod(request.payment_method)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method: {request.payment_method}"
        )

    try:
        payment_data = PaymentCreate(
            user_id=current_user.id,
            product_id=request.product_id,
            payment_method=payment_method
        )
        result = payment_svc.initiate_payment(payment_data)
        return PaymentInitiateResponse(
            payment_id=result["payment_id"],
            order_id=result["order_id"],
            amount=result["amount"],
            redirect_url=result["redirect_url"]
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )


@router.post("/callback")
async def payment_callback(
    request: PaymentCallbackRequest,
    payment_svc: PaymentService = Depends(payment_service)
):
    """Process payment callback from gateway."""
    try:
        callback_data = PaymentCallback(
            order_id=request.order_id,
            status=request.status,
            provider_transaction_id=request.provider_transaction_id,
            receipt_url=request.receipt_url,
            raw_data=request.raw_data
        )
        payment = payment_svc.process_callback(callback_data)
        return {"status": payment.status.value, "message": "Callback processed"}
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )


@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_active_user),
    payment_svc: PaymentService = Depends(payment_service)
):
    """Get current user's payment history."""
    payments = payment_svc.get_user_payments(current_user.id)
    return [
        PaymentResponse(
            id=p.id,
            order_id=p.order_id,
            product_id=p.product_id,
            amount=float(p.amount),
            status=p.status.value,
            payment_method=p.payment_method.value,
            created_at=p.created_at.isoformat(),
            receipt_url=p.receipt_url
        )
        for p in payments
    ]


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    payment_svc: PaymentService = Depends(payment_service)
):
    """Get current user's subscription."""
    subscription = payment_svc.get_user_subscription(current_user.id)
    if not subscription:
        return None

    return SubscriptionResponse(
        id=subscription.id,
        tier=subscription.tier.value,
        billing_cycle=subscription.billing_cycle.value,
        starts_at=subscription.starts_at.isoformat(),
        expires_at=subscription.expires_at.isoformat(),
        is_active=subscription.is_active,
        auto_renew=subscription.auto_renew
    )


@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    payment_svc: PaymentService = Depends(payment_service)
):
    """Cancel current user's subscription."""
    subscription = payment_svc.cancel_subscription(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    return {"message": "Subscription cancelled. Access until " + subscription.expires_at.isoformat()}


@router.post("/{payment_id}/refund")
async def request_refund(
    payment_id: str,
    request: RefundRequest,
    current_user: User = Depends(get_current_active_user),
    payment_svc: PaymentService = Depends(payment_service)
):
    """Request refund for a payment."""
    try:
        # Verify ownership
        payment = payment_svc.get_payment(payment_id)
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )

        refund_amount = Decimal(str(request.amount)) if request.amount else None
        payment = payment_svc.refund_payment(
            payment_id,
            amount=refund_amount,
            reason=request.reason
        )
        return {"message": "Refund processed", "status": payment.status.value}
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    except RefundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================
# Admin Endpoints
# =====================

@router.get("/stats")
async def get_payment_stats(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    admin_user: User = Depends(get_admin_user),
    payment_svc: PaymentService = Depends(payment_service)
):
    """Get payment statistics (admin only)."""
    return payment_svc.get_stats(start_date, end_date)
