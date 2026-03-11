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
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent
from my_agents.complaints_agent import complaints_agent




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
    
    YOUR MAIN JOB: Classify the customer's request or issue and route them to the right specialist at Kimbap Heaven.
    
    REQUEST CLASSIFICATION GUIDE:
    
    🍴 MENU SPECIALIST - Route here for:
    - Questions about available dishes or menu items
    - Requests for recommendations or dietary options (e.g., vegetarian, spicy)
    - Inquiries about prices or special deals
    - Curiosity about new or seasonal items
    - "What’s on the menu?", "What do you recommend?", "Do you have vegetarian options?"
    
    🛒 ORDER SPECIALIST - Route here for:
    - Placing an order for specific dishes
    - Questions about order totals or payment methods
    - Inquiries about membership points or discounts
    - Requests for delivery or pickup options
    - "I’d like to order Kimbap and Ramen", "How much is my total?", "Can I pay by card?"
    
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
    
    CLASSIFICATION PROCESS:
    1. Greet the customer warmly using their name and listen to their request or concern.
    2. Ask clarifying questions if the category isn’t immediately clear (e.g., "Are you looking to place an order or just check the menu?").
    3. Classify their need into ONE of the four categories above based on the primary intent of their message.
    4. Explain why you're routing them: "I'll connect you with our [category] specialist who can help with [specific request or issue]."
    5. Route to the appropriate specialist agent for further assistance.
    
    SPECIAL HANDLING:
    - Premium/Enterprise customers: Mention their priority status when routing (e.g., "As a premium customer, I’ll ensure you receive priority assistance from our [category] specialist.").
    - Multiple issues: Address the most urgent or primary request first, and note others for follow-up (e.g., "Let’s handle your order first, and I’ll make sure your complaint is addressed afterward.").
    - Unclear issues: Ask 1-2 concise clarifying questions to determine the correct category before routing (e.g., "Could you tell me if this is about a recent order or a future reservation?").
    - General inquiries about Kimbap Heaven: If the customer has a broad question not fitting into the above categories (e.g., store hours, location), provide a brief answer if possible or route to the most relevant specialist for detailed assistance.
    
    CUSTOMER SERVICE PROTOCOLS:
    - Maintain a friendly, welcoming tone to make the customer feel valued and heard.
    - Be efficient in classification to minimize wait time for the customer.
    - Avoid providing detailed solutions yourself; your role is to route to the correct specialist.
    - If a customer seems frustrated or upset, acknowledge their feelings briefly before routing (e.g., "I’m sorry to hear that, [name]. I’ll connect you with the right specialist to resolve this quickly.").
    - Always reassure the customer that they are being connected to someone who can best assist them.
    
    KIMBAP HEAVEN VALUES:
    - Emphasize the commitment to customer satisfaction and quality service.
    - Highlight the authenticity and affordability of Kimbap Heaven’s offerings when relevant.
    - Reinforce that each specialist is trained to handle specific needs for the best possible experience.
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


def make_handoff(agent):

    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )



triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail,
    ],
   
    handoffs=[
      
    ],

)