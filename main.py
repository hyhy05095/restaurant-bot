import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered, handoff

from agents.extensions import handoff_filters 
from models import UserAccountContext, HandoffData

from my_agents.triage_agent import triage_agent
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent
from my_agents.complaints_agent import complaints_agent


client = OpenAI()

user_account_ctx = UserAccountContext(
    customer_id=1,
    name="Hana",
    tier="premium",
    email="Hana@gmail.com"
)




def handle_handoff(wrapper, input_data: HandoffData):
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

# 모든 에이전트에 handoffs 설정
all_agents = [triage_agent, menu_agent, order_agent, reservation_agent, complaints_agent]
for agent in all_agents:
    agent.handoffs = [make_handoff(other_agent) for other_agent in all_agents if other_agent != agent]






if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent

if "current_agent_display" not in st.session_state:
    st.session_state["current_agent_display"] = f"Current Assistant: {triage_agent.name}"



async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        content = message["content"][0]["text"] if isinstance(message["content"], list) else message["content"]
                        st.write(content.replace("$", "\$"))


asyncio.run(paint_history())


async def run_agent(message):

    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""

        st.session_state["text_placeholder"] = text_placeholder

        try:

            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=user_account_ctx,
                
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\$"))
                elif event.type == "agent_updated_stream_event":

                    if st.session_state["agent"].name != event.new_agent.name:
                        if "handoff_count" not in st.session_state: st.session_state["handoff_count"] = 0
                        st.session_state["handoff_count"] += 1
                        if st.session_state["handoff_count"] > 1: continue 
                        st.write(f"🤖 Transferred from {st.session_state['agent'].name} to {event.new_agent.name}")
                        st.session_state["agent"] = event.new_agent
                        st.session_state["current_agent_display"] = f"Current Assistant: {event.new_agent.name}"

                        with st.sidebar:  
                            st.markdown("### Assistant Status")
                            agent_status = st.empty()
                            agent_status.markdown(st.session_state["current_agent_display"])
                        text_placeholder = st.empty()
                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""

        except InputGuardrailTripwireTriggered:
            st.write("I can't help you with that. Your request seems to be off-topic. Please ask something related to Kimbap Heaven's menu, orders, reservations, or complaints.")


message = st.chat_input(
    "Write a message for Kimbap Heaven assistance",
)

if message:
    with st.chat_message("human"):
        st.write(message)
    asyncio.run(run_agent(message))




with st.sidebar:
    st.markdown("### Assistant Status")
    agent_status = st.empty()  
    agent_status.markdown(st.session_state["current_agent_display"])
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
        st.session_state["agent"] = triage_agent
        st.session_state["current_agent_display"] = f"Current Assistant: {triage_agent.name}"
        agent_status.markdown(st.session_state["current_agent_display"])
        st.write("Memory reset completed.")
    st.write(asyncio.run(session.get_items()))









