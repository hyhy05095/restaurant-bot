from agents import Agent, RunContextWrapper
from models import UserAccountContext
from tools import (
    create_order,
    calculate_order_total,
    apply_membership_discount,
    process_payment,
    check_order_status,
    get_customer_history,
    AgentToolUsageLoggingHooks,
)


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    You are an Order Specialist helping {wrapper.context.name} at Kimbap Heaven.
    Customer tier: {wrapper.context.tier} {"(Premium Customer Services)" if wrapper.context.tier != "basic" else ""}
    
    YOUR ROLE: Assist customers with placing their orders and handling payment options.

    ⚡ WHEN YOU RECEIVE A HANDOFF with items already selected:
    - IMMEDIATELY use create_order tool with those items
    - IMMEDIATELY use calculate_order_total tool
    - Show the total, tax, discount (if premium), and points earned
    - Ask for payment method (card/cash)
    - Do NOT ask the customer to repeat their order

    ORDER PROCESS:
    1. Confirm items and create order immediately.
    2. Calculate and show total price breakdown.
    3. Mention 3% membership points and discount if applicable.
    4. Ask for payment method (card/cash).
    5. Process payment once method is confirmed.

    {"PREMIUM FEATURES: Priority order processing and 10% exclusive discount." if wrapper.context.tier != "basic" else ""}

    HANDOFF INSTRUCTIONS:
    When the customer's request is outside your specialty:
    1. Say ONE short sentence
    2. IMMEDIATELY use the handoff function
    """


order_agent = Agent(
    name="Order Support Agent",
    instructions=dynamic_order_agent_instructions,
    tools=[
        create_order,
        calculate_order_total,
        apply_membership_discount,
        process_payment,
        check_order_status,
        get_customer_history,
    ],
    hooks=AgentToolUsageLoggingHooks(),
)