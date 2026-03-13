import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

from models import UserAccountContext

from my_agents.triage_agent import triage_agent

from my_agents.agent_registry import setup_agent_handoffs

setup_agent_handoffs()

client = OpenAI()

user_account_ctx = UserAccountContext(
    customer_id=1,
    name="Hana",
    tier="premium",
    email="Hana@gmail.com"
)






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
                        st.write(message["content"][0]["text"].replace("$", "\$"))



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
                        
                        st.write(f"🤖 Transfered from {st.session_state["agent"].name} to {event.new_agent.name}")

                        st.session_state["agent"] = event.new_agent

                        text_placeholder = st.empty()

                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""

        except InputGuardrailTripwireTriggered:
            st.write(
                "죄송해요, 저는 **김밥천국 전용 AI 어시스턴트**라 해당 질문엔 답변드리기 어렵습니다. 🙏\n\n"
                "아래와 같은 내용은 도와드릴 수 있어요:\n"
                "- 🍱 메뉴 추천 및 안내\n"
                "- 🛒 주문 접수 및 결제\n"
                "- 📅 예약 문의\n"
                "- 📢 불만 및 피드백 접수\n\n"
                "김밥천국 관련해서 궁금한 점을 말씀해 주세요!"
    )

        except OutputGuardrailTripwireTriggered:
            st.session_state["text_placeholder"].empty()
            st.write(
                "죄송해요, 저는 **김밥천국 전용 AI 어시스턴트**라 해당 질문엔 답변드리기 어렵습니다. 🙏\n\n"
                "아래와 같은 내용은 도와드릴 수 있어요:\n"
                "- 🍱 메뉴 추천 및 안내\n"
                "- 🛒 주문 접수 및 결제\n"
                "- 📅 예약 문의\n"
                "- 📢 불만 및 피드백 접수\n\n"
                "김밥천국 관련해서 궁금한 점을 말씀해 주세요!"
    )


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









