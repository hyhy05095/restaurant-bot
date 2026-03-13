import streamlit as st
from agents import function_tool, AgentHooks, Agent, Tool, RunContextWrapper
from models import UserAccountContext
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# =============================================================================
# MENU SUPPORT TOOLS
# =============================================================================


@function_tool
def get_menu_items(context: UserAccountContext, category: Optional[str] = None) -> str:
    """
    Retrieve menu items with prices and descriptions.
    
    Args:
        category: Menu category (kimbap, rice, noodles, side_dishes, drinks)
    """
    menu = {
        "kimbap": [
            "🍙 오리지널 김밥 - 3,500원 (야채, 계란, 단무지)",
            "🐟 참치 김밥 - 4,000원 (참치 마요, 야채)",
            "🥩 소고기 김밥 - 4,500원 (양념 소고기, 야채)",
            "🌱 야채 김밥 - 3,000원 (신선한 야채만 사용)",
            "🧀 치즈 김밥 - 4,000원 (모짜렐라 치즈, 야채)",
        ],
        "rice": [
            "🍳 김치볶음밥 - 6,500원 (매콤한 김치, 계란, 야채)",
            "🥩 소고기볶음밥 - 7,500원 (양념 소고기, 계란, 야채)",
            "🍤 새우볶음밥 - 8,000원 (새우, 계란, 야채)",
            "🌶️ 제육덮밥 - 7,000원 (고추장 돼지고기, 야채)",
        ],
        "noodles": [
            "🍜 라면 - 4,500원 (클래식 라면)",
            "🧀 치즈라면 - 5,500원 (모짜렐라 치즈 추가)",
            "🥟 만두라면 - 6,000원 (야채 만두 추가)",
            "🌶️ 비빔냉면 - 7,000원 (매콤한 비빔냉면)",
        ],
        "side_dishes": [
            "🍢 떡볶이 - 5,000원 (매콤한 양념)",
            "🥟 군만두 - 4,000원 (6개, 야채/고기)",
            "🍳 계란말이 - 3,500원 (한국식 계란말이)",
            "🥗 한국식 샐러드 - 3,000원 (참깨 드레싱)",
        ],
        "drinks": [
            "🥤 한국식 소다 - 2,000원 (다양한 맛)",
            "☕ 아이스커피 - 2,500원 (한국식 달달한 커피)",
            "🍵 녹차 - 2,000원 (핫/아이스)",
            "🥛 바나나우유 - 2,500원 (바나나맛 우유)",
        ]
    }
    
    if category and category in menu:
        items = menu[category]
        return f"📋 {category.title()} 메뉴:\n" + "\n".join(items)
    elif not category:
        all_items = []
        for cat, items in menu.items():
            all_items.append(f"\n📍 {cat.upper()}:")
            all_items.extend(items)
        return "🍱 김밥천국 전체 메뉴:" + "\n".join(all_items)
    else:
        return f"❌ '{category}' 카테고리를 찾을 수 없습니다. 가능한 카테고리: kimbap, rice, noodles, side_dishes, drinks"


@function_tool
def check_ingredient_info(context: UserAccountContext, dish_name: str) -> str:
    """
    Check ingredients and allergen information for specific dishes.
    
    Args:
        dish_name: Name of the dish to check ingredients
    """
    ingredients_db = {
        "original kimbap": {
            "ingredients": ["rice", "seaweed", "carrot", "spinach", "egg", "pickled radish", "sesame oil"],
            "allergens": ["egg", "sesame"],
            "vegetarian": False,
            "spicy": False
        },
        "vegetable kimbap": {
            "ingredients": ["rice", "seaweed", "carrot", "spinach", "cucumber", "pickled radish", "sesame oil"],
            "allergens": ["sesame"],
            "vegetarian": True,
            "spicy": False
        },
        "kimchi fried rice": {
            "ingredients": ["rice", "kimchi", "egg", "green onion", "sesame oil", "gochujang"],
            "allergens": ["egg", "sesame"],
            "vegetarian": False,
            "spicy": True
        },
        "tteokbokki": {
            "ingredients": ["rice cakes", "gochujang", "fish cake", "green onion", "sugar", "garlic"],
            "allergens": ["fish", "garlic"],
            "vegetarian": False,
            "spicy": True
        }
    }
    
    dish_key = dish_name.lower()
    if dish_key in ingredients_db:
        info = ingredients_db[dish_key]
        return f"""
🍽️ Ingredient Information for {dish_name.title()}:
📝 Ingredients: {', '.join(info['ingredients'])}
⚠️ Allergens: {', '.join(info['allergens']) if info['allergens'] else 'None'}
🌱 Vegetarian: {'Yes' if info['vegetarian'] else 'No'}
🌶️ Spicy: {'Yes' if info['spicy'] else 'No'}
        """.strip()
    else:
        return f"❌ Ingredient information for '{dish_name}' not found. Please ask staff for details."


