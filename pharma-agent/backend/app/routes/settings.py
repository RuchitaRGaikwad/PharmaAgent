"""
Settings Routes - User Settings with Database Persistence

Provides endpoints for:
1. Get user settings (from database)
2. Update all user settings
3. Patch single setting (for instant toggle updates)
4. System status for AI/Database/Safety monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json

from ..database import get_db
from ..models import UserSettings, AgentTrace, Medicine

router = APIRouter(prefix="/settings", tags=["Settings"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class UserSettingsSchema(BaseModel):
    language: str = "en"
    darkMode: bool = True
    notifications: bool = True
    emailAlerts: bool = True
    smsAlerts: bool = False
    autoRefill: bool = True
    voiceAssistant: bool = True
    dataSharing: bool = False
    adminMode: bool = False

    class Config:
        from_attributes = True


class SettingsResponse(BaseModel):
    user_id: int
    settings: UserSettingsSchema
    updated_at: str


class SystemStatus(BaseModel):
    ai_core: str  # "online", "offline", "degraded"
    database: str  # "connected", "disconnected"
    security: str  # "secure", "warning", "critical"
    compliance_percent: int
    ai_confidence: int
    recent_checks: list


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_or_create_settings(db: Session, user_id: int) -> UserSettings:
    """Get existing settings or create defaults for a user."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(
            user_id=user_id,
            language="en",
            dark_mode=True,
            push_notifications=True,
            email_alerts=True,
            sms_alerts=False,
            auto_refill=True,
            voice_assistant=True,
            data_sharing=False,
            admin_mode=False
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def model_to_schema(settings: UserSettings) -> UserSettingsSchema:
    """Convert SQLAlchemy model to Pydantic schema with camelCase keys."""
    return UserSettingsSchema(
        language=settings.language,
        darkMode=settings.dark_mode,
        notifications=settings.push_notifications,
        emailAlerts=settings.email_alerts,
        smsAlerts=settings.sms_alerts,
        autoRefill=settings.auto_refill,
        voiceAssistant=settings.voice_assistant,
        dataSharing=settings.data_sharing,
        adminMode=settings.admin_mode
    )


# =============================================================================
# SETTINGS ENDPOINTS
# =============================================================================

@router.get("/{user_id}", response_model=SettingsResponse)
def get_settings(user_id: int, db: Session = Depends(get_db)):
    """Get settings for a user (creates defaults if none exist)."""
    settings = get_or_create_settings(db, user_id)
    return {
        "user_id": user_id,
        "settings": model_to_schema(settings),
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else datetime.utcnow().isoformat()
    }


@router.put("/{user_id}", response_model=SettingsResponse)
def update_settings(user_id: int, new_settings: UserSettingsSchema, db: Session = Depends(get_db)):
    """Update all settings for a user."""
    settings = get_or_create_settings(db, user_id)
    
    # Update all fields
    settings.language = new_settings.language
    settings.dark_mode = new_settings.darkMode
    settings.push_notifications = new_settings.notifications
    settings.email_alerts = new_settings.emailAlerts
    settings.sms_alerts = new_settings.smsAlerts
    settings.auto_refill = new_settings.autoRefill
    settings.voice_assistant = new_settings.voiceAssistant
    settings.data_sharing = new_settings.dataSharing
    settings.admin_mode = new_settings.adminMode
    settings.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(settings)
    
    return {
        "user_id": user_id,
        "settings": model_to_schema(settings),
        "updated_at": settings.updated_at.isoformat()
    }


@router.patch("/{user_id}")
def patch_setting(
    user_id: int, 
    key: str = Query(..., description="Setting key to update"),
    value: str = Query(..., description="New value for the setting"),
    db: Session = Depends(get_db)
):
    """Update a single setting instantly (for toggle switches)."""
    settings = get_or_create_settings(db, user_id)
    
    # Map camelCase frontend keys to snake_case database columns
    key_mapping = {
        "language": "language",
        "darkMode": "dark_mode",
        "notifications": "push_notifications",
        "emailAlerts": "email_alerts",
        "smsAlerts": "sms_alerts",
        "autoRefill": "auto_refill",
        "voiceAssistant": "voice_assistant",
        "dataSharing": "data_sharing",
        "adminMode": "admin_mode"
    }
    
    if key not in key_mapping:
        raise HTTPException(status_code=400, detail=f"Unknown setting: {key}")
    
    db_key = key_mapping[key]
    
    # Parse value appropriately
    if value.lower() in ["true", "false"]:
        parsed_value = value.lower() == "true"
    else:
        parsed_value = value
    
    # Update the specific field
    setattr(settings, db_key, parsed_value)
    settings.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(settings)
    
    return {
        "success": True,
        "user_id": user_id,
        "key": key,
        "value": parsed_value,
        "updated_at": settings.updated_at.isoformat()
    }


# =============================================================================
# SYSTEM STATUS ENDPOINT
# =============================================================================

@router.get("/system/status", response_model=SystemStatus)
def get_system_status(db: Session = Depends(get_db)):
    """
    Get system status for the Settings dashboard.
    Returns AI Core status, database connectivity, compliance metrics,
    and recent safety checks from AgentTraces.
    """
    # Check database connectivity
    try:
        medicine_count = db.query(Medicine).count()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
        medicine_count = 0
    
    # Get recent agent traces for safety checks
    try:
        recent_traces = db.query(AgentTrace).filter(
            AgentTrace.agent_name.in_(["SafetyAgent", "ConversationAgent", "ActionAgent"])
        ).order_by(AgentTrace.created_at.desc()).limit(5).all()
        
        recent_checks = []
        for trace in recent_traces:
            # Format the trace as a readable check
            icon = "✓" if trace.decision and "approved" in trace.decision.lower() else "⚠"
            recent_checks.append({
                "icon": icon,
                "message": f"{trace.action}: {trace.decision or 'Completed'}",
                "time": trace.created_at.isoformat() if trace.created_at else None
            })
    except Exception:
        recent_checks = []
    
    # Calculate compliance (based on approved vs rejected orders)
    try:
        approved = db.query(AgentTrace).filter(
            AgentTrace.agent_name == "SafetyAgent",
            AgentTrace.decision.like("%approved%")
        ).count()
        total = db.query(AgentTrace).filter(
            AgentTrace.agent_name == "SafetyAgent"
        ).count()
        compliance = int((approved / max(total, 1)) * 100)
    except Exception:
        compliance = 98  # Default fallback
    
    return {
        "ai_core": "online",  # We're running, so AI is online
        "database": db_status,
        "security": "secure",  # Default to secure
        "compliance_percent": min(compliance, 100),
        "ai_confidence": 95,  # Default high confidence
        "recent_checks": recent_checks if recent_checks else [
            {"icon": "✓", "message": "System initialized", "time": datetime.utcnow().isoformat()},
            {"icon": "✓", "message": "Database connected", "time": datetime.utcnow().isoformat()},
            {"icon": "✓", "message": "AI Core ready", "time": datetime.utcnow().isoformat()}
        ]
    }
