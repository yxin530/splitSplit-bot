from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database.db import SessionLocal
from database.models import Participant
import logging

logger = logging.getLogger(__name__)

async def prompt_color_mapping(update: Update, context: ContextTypes.DEFAULT_TYPE, colors: list, session_id: int):
    """
    Sends a message with inline buttons for users to claim a color.
    """
    if not colors:
        return

    # Filter out null/None colors
    distinct_colors = set(c.lower() for c in colors if c)
    if not distinct_colors:
        await update.message.reply_text("No distinct highlight colors were found on the items.")
        return

    keyboard = []
    for color in distinct_colors:
        # callback_data format: colorclaim_<session_id>_<color>
        callback_data = f"colorclaim_{session_id}_{color}"
        button = InlineKeyboardButton(f"I am {color.capitalize()}", callback_data=callback_data)
        keyboard.append([button])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Highlighted items detected! Please tap a color below to claim the items highlighted in that color:",
        reply_markup=reply_markup
    )

async def handle_color_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles inline button clicks for color claims.
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("colorclaim_"):
        return

    _, session_id_str, color = data.split("_", 2)
    session_id = int(session_id_str)
    user_id = str(query.from_user.id)
    display_name = query.from_user.first_name

    db = SessionLocal()
    try:
        # Check if someone already claimed this color
        existing = db.query(Participant).filter(
            Participant.session_id == session_id,
            Participant.highlight_color == color
        ).first()

        if existing:
            if existing.telegram_user_id == user_id:
                await query.edit_message_text(text=f"{query.message.text}\n\nYou ({display_name}) already claimed {color.capitalize()}!")
                return
            else:
                # Update claim to the new user (allowing corrections)
                existing.telegram_user_id = user_id
                existing.display_name = display_name
                db.commit()
                await query.message.reply_text(f"{display_name} has taken over the {color.capitalize()} highlight.")
                return

        # Create new participant mapping
        new_participant = Participant(
            session_id=session_id,
            telegram_user_id=user_id,
            display_name=display_name,
            highlight_color=color
        )
        db.add(new_participant)
        db.commit()
        
        await query.message.reply_text(f"✅ {display_name} claimed {color.capitalize()}.")
        
        # NOTE: In a full implementation, we would check if ALL distinct colors have been claimed, 
        # and if so, automatically trigger calculate_split. For simplicity, users can just run /calculate.
        
    finally:
        db.close()