@function_tool
def get_daily_specials(context: UserAccountContext) -> str:
    """
    Get today's special menu items and promotions.
    """
    day = datetime.now().strftime("%A")
    specials = {
        "Monday": "🎯 Kimbap Combo: Any 2 kimbap + drink for $8.99",
        "Tuesday": "🍜 Ramen Tuesday: All ramen 20% off",
        "Wednesday": "🥟 Dumpling Day: Free dumplings with any rice dish",
        "Thursday": "🌶️ Spicy Thursday: Tteokbokki + Spicy Ramen combo $8.50",
        "Friday": "🎉 TGIF Special: 15% off all orders over $20",
        "Saturday": "👨‍👩‍👧‍👦 Family Pack: 4 kimbap + 2 ramen + 4 drinks for $25",
        "Sunday": "☕ Brunch Special: Any kimbap + coffee for $5.00"
    }
    
    premium_bonus = "\n🌟 Premium Member Bonus: Additional 10% off!" if context.is_premium_customer() else ""
    
    return f"""
📅 Today's Special ({day}):
{specials[day]}
{premium_bonus}
⏰ Valid all day while supplies last
    """.strip()


@function_tool
def check_dietary_options(context: UserAccountContext, dietary_type: str) -> str:
    """
    Find menu items suitable for specific dietary requirements.
    
    Args:
        dietary_type: Type of dietary requirement (vegetarian, vegan, gluten_free, no_garlic, halal)
    """
    dietary_options = {
        "vegetarian": [
            "🌱 Vegetable Kimbap - $3.00",
            "🧀 Cheese Kimbap - $4.00 (without ham)",
            "🥗 Korean Salad - $3.00",
            "🍳 Egg Roll - $3.50",
            "🥟 Vegetable Dumplings - $4.00"
        ],
        "vegan": [
            "🌱 Vegetable Kimbap - $3.00 (without egg)",
            "🥗 Korean Salad - $3.00 (without egg)",
            "🍵 Green Tea - $2.00",
            "🌶️ Kimchi (side) - $2.00"
        ],
        "gluten_free": [
            "🍙 All Kimbap varieties (rice-based)",
            "🍳 Egg Roll - $3.50",
            "🥗 Korean Salad - $3.00",
            "Most rice dishes (ask about sauce)"
        ],
        "no_garlic": [
            "🍙 Original Kimbap - $3.50",
            "🧀 Cheese Kimbap - $4.00",
            "🍳 Egg Roll - $3.50",
            "🥗 Korean Salad - $3.00"
        ],
        "halal": [
            "🌱 Vegetable Kimbap - $3.00",
            "🐟 Tuna Kimbap - $4.00",
            "🍤 Shrimp Fried Rice - $8.00",
            "All vegetarian options"
        ]
    }
    
    diet_key = dietary_type.lower().replace(" ", "_")
    if diet_key in dietary_options:
        options = dietary_options[diet_key]
        return f"""
🍽️ {dietary_type.title()} Options Available:
""" + "\n".join(options) + """

💡 Note: Please inform staff about your dietary requirements when ordering.
📞 We can customize some dishes upon request!
        """
    else:
        return f"❌ Dietary category '{dietary_type}' not recognized. Available: vegetarian, vegan, gluten_free, no_garlic, halal"


