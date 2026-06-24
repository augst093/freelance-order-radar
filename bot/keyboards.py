from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from storage.models import Opportunity

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Returns the persistent main menu reply keyboard."""
    keyboard = [
        [KeyboardButton(text="🔍 Scan Now"), KeyboardButton(text="📊 Status")],
        [KeyboardButton(text="🔥 Hot Offers"), KeyboardButton(text="📑 Latest")],
        [KeyboardButton(text="⭐ Saved"), KeyboardButton(text="💼 Portfolio")],
        [KeyboardButton(text="⚙️ Settings"), KeyboardButton(text="❓ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_opportunity_keyboard(opp: Opportunity) -> InlineKeyboardMarkup:
    """
    Returns the action buttons layout for a specific freelance order.
    Buttons:
    [Open Order] [Copy Reply]
    [Save] [Skip] [Mark as Applied]
    [Generate Better Reply] [Show Details]
    """
    builder = InlineKeyboardBuilder()
    
    # 1. Primary actions
    builder.row(
        InlineKeyboardButton(text="🔗 Open Order", url=opp.url),
        InlineKeyboardButton(text="📋 Copy Reply", callback_data=f"copy_{opp.id}")
    )
    
    # 2. Status operations
    status_buttons = []
    if opp.status != "saved":
        status_buttons.append(InlineKeyboardButton(text="⭐ Save", callback_data=f"save_{opp.id}"))
    if opp.status != "skipped":
        status_buttons.append(InlineKeyboardButton(text="❌ Skip", callback_data=f"skip_{opp.id}"))
    if opp.status != "applied":
        status_buttons.append(InlineKeyboardButton(text="✅ Applied", callback_data=f"apply_{opp.id}"))
        
    builder.row(*status_buttons)
    
    # 3. Utilities
    builder.row(
        InlineKeyboardButton(text="✍️ Better Reply", callback_data=f"regen_{opp.id}"),
        InlineKeyboardButton(text="📄 Show Details", callback_data=f"details_{opp.id}")
    )
    
    return builder.as_markup()

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Returns the main settings menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📡 Sources Configuration", callback_data="set_sources"),
        InlineKeyboardButton(text="✍️ Reply Style", callback_data="set_reply_style")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Profile Text", callback_data="set_profile"),
        InlineKeyboardButton(text="🔑 Keywords Management", callback_data="set_keywords")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Notification Rules", callback_data="set_rules")
    )
    return builder.as_markup()

def get_reply_style_keyboard(current_style: str) -> InlineKeyboardMarkup:
    """Returns options to pick a reply tone/style."""
    styles = [
        ("confident", "Confident (Default)"),
        ("casual", "Casual/Friendly"),
        ("short", "Short/Direct"),
        ("premium", "Premium/Expert"),
        ("aggressive but polite", "Aggressive but Polite")
    ]
    
    builder = InlineKeyboardBuilder()
    for key, label in styles:
        # Highlight current active style
        mark = "🔹 " if key == current_style else ""
        builder.row(InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"style_{key}"))
        
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_settings"))
    return builder.as_markup()

def get_sources_keyboard(sources: list[dict]) -> InlineKeyboardMarkup:
    """Returns a toggle list of sources."""
    builder = InlineKeyboardBuilder()
    for src in sources:
        enabled_icon = "🟢" if src["enabled"] == 1 else "🔴"
        name = src["name"].upper()
        builder.row(
            InlineKeyboardButton(text=f"{enabled_icon} {name}", callback_data=f"toggle_src_{src['name']}")
        )
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_settings"))
    return builder.as_markup()

def get_keywords_menu_keyboard() -> InlineKeyboardMarkup:
    """Inline menu to manage keywords."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Add Keyword", callback_data="add_keyword_prompt"),
        InlineKeyboardButton(text="➖ Remove Keyword", callback_data="remove_keyword_prompt")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Show Keywords", callback_data="show_keywords_list")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_settings"))
    return builder.as_markup()

def get_yes_no_keyboard(prefix: str, opp_id: int) -> InlineKeyboardMarkup:
    """General confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Yes", callback_data=f"{prefix}_yes_{opp_id}"),
        InlineKeyboardButton(text="No", callback_data=f"{prefix}_no_{opp_id}")
    )
    return builder.as_markup()
