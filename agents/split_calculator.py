import logging
from typing import Dict, List, Tuple
from collections import defaultdict
from database.models import Item, Vote

logger = logging.getLogger(__name__)

def calculate_split(items: List[Item], votes: List[Vote], tax: float, service_charge: float, participants: List = None) -> Tuple[Dict[str, float], Dict, List[str]]:
    """
    Calculates how much each user owes.
    Returns a tuple of (user_shares_dict, extras_info_dict, warnings_list)
    """
    warnings = []
    user_subtotals = defaultdict(float)
    
    # Map item_id to list of user_ids who voted for it
    item_votes = defaultdict(list)
    for vote in votes:
        item_votes[vote.item_id].append(vote.telegram_user_id)
        
    total_receipt_subtotal = 0.0

    for item in items:
        total_receipt_subtotal += item.line_total
        
        # Determine voters: either from explicit Votes table, or mapped via color
        voters = item_votes.get(item.id, [])
        if not voters and item.highlight_color and participants:
            # Map the color to a user
            mapped_user = next((p.telegram_user_id for p in participants if p.highlight_color == item.highlight_color), None)
            if mapped_user:
                voters = [mapped_user]
                
        if not voters:
            warnings.append(f"No one claimed: {item.name} (RM {item.line_total:.2f})")
            continue
            
        # Split item cost among voters
        num_voters = len(voters)
        split_amount = item.line_total / num_voters
        
        for user_id in voters:
            user_subtotals[user_id] += split_amount

    # Distribute tax and service charge EVENLY among all participants
    total_extras = tax + service_charge
    user_totals = {}
    num_users = len(user_subtotals)
    
    extras_per_person = 0.0
    if num_users > 0:
        extras_per_person = total_extras / num_users
        for user_id, subtotal in user_subtotals.items():
            user_totals[user_id] = subtotal + extras_per_person
    else:
        warnings.append("No one claimed any items, cannot distribute charges.")
        user_totals = dict(user_subtotals)
        
    # Reconcile rounding
    user_totals_rounded = {user: round(amt, 2) for user, amt in user_totals.items()}
    
    sum_rounded = sum(user_totals_rounded.values())
    target_total = total_receipt_subtotal + total_extras
    
    diff = round(target_total - sum_rounded, 2)
    
    if diff != 0 and user_totals_rounded:
        # Give the remainder (e.g. 0.01 or -0.01) to the person with the largest share
        largest_share_user = max(user_totals_rounded, key=user_totals_rounded.get)
        user_totals_rounded[largest_share_user] = round(user_totals_rounded[largest_share_user] + diff, 2)
        
    extras_info = {
        "tax": tax,
        "service_charge": service_charge,
        "total_extras": total_extras,
        "num_users": num_users,
        "extras_per_person": extras_per_person
    }

    return user_totals_rounded, extras_info, warnings