# =============================================================================
# ORDER SUPPORT TOOLS
# =============================================================================


@function_tool
def create_order(
    context: UserAccountContext, 
    items: List[str], 
    special_requests: Optional[str] = None
) -> str:
    """
    Create a new order for the customer.
    
    Args:
        items: List of items to order
        special_requests: Any special preparation requests
    """
    order_id = f"ORD-{random.randint(100000, 999999)}"
    
    # Simple price calculation (would be more complex in real system)
    item_count = len(items)
    estimated_total = item_count * 5.50  # Average price
    
    return f"""
✅ Order Created Successfully!
📋 Order ID: {order_id}
🛒 Items: {', '.join(items)}
💬 Special requests: {special_requests if special_requests else 'None'}
👤 Customer: {context.name}
💰 Estimated total: ${estimated_total:.2f}
⏱️ Preparation time: 10-15 minutes
    """.strip()


@function_tool
def calculate_order_total(
    context: UserAccountContext, 
    items_json: str,   # "{"Original Kimbap": 3.50, "Ramen": 4.50}" 형태
    apply_discount: bool = True
) -> str:
    """
    Calculate the total price for an order including applicable discounts.
    
    Args:
        items_json: JSON string of item names and their prices e.g. '{"Original Kimbap": 3.50}'
        apply_discount: Whether to apply membership discount
    """
    import json
    try:
        items = json.loads(items_json)
    except Exception:
        items = {}

    subtotal = sum(items.values())
    tax_rate = 0.08
    tax = subtotal * tax_rate

    discount = 0
    if apply_discount and context.is_premium_customer():
        discount = subtotal * 0.10

    membership_points = int((subtotal - discount) * 0.03 * 100)
    total = subtotal + tax - discount

    return f"""
💰 Order Total Calculation:
━━━━━━━━━━━━━━━━━━━━━
📝 Subtotal: ${subtotal:.2f}
📊 Tax (8%): ${tax:.2f}
{'🎯 Premium Discount (10%): -$' + f'{discount:.2f}' if discount > 0 else ''}
━━━━━━━━━━━━━━━━━━━━━
💵 Total: ${total:.2f}
🎁 Points Earned: {membership_points} pts
    """.strip()


@function_tool
def apply_membership_discount(
    context: UserAccountContext, 
    order_total: float
) -> str:
    """
    Apply membership benefits and calculate points earned.
    
    Args:
        order_total: Original order total before discount
    """
    if context.tier == "premium":
        discount_rate = 0.10
        points_rate = 0.05
    elif context.tier == "gold":
        discount_rate = 0.15
        points_rate = 0.07
    else:
        discount_rate = 0.0
        points_rate = 0.03
    
    discount_amount = order_total * discount_rate
    final_total = order_total - discount_amount
    points_earned = int(final_total * points_rate * 100)
    
    return f"""
🎯 Membership Benefits Applied:
👤 Member: {context.name} ({context.tier.title()})
💳 Original Total: ${order_total:.2f}
🎁 Discount ({int(discount_rate*100)}%): -${discount_amount:.2f}
💰 Final Total: ${final_total:.2f}
⭐ Points Earned: {points_earned} pts
📊 Total Points Balance: {random.randint(500, 2000)} pts
    """.strip()


@function_tool
def process_payment(
    context: UserAccountContext,
    order_id: str,
    payment_method: str,
    amount: float
) -> str:
    """
    Process payment for an order.
    
    Args:
        order_id: Order ID to process payment for
        payment_method: Payment method (card, cash, mobile_pay)
        amount: Payment amount
    """
    transaction_id = f"TXN-{random.randint(100000, 999999)}"
    
    payment_status = "approved" if payment_method != "cash" else "pending"
    
    return f"""
💳 Payment Processing:
━━━━━━━━━━━━━━━━━━━━━
📋 Order ID: {order_id}
💰 Amount: ${amount:.2f}
💳 Method: {payment_method.replace('_', ' ').title()}
🔖 Transaction ID: {transaction_id}
✅ Status: {payment_status.title()}
{'🧾 Please pay at counter' if payment_method == 'cash' else '📧 Receipt sent to: ' + context.email}
    """.strip()


