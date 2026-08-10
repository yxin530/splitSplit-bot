import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.db import SessionLocal
from database.models import Item, Vote, Participant, Session

logger = logging.getLogger(__name__)

async def generate_poll(update: Update, context: ContextTypes.DEFAULT_TYPE, items: list, session_id: int):
    """
    Creates a Telegram poll from the list of extracted items.
    """
    if not items:
        return
        
    options = []
    item_id_map = []
    # If quantity > 1, expand into separate options
    for item in items:
        # Check if item is a dictionary (fallback) or an object
        if isinstance(item, dict):
            qty = item.get("quantity", 1)
            name = item.get("name", "Unknown Item")
            price = item.get("unit_price", 0.0)
            item_id = item.get("id", 0) # Might be missing
        else:
            qty = item.quantity
            name = item.name
            price = item.unit_price
            item_id = item.id
            
        if qty > 1:
            for i in range(qty):
                options.append(f"{name} ({i+1} of {qty}) - RM {price:.2f}")
                item_id_map.append(item_id)
        else:
            options.append(f"{name} - RM {price:.2f}")
            item_id_map.append(item_id)

    if len(options) > 10:
        await update.message.reply_text("Warning: Too many items for a single Telegram poll. Showing first 10.")
        options = options[:10]
        item_id_map = item_id_map[:10]

    if not options:
        return

    message = await update.message.reply_poll(
        question="Select the items you ordered:",
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True
    )
    
    # Store poll ID in context to track votes mapped to real DB item IDs
    context.bot_data[message.poll.id] = {
        "session_id": session_id,
        "item_map": item_id_map
    }
    return message.poll.id

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tracks votes when a user answers the poll.
    """
    answer = update.poll_answer
    poll_id = answer.poll_id
    user_id = str(answer.user.id)
    selected_option_ids = answer.option_ids
    
    poll_data = context.bot_data.get(poll_id)
    if not poll_data:
        return # Poll not tracked by this bot or session ended
        
    session_id = poll_data["session_id"]
    item_map = poll_data["item_map"]
        
    db = SessionLocal()
    try:
        # Save or update participant name
        participant = db.query(Participant).filter(
            Participant.session_id == session_id,
            Participant.telegram_user_id == user_id
        ).first()
        
        if not participant:
            participant = Participant(
                session_id=session_id,
                telegram_user_id=user_id,
                display_name=answer.user.first_name
            )
            db.add(participant)
        else:
            participant.display_name = answer.user.first_name
            
        # Remove old votes for this user in this poll since Telegram sends full current selection
        db.query(Vote).filter(
            Vote.session_id == session_id,
            Vote.telegram_user_id == user_id
        ).delete()
        
        # Add new votes mapping to actual DB item_ids
        for opt_id in selected_option_ids:
            if opt_id < len(item_map):
                actual_item_id = item_map[opt_id]
                new_vote = Vote(
                    session_id=session_id,
                    item_id=actual_item_id,
                    telegram_user_id=user_id
                )
                db.add(new_vote)
        db.commit()
        
        # Check if all items are claimed for auto-calculation
        items = db.query(Item).filter(Item.session_id == session_id).all()
        all_votes = db.query(Vote).filter(Vote.session_id == session_id).all()
        
        claimed_item_ids = set(v.item_id for v in all_votes)
        all_item_ids = set(i.id for i in items)
        
        if all_item_ids and claimed_item_ids.issuperset(all_item_ids):
            # All items have been claimed!
            session = db.query(Session).filter(Session.id == session_id).first()
            if session.status != 'calculated':
                from agents.split_calculator import calculate_split
                from agents.summary_formatter import format_summary
                
                participants = db.query(Participant).filter(Participant.session_id == session_id).all()
                user_totals, extras_info, warnings = calculate_split(
                    items=items,
                    votes=all_votes,
                    tax=session.tax,
                    service_charge=session.service_charge,
                    participants=participants
                )
                
                summary_text = format_summary(user_totals, extras_info, warnings, participants)
                
                # Send the auto-calculated summary to the original chat
                await context.bot.send_message(
                    chat_id=session.chat_id,
                    text=f"✨ **All items have been claimed! Auto-calculating...** ✨\n\n" + summary_text
                )
                
                session.status = 'calculated'
                db.commit()
                
    finally:
        db.close()
