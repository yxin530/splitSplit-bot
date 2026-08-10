import logging
import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler, PollAnswerHandler

from agents.state_manager import create_new_session, get_active_session, cancel_session
from agents.receipt_classifier import is_highlighted
from agents.ocr_agent import extract_receipt_data
from agents.poll_manager import generate_poll, handle_poll_answer
from agents.split_calculator import calculate_split
from agents.color_mapper import prompt_color_mapping, handle_color_claim
from agents.summary_formatter import format_summary
from database.db import SessionLocal
from database.models import Item, Vote, Session

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Add me to a group and send a receipt photo to split a bill.",
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the active session in this chat."""
    chat_id = str(update.effective_chat.id)
    cancelled = cancel_session(chat_id)
    if cancelled:
        await update.message.reply_text("The current bill splitting session has been cancelled.")
    else:
        await update.message.reply_text("There is no active session to cancel.")

async def calculate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger calculation of the current active session based on poll votes."""
    chat_id = str(update.effective_chat.id)
    active_session = get_active_session(chat_id)
    
    if not active_session:
        await update.message.reply_text("No active session to calculate. Send a receipt first.")
        return
        
    db = SessionLocal()
    try:
        items = db.query(Item).filter(Item.session_id == active_session.id).all()
        votes = db.query(Vote).filter(Vote.session_id == active_session.id).all()
        # Query participants explicitly instead of using detached session relationship
        from database.models import Participant
        participants = db.query(Participant).filter(Participant.session_id == active_session.id).all()
        
        user_totals, extras_info, warnings = calculate_split(
            items=items,
            votes=votes,
            tax=active_session.tax,
            service_charge=active_session.service_charge,
            participants=participants
        )
        
        summary_text = format_summary(user_totals, extras_info, warnings, participants)
        await update.message.reply_text(summary_text)
        
        # Mark session as calculated
        active_session.status = 'calculated'
        db.commit()
    finally:
        db.close()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle receipt photo uploads."""
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    
    # Only allow one active session per chat (simplified for now, v2 can support multiple)
    active_session = get_active_session(chat_id)
    if active_session:
        await update.message.reply_text("There's already an active session in this chat. Finish or /cancel it first.")
        return

    # Grab the highest resolution photo (if sent as photo) or the document (if sent as file)
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
    else:
        photo_file = await update.message.document.get_file()
    
    # Save the photo temporarily
    os.makedirs("temp_receipts", exist_ok=True)
    file_path = f"temp_receipts/{photo_file.file_id}.jpg"
    await photo_file.download_to_drive(file_path)

    # Acknowledge receipt
    msg = await update.message.reply_text("Receipt received! Processing...")
    
    # Create DB session
    session = create_new_session(chat_id, user_id, file_path)

    # Classification
    highlighted = is_highlighted(file_path)
    session_type = "highlighted" if highlighted else "plain"
    
    # Update status message
    await msg.edit_text(f"Detected as **{session_type}** receipt. Extracting items using Gemini...")

    # OCR extraction
    extracted_data = extract_receipt_data(file_path)
    
    if not extracted_data or not extracted_data.get("items"):
        await msg.edit_text("Sorry, I couldn't extract items from this receipt. Try another photo or a clearer angle.")
        return

    # Save items to Database
    db = SessionLocal()
    saved_items_data = []
    try:
        # Update session with tax and service charge
        db_session = db.query(Session).filter(Session.id == session.id).first()
        if db_session:
            db_session.tax = extracted_data.get("tax", 0.0) or 0.0
            db_session.service_charge = extracted_data.get("service_charge", 0.0) or 0.0
            db_session.subtotal = extracted_data.get("subtotal", 0.0) or 0.0
            db_session.total = extracted_data.get("total", 0.0) or 0.0
            
        for it in extracted_data["items"]:
            new_item = Item(
                session_id=session.id,
                name=it.get("name", "Unknown"),
                quantity=it.get("quantity", 1),
                unit_price=it.get("unit_price", 0.0),
                line_total=it.get("line_total", 0.0),
                highlight_color=it.get("highlight_color")
            )
            db.add(new_item)
            db.flush() # Flush to populate new_item.id
            
            # Store in a plain dictionary to safely pass outside the DB session
            saved_items_data.append({
                "id": new_item.id,
                "name": new_item.name,
                "quantity": new_item.quantity,
                "unit_price": new_item.unit_price,
                "line_total": new_item.line_total,
                "highlight_color": new_item.highlight_color
            })
        db.commit()
    finally:
        db.close()

    # For plain receipts, generate a poll
    if session_type == "plain":
        await msg.edit_text("Extracted successfully! Generating poll for group members...")
        await generate_poll(update, context, saved_items_data, session.id)
    else:
        # Highlighted flows map colors to users
        distinct_colors = set(item.get('highlight_color') for item in extracted_data['items'] if item.get('highlight_color'))
        
        if distinct_colors:
            items_text = "\n".join([f"- {item.get('quantity', 1)}x {item.get('name')} (RM {item.get('line_total')}) [{item.get('highlight_color', 'none')}]" for item in extracted_data['items']])
            await msg.edit_text(f"Highlighted receipt detected! Found colors: {', '.join(filter(None, distinct_colors))}\n\nItems:\n{items_text}")
            await prompt_color_mapping(update, context, list(distinct_colors), session.id)
        else:
            # False positive! Classifier thought it was highlighted, but OCR found no colors. Fallback to normal poll.
            await msg.edit_text("Extracted successfully! (Generating normal poll as no specific highlights were found)...")
            await generate_poll(update, context, saved_items_data, session.id)

def setup_handlers(application) -> None:
    """Register all handlers to the application."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("calculate", calculate_command))
    # Listen for photos AND document images (files)
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    application.add_handler(CallbackQueryHandler(handle_color_claim))