@function_tool
def check_order_status(context: UserAccountContext, order_id: str) -> str:
    """
    Check the current status of an order.
    
    Args:
        order_id: Order ID to check status
    """
    statuses = ["received", "preparing", "ready", "completed"]
    current_status = random.choice(statuses)
    
    status_emoji = {
        "received": "📝",
        "preparing": "👨‍🍳",
        "ready": "✅",
        "completed": "🎉"
    }
    
    time_estimates = {
        "received": "10-15 minutes",
        "preparing": "5-10 minutes",
        "ready": "Ready for pickup!",
        "completed": "Thank you!"
    }
    
    return f"""
📦 Order Status Update:
━━━━━━━━━━━━━━━━━━━━━
📋 Order ID: {order_id}
{status_emoji[current_status]} Status: {current_status.upper()}
⏱️ Time: {time_estimates[current_status]}
📍 Location: Kimbap Heaven Main Kitchen
{'🔔 We\'ll notify you when ready!' if current_status != 'ready' else '🔔 Your order is ready for pickup!'}
    """.strip()


# =============================================================================
# RESERVATION SUPPORT TOOLS
# =============================================================================


@function_tool
def check_table_availability(
    context: UserAccountContext,
    date: str,
    time: str,
    party_size: int
) -> str:
    """
    Check table availability for requested date and time.
    
    Args:
        date: Requested date (YYYY-MM-DD)
        time: Requested time (HH:MM)
        party_size: Number of people
    """
    # Simulate availability check
    available_times = []
    requested_hour = int(time.split(':')[0])
    
    for i in range(-1, 2):
        hour = requested_hour + i
        if 11 <= hour <= 21:  # Restaurant hours
            if random.random() > 0.3:  # 70% chance of availability
                available_times.append(f"{hour}:00")
                available_times.append(f"{hour}:30")
    
    is_available = time in available_times
    
    return f"""
🗓️ Table Availability Check:
━━━━━━━━━━━━━━━━━━━━━
📅 Date: {date}
⏰ Requested Time: {time}
👥 Party Size: {party_size} people
{'✅ AVAILABLE' if is_available else '❌ FULLY BOOKED'}

📍 Available times nearby:
""" + "\n".join([f"  • {t}" for t in available_times[:6]]) + f"""

{'🌟 Premium members get priority seating!' if context.is_premium_customer() else '💡 Tip: Book in advance for weekend slots!'}
    """


@function_tool
def create_reservation(
    context: UserAccountContext,
    date: str,
    time: str,
    party_size: int,
    special_requests: Optional[str] = None
) -> str:
    """
    Create a table reservation.
    
    Args:
        date: Reservation date (YYYY-MM-DD)
        time: Reservation time (HH:MM)
        party_size: Number of people
        special_requests: Special seating or dietary requests
    """
    reservation_id = f"RES-{random.randint(100000, 999999)}"
    deposit_required = 10.0 if party_size >= 6 else 0
    
    # Premium customers get private dining area for large groups
    seating_area = "Private Dining Room" if context.is_premium_customer() and party_size >= 6 else "Main Dining Area"
    
    return f"""
✅ Reservation Confirmed!
━━━━━━━━━━━━━━━━━━━━━
🎫 Reservation ID: {reservation_id}
👤 Name: {context.name}
📅 Date: {date}
⏰ Time: {time}
👥 Party Size: {party_size} people
📍 Seating: {seating_area}
{'💬 Special Requests: ' + special_requests if special_requests else ''}
{'💰 Deposit Required: $' + f'{deposit_required:.2f}' if deposit_required > 0 else '✨ No deposit required'}
📧 Confirmation sent to: {context.email}

⚠️ Cancellation Policy:
• Free cancellation up to 24 hours before
• 50% charge for same-day cancellation
    """.strip()


