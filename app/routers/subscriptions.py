from fastapi import APIRouter, Depends, Form
from sqlmodel import select

from ..database import get_session
from ..dependencies import get_current_user
from ..models import Subscription, SubscriptionTier, User

router = APIRouter()


@router.post("/subscriptions/change")
def change_subscription(
    tier: SubscriptionTier = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    subscription = session.exec(select(Subscription).where(Subscription.user_id == user.id)).first()
    if not subscription:
        subscription = Subscription(user_id=user.id, tier=tier)
    subscription.tier = tier
    subscription.max_accounts = 1 if tier == SubscriptionTier.FREE else (5 if tier == SubscriptionTier.PRO else 20)
    session.add(subscription)
    session.commit()
    return {"message": "Subscription updated", "tier": tier}
