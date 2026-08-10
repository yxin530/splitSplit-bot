import logging
from database.db import SessionLocal
from database.models import Session

logger = logging.getLogger(__name__)

def create_new_session(chat_id: str, created_by: str, image_url: str):
    db = SessionLocal()
    try:
        new_session = Session(
            chat_id=chat_id,
            created_by=created_by,
            image_url=image_url,
            status='processing'
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    finally:
        db.close()

def get_active_session(chat_id: str):
    db = SessionLocal()
    try:
        # Looking for sessions that aren't cancelled or fully calculated
        active = db.query(Session).filter(
            Session.chat_id == chat_id,
            Session.status.in_(['processing', 'awaiting_input', 'open'])
        ).first()
        return active
    finally:
        db.close()

def cancel_session(chat_id: str) -> bool:
    db = SessionLocal()
    try:
        active = db.query(Session).filter(
            Session.chat_id == chat_id,
            Session.status.in_(['processing', 'awaiting_input', 'open'])
        ).first()
        
        if active:
            active.status = 'cancelled'
            db.commit()
            return True
        return False
    finally:
        db.close()