@function_tool
def modify_reservation(
    context: UserAccountContext,
    reservation_id: str,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
    new_party_size: Optional[int] = None
) -> str:
    """
    Modify an existing reservation.
    
    Args:
        reservation_id: Existing reservation ID
        new_date: New date if changing
        new_time: New time if changing
        new_party_size: New party size if changing
    """
    changes = []
    if new_date:
        changes.append(f"📅 Date → {new_date}")
    if new_time:
        changes.append(f"⏰ Time → {new_time}")
    if new_party_size:
        changes.append(f"👥 Party size → {new_party_size}")
    
    return f"""
✏️ Reservation Modified Successfully!
━━━━━━━━━━━━━━━━━━━━━
🎫 Reservation ID: {reservation_id}
👤 Customer: {context.name}

📝 Changes Made:
""" + "\n".join(changes) + """

✅ Modification confirmed
📧 Updated confirmation sent to: {context.email}
{'🌟 Premium member - no modification fees!' if context.is_premium_customer() else ''}
    """.strip()


@function_tool
def cancel_reservation(
    context: UserAccountContext,
    reservation_id: str
) -> str:
    """
    Cancel a reservation and process any applicable refunds.
    
    Args:
        reservation_id: Reservation ID to cancel
    """
    # Simulate checking reservation details
    hours_until_reservation = random.randint(1, 48)
    had_deposit = random.choice([True, False])
    deposit_amount = 10.0 if had_deposit else 0
    
    if hours_until_reservation >= 24:
        refund_amount = deposit_amount
        cancellation_fee = 0
    else:
        refund_amount = deposit_amount * 0.5
        cancellation_fee = deposit_amount * 0.5
    
    return f"""
❌ Reservation Cancelled
━━━━━━━━━━━━━━━━━━━━━
🎫 Reservation ID: {reservation_id}
⏱️ Time until reservation: {hours_until_reservation} hours
{'💰 Deposit refund: $' + f'{refund_amount:.2f}' if had_deposit else '✨ No deposit was required'}
{'📊 Cancellation fee: $' + f'{cancellation_fee:.2f}' if cancellation_fee > 0 else '✅ No cancellation fee'}
{'💳 Refund will be processed in 3-5 business days' if refund_amount > 0 else ''}
📧 Cancellation confirmation sent to: {context.email}
    """.strip()


@function_tool
def process_reservation_deposit(
    context: UserAccountContext,
    reservation_id: str,
    amount: float = 10.0
) -> str:
    """
    Process deposit payment for a reservation.
    
    Args:
        reservation_id: Reservation ID
        amount: Deposit amount (default $10)
    """
    transaction_id = f"DEP-{random.randint(100000, 999999)}"
    
    return f"""
💳 Reservation Deposit Processed
━━━━━━━━━━━━━━━━━━━━━
🎫 Reservation ID: {reservation_id}
💰 Deposit Amount: ${amount:.2f}
🔖 Transaction ID: {transaction_id}
✅ Status: Confirmed
📧 Receipt sent to: {context.email}

ℹ️ Deposit Information:
• Applied to final bill on arrival
• Fully refundable if cancelled 24hrs+ before
• 50% refundable for late cancellations
    """.strip()


# =============================================================================
# COMPLAINTS SUPPORT TOOLS
# =============================================================================


@function_tool
def create_complaint_ticket(
    context: UserAccountContext,
    complaint_type: str,
    description: str
) -> str:
    """
    Create a formal complaint ticket for tracking and resolution.
    
    Args:
        complaint_type: Type of complaint (food_quality, service, cleanliness, billing)
        description: Detailed description of the issue
    """
    ticket_id = f"CMP-{random.randint(100000, 999999)}"
    priority = "HIGH" if context.is_premium_customer() else "MEDIUM"
    
    response_time = "2 hours" if context.is_premium_customer() else "24 hours"
    
    return f"""
📝 Complaint Ticket Created
━━━━━━━━━━━━━━━━━━━━━
🎫 Ticket ID: {ticket_id}
👤 Customer: {context.name}
📋 Type: {complaint_type.replace('_', ' ').title()}
⚡ Priority: {priority}
📝 Issue: {description}
⏱️ Expected Response: Within {response_time}
📧 Updates will be sent to: {context.email}

We sincerely apologize for this experience and will address it immediately.
    """.strip()


