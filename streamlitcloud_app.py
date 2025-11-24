import streamlit as st
from openai import OpenAI

st.title("GPT-5-mini 질문/답변 웹앱")


# -----------------------------
# 1) API Key를 session_state에 저장
# -----------------------------
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

api_key_input = st.text_input(
    "OpenAI API Key를 입력하세요",
    type="password",
    value=st.session_state["api_key"],  # 저장된 값 있으면 자동으로 채워지게
)

# 입력한 값을 항상 session_state에 반영
st.session_state["api_key"] = api_key_input


# -----------------------------
# 2) 질문 입력
# -----------------------------
question = st.text_area("질문을 입력하세요")


# -----------------------------
# 3) @st.cache_data로 결과 캐시
#    - 같은 api_key + 질문이면 재실행 시 API 재호출 안 함
# -----------------------------
@st.cache_data
def ask_gpt(api_key: str, question: str) -> str:
    """gpt-5-mini에 질문하고, 답을 문자열로 돌려주는 함수 (결과 캐시됨)."""
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question},
        ],
    )
    return completion.choices[0].message.content


# 마지막 답변을 session_state에 보관해서 화면에 유지
if "last_answer" not in st.session_state:
    st.session_state["last_answer"] = ""


# -----------------------------
# 4) 버튼 누르면 답변 요청
# -----------------------------
if st.button("GPT-5-mini에게 물어보기"):
    if not st.session_state["api_key"]:
        st.error("먼저 OpenAI API Key를 입력하세요.")
    elif not question.strip():
        st.error("질문을 입력하세요.")
    else:
        with st.spinner("생각 중입니다..."):
            try:
                answer = ask_gpt(st.session_state["api_key"], question)
                st.session_state["last_answer"] = answer
            except Exception as e:
                st.error("API 호출 중 오류가 발생했습니다.")
                st.write(e)


# -----------------------------
# 5) 화면에 답변 출력
# -----------------------------
if st.session_state["last_answer"]:
    st.subheader("답변")
    st.write(st.session_state["last_answer"])
