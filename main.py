import dotenv
dotenv.load_dotenv()

from openai import OpenAI
import asyncio
import streamlit as st
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
import pandas as pd
import json
import os

from models import UserAccountContext
from my_agents.triage_agent import triage_agent
from my_agents.agent_registry import setup_agent_handoffs

setup_agent_handoffs()

client = OpenAI()

# ─── 회원 관리 (users.json) ──────────────────────────────────────
USERS_FILE = "users.json"

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user(name: str, tier: str = "basic"):
    users = load_users()
    if name not in users:
        users[name] = {
            "customer_id": len(users) + 1,
            "tier": tier,
            "email": f"{name.lower()}@kimbap.com"
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return False  # 신규 회원
    return True  # 기존 회원

def get_user(name: str) -> UserAccountContext:
    users = load_users()
    u = users[name]
    return UserAccountContext(
        customer_id=u["customer_id"],
        name=name,
        tier=u["tier"],
        email=u["email"]
    )

# ─── 김밥천국 메뉴 데이터 ────────────────────────────────────────
MENU_DATA = {
    "김밥류": [
        {"메뉴": "참치김밥", "가격": "3,500원", "칼로리": "420kcal", "추천": "⭐"},
        {"메뉴": "치즈김밥", "가격": "3,500원", "칼로리": "450kcal", "추천": "⭐"},
        {"메뉴": "소고기김밥", "가격": "4,500원", "칼로리": "480kcal", "추천": "⭐⭐"},
        {"메뉴": "야채김밥", "가격": "2,500원", "칼로리": "320kcal", "추천": ""},
        {"메뉴": "스팸김밥", "가격": "4,000원", "칼로리": "460kcal", "추천": "⭐⭐"},
    ],
    "라면류": [
        {"메뉴": "라면", "가격": "3,000원", "칼로리": "500kcal", "추천": "⭐"},
        {"메뉴": "치즈라면", "가격": "3,500원", "칼로리": "550kcal", "추천": "⭐⭐"},
        {"메뉴": "해장라면", "가격": "4,000원", "칼로리": "520kcal", "추천": ""},
        {"메뉴": "짜파게티", "가격": "3,500원", "칼로리": "580kcal", "추천": "⭐"},
    ],
    "분식류": [
        {"메뉴": "떡볶이", "가격": "4,000원", "칼로리": "380kcal", "추천": "⭐⭐"},
        {"메뉴": "순대", "가격": "3,500원", "칼로리": "350kcal", "추천": "⭐"},
        {"메뉴": "튀김(5개)", "가격": "2,500원", "칼로리": "300kcal", "추천": ""},
        {"메뉴": "오뎅탕", "가격": "3,000원", "칼로리": "200kcal", "추천": "⭐"},
    ],
    "식사류": [
        {"메뉴": "김치찌개", "가격": "6,000원", "칼로리": "450kcal", "추천": "⭐⭐"},
        {"메뉴": "된장찌개", "가격": "6,000원", "칼로리": "380kcal", "추천": "⭐"},
        {"메뉴": "비빔밥", "가격": "6,500원", "칼로리": "520kcal", "추천": "⭐⭐"},
        {"메뉴": "볶음밥", "가격": "5,500원", "칼로리": "490kcal", "추천": "⭐"},
    ],
}

MENU_KEYWORDS = ["메뉴", "뭐가 있", "뭐 있", "먹을", "음식", "추천", "김밥", "라면", "떡볶이", "식사", "가격", "얼마"]

def show_menu_table():
    st.markdown("#### 🍱 김밥천국 메뉴판")
    tabs = st.tabs(list(MENU_DATA.keys()))
    for tab, (category, items) in zip(tabs, MENU_DATA.items()):
        with tab:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True, hide_index=True)