@function_tool
def process_refund(
    context: UserAccountContext,
    order_id: str,
    amount: float,
    reason: str
) -> str:
    """
    Process a refund for a customer complaint.
    
    Args:
        order_id: Order ID for refund
        amount: Refund amount
        reason: Reason for refund
    """
    refund_id = f"REF-{random.randint(100000, 999999)}"
    processing_days = 3 if context.is_premium_customer() else 5
    
    return f"""
💰 Refund Processed
━━━━━━━━━━━━━━━━━━━━━
🎫 Refund ID: {refund_id}
📋 Order ID: {order_id}
💵 Amount: ${amount:.2f}
📝 Reason: {reason}
⏱️ Processing Time: {processing_days} business days
💳 Refund Method: Original payment method
📧 Confirmation sent to: {context.email}

We apologize for the inconvenience and appreciate your understanding.
    """.strip()


@function_tool
def issue_compensation(
    context: UserAccountContext,
    compensation_type: str,
    value: float
) -> str:
    """
    Issue compensation such as coupons or account credits.
    
    Args:
        compensation_type: Type of compensation (coupon, credit, free_meal)
        value: Value of compensation
    """
    comp_id = f"COMP-{random.randint(100000, 999999)}"
    expiry_days = 90 if context.is_premium_customer() else 60
    
    compensation_details = {
        "coupon": f"🎟️ Discount Coupon: ${value:.2f} off next order",
        "credit": f"💳 Account Credit: ${value:.2f} added to account",
        "free_meal": f"🍱 Free Meal Voucher: Up to ${value:.2f} value"
    }
    
    return f"""
🎁 Compensation Issued
━━━━━━━━━━━━━━━━━━━━━
🎫 Compensation ID: {comp_id}
{compensation_details.get(compensation_type, f"🎁 Compensation: ${value:.2f}")}
⏰ Valid for: {expiry_days} days
👤 Issued to: {context.name}
📧 Details sent to: {context.email}

Thank you for giving us the opportunity to make this right!
    """.strip()


@function_tool
def escalate_to_manager(
    context: UserAccountContext,
    ticket_id: str,
    reason: str
) -> str:
    """
    Escalate a complaint to restaurant management.
    
    Args:
        ticket_id: Complaint ticket ID
        reason: Reason for escalation
    """
    manager_name = random.choice(["Sarah Kim", "James Park", "Michelle Lee"])
    callback_time = "30 minutes" if context.is_premium_customer() else "2 hours"
    
    return f"""
⬆️ Escalated to Management
━━━━━━━━━━━━━━━━━━━━━
🎫 Ticket ID: {ticket_id}
👔 Assigned Manager: {manager_name}
📝 Escalation Reason: {reason}
📞 Callback Time: Within {callback_time}
📱 Contact Number: On file
{'🌟 Premium Priority Handling' if context.is_premium_customer() else ''}

Our management team takes all concerns seriously and will contact you directly.
    """.strip()


@function_tool
def log_hygiene_issue(
    context: UserAccountContext,
    location: str,
    issue_type: str,
    action_taken: str
) -> str:
    """
    Log and document hygiene or cleanliness issues.
    
    Args:
        location: Location of issue (dining_area, kitchen, restroom)
        issue_type: Type of hygiene issue
        action_taken: Immediate action taken
    """
    incident_id = f"HYG-{random.randint(100000, 999999)}"
    
    return f"""
🧹 Hygiene Issue Logged
━━━━━━━━━━━━━━━━━━━━━
🎫 Incident ID: {incident_id}
📍 Location: {location.replace('_', ' ').title()}
⚠️ Issue Type: {issue_type}
✅ Action Taken: {action_taken}
👤 Reported by: {context.name}
🕐 Logged at: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔧 Follow-up Actions:
• Immediate cleaning scheduled
• Staff retraining if needed
• Health & Safety team notified
• Compensation offered for inconvenience

Thank you for bringing this to our attention. We maintain the highest standards of cleanliness.
    """.strip()


