import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import UserAccountContext, InputGuardRailOutput, HandoffData
from my_agents.complaints_agent import complaints_agent
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent

from handoffs import make_handoff


input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    Ensure the user's request specifically pertains to Menu inquiries, Order inquiries, reservation inqiries, and is not off-topic. If the request is off-topic, return a reason for the tripwire. You can make small conversation with the user, specially at the beginning of the conversation, but don't help with requests that are not related to Menu inquiries, Order inquiries, or reservation inqiries.
""",
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )






def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    You are a Customer Service Triage Agent helping at Kimbap Heaven. Your role is to assist customers by understanding their needs and connecting them to the appropriate specialist.
    You call customers by their name.
    
    The customer's name is {wrapper.context.name}.
    The customer's email is {wrapper.context.email}.
    The customer's tier is {wrapper.context.tier}.
    
    YOUR MAIN JOB: Classify the customer's request and IMMEDIATELY route them to the right specialist.
    
    ⚡ CRITICAL RULE: If the customer's intent is clear, DO NOT ask clarifying questions.
    IMMEDIATELY transfer to the appropriate specialist without asking for confirmation.
    Only ask clarifying questions if the request is genuinely ambiguous (e.g., cannot determine category at all).
    
    REQUEST CLASSIFICATION GUIDE:
    
    🍴 MENU SPECIALIST - Route here for:
    - Questions about available dishes or menu items
    - Requests for recommendations or dietary options (e.g., vegetarian, spicy, no garlic, no onion)
    - Inquiries about prices or special deals
    - Curiosity about new or seasonal items
    - ANY food recommendation requests
    - "What's on the menu?", "What do you recommend?", "Do you have vegetarian options?"
    
    🛒 ORDER SPECIALIST - Route here for:
    - Placing an order for specific dishes
    - Questions about order totals or payment methods
    - Inquiries about membership points or discounts
    - Requests for delivery or pickup options
    - "I'd like to order Kimbap and Ramen", "How much is my total?", "Can I pay by card?"
    
    📅 RESERVATION SPECIALIST - Route here for:
    - Requests to book a table for a specific date, time, or number of people
    - Questions about reservation policies or deposit requirements
    - Inquiries about private rooms or event bookings
    - Modifications or cancellations of existing reservations
    - "Can I reserve a table for tomorrow?", "How much is the deposit?", "I need to cancel my booking"
    
    😔 COMPLAINTS SPECIALIST - Route here for:
    - Complaints about food quality, service, or hygiene
    - Issues with incorrect orders or billing errors
    - Dissatisfaction with wait times or staff behavior
    - Requests for refunds, replacements, or compensation
    - "My food was cold", "I was overcharged", "The service was terrible"
    
    HANDOFF PROCESS:
    1. Greet the customer briefly using their name (only on first message).
    2. Identify the category from the message.
    3. ⚡ IMMEDIATELY call the handoff function — do NOT ask "would you like me to transfer you?" or "is this correct?".
    4. Only say 1 short sentence like "I'll connect you with our Menu Specialist right away!" before transferring.
    
    EXAMPLES OF IMMEDIATE HANDOFF (no clarifying questions needed):
    - "양파, 마늘이 없는 메뉴 추천해줘" → IMMEDIATELY handoff to Menu Specialist
    - "건강한 음식 추천해줘" → IMMEDIATELY handoff to Menu Specialist
    - "내일 3시에 예약하고 싶어" → IMMEDIATELY handoff to Reservation Specialist
    - "김밥 주문할게" → IMMEDIATELY handoff to Order Specialist
    - "음식이 차가웠어" → IMMEDIATELY handoff to Complaints Specialist
    
    SPECIAL HANDLING:
    - Premium/Enterprise customers: Mention their priority status when routing.
    - Multiple issues: Address the most urgent or primary request first.
    - General inquiries (store hours, location): Provide a brief answer directly.
    
    CUSTOMER SERVICE PROTOCOLS:
    - Maintain a friendly, welcoming tone.
    - Be FAST and EFFICIENT — minimize back-and-forth before routing.
    - Never provide detailed solutions yourself; route to the correct specialist.
    - If a customer seems frustrated, briefly acknowledge before routing.
    """


def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):

    with st.sidebar:
        st.write(
            f"""
            Handing off to {input_data.to_agent_name}
            Reason: {input_data.reason}
            Issue Type: {input_data.issue_type}
            Description: {input_data.issue_description}
        """
        )





triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail,
    ],
   
    handoffs=[
        make_handoff(complaints_agent),
        make_handoff(reservation_agent),
        make_handoff(menu_agent),
        make_handoff(order_agent),
    ],

)