# ─── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background-color: #fffdf5; }
.kimbap-header {
    background: linear-gradient(135deg, #e8000d, #c0000a);
    color: white; text-align: center;
    padding: 18px 10px 12px 10px;
    border-radius: 0 0 18px 18px;
    margin-bottom: 18px;
    box-shadow: 0 4px 12px rgba(200,0,10,0.15);
}
.kimbap-header h1 { font-size: 2rem; font-weight: 900; letter-spacing: 2px; margin: 0; }
.kimbap-header p { font-size: 0.85rem; margin: 4px 0 0 0; opacity: 0.88; }
.welcome-box {
    background: #fff8e1; border-left: 5px solid #e8000d;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;
    font-size: 1rem; color: #333;
}
.login-box {
    background: white; border: 2px solid #e8000d;
    border-radius: 16px; padding: 32px 28px;
    max-width: 400px; margin: 40px auto; text-align: center;
    box-shadow: 0 4px 20px rgba(232,0,13,0.1);
}
.menu-card { background: white; border: 2px solid #e8000d; border-radius: 14px; padding: 18px 12px; text-align: center; margin-bottom: 8px; }
.menu-card .icon { font-size: 2rem; }
.menu-card .title { font-weight: 700; font-size: 1rem; color: #e8000d; margin: 6px 0 4px 0; }
.menu-card .desc { font-size: 0.78rem; color: #666; }
.stChatInput input { border: 2px solid #e8000d !important; border-radius: 10px !important; }
section[data-testid="stSidebar"] { background: #fff0f0; }
section[data-testid="stSidebar"] .stMarkdown h3 { color: #e8000d; }
.stButton > button { background-color: #e8000d; color: white; border: none; border-radius: 8px; font-weight: 700; padding: 6px 18px; }
.stButton > button:hover { background-color: #c0000a; color: white; }
</style>
""", unsafe_allow_html=True)

# ─── 헤더 ────────────────────────────────────────────────────────
st.markdown("""
<div class="kimbap-header">
    <h1>🍱 KIMBAP HEAVEN</h1>
    <p>건강하고 맛있는 한끼 · 김밥천국에 오신 것을 환영합니다</p>
</div>
""", unsafe_allow_html=True)

# ─── 로그인 화면 ─────────────────────────────────────────────────
if "user_name" not in st.session_state:
    st.markdown("""
    <div class="login-box">
        <div style="font-size:2.5rem">🍱</div>
        <h3 style="color:#e8000d; margin: 8px 0">어서오세요!</h3>
        <p style="color:#666; font-size:0.9rem">이름을 입력하고 시작하세요</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name_input = st.text_input("이름", placeholder="이름을 입력하세요", label_visibility="collapsed")
        if st.button("시작하기 →", use_container_width=True):
            if name_input.strip():
                is_existing = save_user(name_input.strip())
                st.session_state["user_name"] = name_input.strip()
                st.session_state["is_new_user"] = not is_existing
                st.rerun()
            else:
                st.warning("이름을 입력해주세요!")
    st.stop()  # 로그인 전까지 아래 코드 실행 안 함

# ─── 유저 컨텍스트 설정 ──────────────────────────────────────────
user_account_ctx = get_user(st.session_state["user_name"])

# ─── 세션 초기화 ─────────────────────────────────────────────────
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        f"chat-{user_account_ctx.name}",  # 유저별 채팅 분리
        "customer-support-memory.db"
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent

if "chat_started" not in st.session_state:
    st.session_state["chat_started"] = False

if "quick_input" not in st.session_state:
    st.session_state["quick_input"] = None

# ─── 히스토리 출력 ───────────────────────────────────────────────
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

# ─── 첫 화면 ─────────────────────────────────────────────────────
async def has_history():
    items = await session.get_items()
    return len(items) > 0

has_prev = asyncio.run(has_history())

if not has_prev and not st.session_state["chat_started"]:
    # 신규/기존 회원 인사
    if st.session_state.get("is_new_user"):
        st.markdown(f"""
        <div class="welcome-box">
            🎉 환영해요, <b>{user_account_ctx.name}</b>님!<br>
            Basic 멤버로 등록되었습니다 😊<br><br>
            <b>무엇을 도와드릴까요?</b>
        </div>
        """, unsafe_allow_html=True)
    else:
        tier_emoji = "🌟" if user_account_ctx.tier == "premium" else "👋"
        st.markdown(f"""
        <div class="welcome-box">
            {tier_emoji} 다시 오셨군요, <b>{user_account_ctx.name}</b>님! 
            ({user_account_ctx.tier.title()})<br><br>
            <b>무엇을 도와드릴까요?</b>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="menu-card"><div class="icon">🍱</div><div class="title">메뉴 검색</div><div class="desc">오늘의 메뉴와<br>추천 음식을 확인해요</div></div>""", unsafe_allow_html=True)
        if st.button("메뉴 보러가기", key="btn_menu"):
            st.session_state["quick_input"] = "메뉴를 알고 싶어요"
            st.session_state["chat_started"] = True
            st.rerun()
    with col2:
        st.markdown("""<div class="menu-card"><div class="icon">🛒</div><div class="title">주문하기</div><div class="desc">원하는 메뉴를<br>지금 바로 주문해요</div></div>""", unsafe_allow_html=True)
        if st.button("주문 시작하기", key="btn_order"):
            st.session_state["quick_input"] = "주문하고 싶어요"
            st.session_state["chat_started"] = True
            st.rerun()
    with col3:
        st.markdown("""<div class="menu-card"><div class="icon">📅</div><div class="title">예약하기</div><div class="desc">자리 예약을<br>간편하게 해드려요</div></div>""", unsafe_allow_html=True)
        if st.button("예약 하러가기", key="btn_reservation"):
            st.session_state["quick_input"] = "예약하고 싶어요"
            st.session_state["chat_started"] = True
            st.rerun()

# ─── 에이전트 실행 ───────────────────────────────────────────────
async def run_agent(message):
    if any(keyword in message for keyword in MENU_KEYWORDS):
        show_menu_table()

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
                        st.write(f"🤖 Transfered from {st.session_state['agent'].name} to {event.new_agent.name}")
                        st.session_state["agent"] = event.new_agent
                        text_placeholder = st.empty()
                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""

        except InputGuardrailTripwireTriggered:
            st.session_state["text_placeholder"].empty()
            st.chat_message("ai").markdown(
                "저는 김밥천국 전용 어시스턴트라 관련 없는 질문엔 답변이 어렵습니다. 😅\n\n"
                "메뉴, 주문, 예약, 불만 접수 관련 질문을 해주세요! 🍱"
            )

        except OutputGuardrailTripwireTriggered:
            st.session_state["text_placeholder"].empty()
            st.chat_message("ai").markdown(
                "죄송해요, 해당 내용은 안전 정책상 보여드리기 어렵습니다. 🙏\n\n"
                "김밥천국 관련해서 다시 질문해 주세요!"
            )

# ─── 빠른 메뉴 버튼 자동 실행 ───────────────────────────────────
if st.session_state["quick_input"]:
    msg = st.session_state["quick_input"]
    st.session_state["quick_input"] = None
    with st.chat_message("human"):
        st.write(msg)
    asyncio.run(run_agent(msg))

# ─── 채팅 입력 ───────────────────────────────────────────────────
message = st.chat_input("김밥천국 고객센터에 무엇이든 물어보세요 🍱")

if message:
    st.session_state["chat_started"] = True
    with st.chat_message("human"):
        st.write(message)
    asyncio.run(run_agent(message))

# ─── 사이드바 ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🍱 어시스턴트 상태")
    st.markdown(f"**👤 {user_account_ctx.name}** ({user_account_ctx.tier.title()})")
    agent_status = st.empty()
    agent_status.markdown(f"**현재:** {st.session_state['agent'].name}")

    reset = st.button("🔄 대화 초기화")
    if reset:
        asyncio.run(session.clear_session())
        st.session_state["agent"] = triage_agent
        st.session_state["chat_started"] = False
        agent_status.markdown(f"**현재:** {triage_agent.name}")
        st.success("대화가 초기화되었습니다.")
        st.rerun()

    # 로그아웃
    if st.button("🚪 로그아웃"):
        for key in ["user_name", "is_new_user", "session", "agent", "chat_started", "quick_input"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.caption("ⓒ Kimbap Heaven Customer Support")