# =============================================================================
# COMMON TOOLS (Used by multiple agents)
# =============================================================================


@function_tool
def get_customer_history(context: UserAccountContext) -> str:
    """
    Retrieve customer's order and visit history.
    """
    # Simulate customer history
    recent_orders = []
    for i in range(3):
        days_ago = random.randint(1, 30)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        order_amount = random.uniform(15, 50)
        recent_orders.append(f"  • {order_date}: ${order_amount:.2f}")
    
    visit_count = random.randint(10, 50)
    total_spent = visit_count * random.uniform(20, 40)
    favorite_item = random.choice(["Original Kimbap", "Kimchi Fried Rice", "Tuna Kimbap", "Cheese Ramen"])
    
    return f"""
👤 Customer Profile: {context.name}
━━━━━━━━━━━━━━━━━━━━━
🏆 Membership Tier: {context.tier.title()}
📧 Email: {context.email}
🎯 Customer ID: {context.customer_id}

📊 Visit Statistics:
• Total Visits: {visit_count}
• Total Spent: ${total_spent:.2f}
• Average Order: ${total_spent/visit_count:.2f}
• Favorite Item: {favorite_item}

📋 Recent Orders:
""" + "\n".join(recent_orders) + f"""

{'🌟 Valued Premium Customer' if context.is_premium_customer() else '💡 Upgrade to Premium for exclusive benefits!'}
    """


@function_tool
def send_confirmation_email(
    context: UserAccountContext,
    confirmation_type: str,
    details_json: str,  
) -> str:
    """
    Send confirmation emails for various transactions.
    
    Args:
        confirmation_type: Type of confirmation (order, reservation, refund, complaint)
        details_json: JSON string containing relevant details e.g. '{"order_id": "ORD-123"}'
    """
    import json
    try:
        details = json.loads(details_json)
    except Exception:
        details = {}

    email_id = f"EMAIL-{random.randint(100000, 999999)}"

    subject_lines = {
        "order": "Your Kimbap Heaven Order Confirmation",
        "reservation": "Your Table Reservation is Confirmed",
        "refund": "Refund Processed - Kimbap Heaven",
        "complaint": "We've Received Your Feedback"
    }

    return f"""
📧 Email Confirmation Sent
━━━━━━━━━━━━━━━━━━━━━
🔖 Email ID: {email_id}
📬 To: {context.email}
📋 Subject: {subject_lines.get(confirmation_type, 'Kimbap Heaven Confirmation')}
✅ Status: Delivered
📎 Includes: {', '.join(details.keys()) if details else 'N/A'}

Check your email for complete details.
{'📱 SMS notification also sent' if context.is_premium_customer() else ''}
    """.strip()


# =============================================================================
# AGENT HOOKS FOR LOGGING
# =============================================================================


class AgentToolUsageLoggingHooks(AgentHooks):
    """Hooks for logging tool usage in the Streamlit sidebar."""

    async def on_tool_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** starting tool: `{tool.name}`")

    async def on_tool_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
        result: str,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** used tool: `{tool.name}`")
            with st.expander("Tool Result", expanded=False):
                st.code(result)

    async def on_handoff(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        source: Agent[UserAccountContext],
    ):
        with st.sidebar:
            st.write(f"🔄 Handoff: **{source.name}** → **{agent.name}**")

    async def on_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
    ):
        with st.sidebar:
            st.write(f"🚀 **{agent.name}** activated")

    async def on_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        output,
    ):
        with st.sidebar:
            st.write(f"🏁 **{agent.name}** completed")