from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, Profile, ActivityLog
from app.schemas.user import ProfileOut, ProfileUpdate
from app.api.deps import get_current_user, log_activity

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileOut)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return current_user.profile


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    data = update.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)

    log_activity(db, current_user.id, "profile", "profile_updated", data)
    return profile


@router.get("/activity")
def get_my_activity(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Read-only view of this user's full behavioral history across all modules."""
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "module": log.module,
            "action": log.action,
            "payload": log.payload,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]
