from typing import Dict, List, Any

def format_summary(user_totals: Dict[str, float], extras_info: Dict, warnings: List[str], participants: List[Any] = None) -> str:
    """
    Turns the split calculation output into a readable Telegram message.
    """
    if not user_totals:
        return "Calculation resulted in no shares. Check if anyone claimed items!"
        
    lines = ["🧾 **Final Bill Split Summary** 🧾\n"]
    
    if extras_info["total_extras"] > 0 and extras_info["num_users"] > 0:
        lines.append(f"ℹ️ **Tax & Service Charge (RM {extras_info['total_extras']:.2f}) was split evenly among {extras_info['num_users']} people (RM {extras_info['extras_per_person']:.2f} each).**\n")
    
    total_bill = 0.0
    
    # Map user IDs to display names if available
    name_map = {}
    if participants:
        name_map = {p.telegram_user_id: (p.display_name or f"User {p.telegram_user_id}") for p in participants}
        
    for user_id, amount in user_totals.items():
        display_name = name_map.get(user_id, f"User {user_id}")
        lines.append(f"• {display_name} owes: RM {amount:.2f}")
        total_bill += amount
        
    lines.append(f"\n**Total Reconciled:** RM {total_bill:.2f}")
    
    if warnings:
        lines.append("\n⚠️ **Warnings / Unresolved Items:**")
        for w in warnings:
            lines.append(f"- {w}")
            
    lines.append("\n_(Pay the person who uploaded the receipt!)_")
    
    return "\n".join(lines)
