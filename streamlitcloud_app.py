import streamlit as st
from openai import OpenAI

# -----------------------------------
# 0. 공통: API Key, 클라이언트 헬퍼
# -----------------------------------
st.set_page_config(page_title="21_Lab Streamlit", page_icon="📚")

st.title("21_Lab Streamlit 실습 앱")

# API Key를 session_state에 저장
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

st.sidebar.header("설정")
api_key_input = st.sidebar.text_input(
    "OpenAI API Key를 입력하세요",
    type="password",
    value=st.session_state["api_key"],
)
st.session_state["api_key"] = api_key_input


def get_client() -> OpenAI | None:
    """API Key가 없으면 None, 있으면 OpenAI 클라이언트 리턴"""
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        st.warning("먼저 왼쪽 사이드바에서 OpenAI API Key를 입력하세요.")
        return None
    return OpenAI(api_key=api_key)


# 페이지 선택
page = st.sidebar.radio(
    "페이지 선택",
    [
        "1. Q&A (gpt-5-mini)",
        "2. Chat (Responses API)",
        "3. 도서관 챗봇",
        "4. ChatPDF",
    ],
)


# -----------------------------------
# 1. Q&A 페이지 (이미 만든 것 + cache_data)
# -----------------------------------
@st.cache_data
def ask_gpt(api_key: str, question: str) -> str:
    """gpt-5-mini에 질문하고, 답을 문자열로 돌려주는 함수 (결과 캐시됨)"""
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question},
        ],
    )
    return completion.choices[0].message.content


def page_qna():
    st.header("1. GPT-5-mini 질문/답변 페이지")

    question = st.text_area("질문을 입력하세요")

    if "last_answer" not in st.session_state:
        st.session_state["last_answer"] = ""

    if st.button("GPT-5-mini에게 물어보기"):
        api_key = st.session_state.get("api_key", "")
        if not api_key:
            st.error("먼저 OpenAI API Key를 입력하세요.")
        elif not question.strip():
            st.error("질문을 입력하세요.")
        else:
            with st.spinner("생각 중입니다..."):
                try:
                    answer = ask_gpt(api_key, question)
                    st.session_state["last_answer"] = answer
                except Exception as e:
                    st.error("API 호출 중 오류가 발생했습니다.")
                    st.write(e)

    if st.session_state.get("last_answer"):
        st.subheader("답변")
        st.write(st.session_state["last_answer"])


# -----------------------------------
# 2. Chat 페이지 (Responses API + Clear 버튼)
# -----------------------------------
def page_chat():
    st.header("2. Chat 페이지 (Responses API)")

    client = get_client()
    if client is None:
        return

    # 대화 내역을 session_state에 저장
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []  # {role: "user"/"assistant", content: str}

    st.caption("아래는 단순 예시 챗봇입니다. Clear 버튼을 누르면 대화 내용이 초기화됩니다.")

    # 기존 대화 보여주기
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 입력
    user_input = st.chat_input("메시지를 입력하세요")

    if user_input:
        # 1) 사용자 메시지를 상태에 추가
        st.session_state["chat_messages"].append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        # 2) 지금까지의 대화를 하나의 텍스트로 만들기
        conversation_text = ""
        for m in st.session_state["chat_messages"]:
            speaker = "사용자" if m["role"] == "user" else "어시스턴트"
            conversation_text += f"{speaker}: {m['content']}\n"
        prompt = conversation_text + "어시스턴트:"

        # 3) Responses API 호출
        with st.chat_message("assistant"):
            with st.spinner("응답 생성 중..."):
                try:
                    response = client.responses.create(
                        model="gpt-5-mini",
                        input=prompt,
                    )

                    # ---- 응답 텍스트 안전하게 꺼내기 ----
                    answer = None

                    # 1) output_text 속성이 있으면 그대로 사용
                    answer = getattr(response, "output_text", None)

                    # 2) 없으면 output -> content -> text 순서대로 한 단계씩 검사하며 꺼내기
                    if not answer:
                        output = getattr(response, "output", None)
                        if output and len(output) > 0:
                            content_list = getattr(output[0], "content", None)
                            if content_list and len(content_list) > 0:
                                text_obj = getattr(content_list[0], "text", None)
                                if text_obj is not None:
                                    answer = getattr(text_obj, "value", str(text_obj))

                    # 3) 그래도 못 꺼냈으면 전체 response를 문자열로 보여주기 (디버그용)
                    if not answer:
                        answer = f"응답을 읽어오는 데 실패했어요.\n원본 응답: {response}"

                    st.markdown(answer)

                    st.session_state["chat_messages"].append(
                        {"role": "assistant", "content": answer}
                    )
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

    # Clear 버튼
    if st.button("대화 내용 지우기"):
        st.session_state["chat_messages"] = []
        st.success("대화 내용이 초기화되었습니다.")



# -----------------------------------
# 3. 도서관 챗봇 페이지
# -----------------------------------

# 여기에 국립부경대학교 도서관 규정집 전체를 복사해서 붙여넣으면 더 정확해집니다.
LIBRARY_RULES = """
여기에 국립부경대학교 도서관 규정을 복사하여 붙여넣으세요.
예: 휴관일, 대출 권수, 연장, 연체료, 열람실 이용 규칙 등...
"""


def page_library_chatbot():
    st.header('3. "국립부경대학교 도서관 챗봇" 페이지')

    client = get_client()
    if client is None:
        return

    st.caption("※ 실제 과제 제출 시에는 코드의 LIBRARY_RULES 변수 안에 도서관 규정집 텍스트를 붙여넣으세요.")

    question = st.text_input("도서관 규정에 대해 궁금한 점을 입력하세요")

    if st.button("도서관 챗봇에게 물어보기"):
        if not question.strip():
            st.error("질문을 입력하세요.")
            return

        prompt = f"""
너는 국립부경대학교 도서관 규정 안내 챗봇이다.
아래 [규정집] 내용을 바탕으로만 답변하고, 내용이 없으면 "규정집에 없는 내용입니다" 라고 답해라.

[규정집]
{LIBRARY_RULES}

[질문]
{question}
"""

        with st.spinner("도서관 규정집을 확인하는 중입니다..."):
            try:
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=prompt,
                )
                answer = response.output[0].content[0].text
                st.subheader("답변")
                st.write(answer)
            except Exception as e:
                st.error("API 호출 중 오류가 발생했습니다.")
                st.write(e)


# -----------------------------------
# 4. ChatPDF 페이지
# -----------------------------------
def page_chatpdf():
    st.header("4. ChatPDF 페이지")

    client = get_client()
    if client is None:
        return

    if "pdf_vector_store_id" not in st.session_state:
        st.session_state["pdf_vector_store_id"] = None

    st.caption("PDF 파일을 업로드하고, 해당 내용을 바탕으로 질문/답변을 수행합니다.")

    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요 (1개)", type=["pdf"])

    # Vector store 생성 버튼
    if uploaded_file is not None and st.button("이 PDF로 Vector store 생성"):
        with st.spinner("PDF 업로드 및 인덱싱 중..."):
            try:
                # 1) PDF를 OpenAI 파일로 업로드
                file = client.files.create(file=uploaded_file, purpose="assistants")

                # 2) 빈 vector store 생성
                vector_store = client.beta.vector_stores.create(
                    name="ChatPDF vector store",
                )

                # 3) vector store에 파일 연결
                client.beta.vector_stores.files.create(
                    vector_store_id=vector_store.id,
                    file_id=file.id,
                )

                st.session_state["pdf_vector_store_id"] = vector_store.id
                st.success("Vector store 생성 완료!")
            except Exception as e:
                st.error("Vector store 생성 중 오류가 발생했습니다.")
                st.write(e)

    # Vector store가 있을 때만 질문/답변 UI 표시
    vs_id = st.session_state.get("pdf_vector_store_id")
    if vs_id:
        st.info(f"현재 활성화된 Vector store ID: {vs_id}")

        question = st.text_input("PDF 내용을 바탕으로 질문을 입력하세요")

        if st.button("PDF에게 물어보기"):
            if not question.strip():
                st.error("질문을 입력하세요.")
            else:
                with st.spinner("PDF 내용을 검색하는 중입니다..."):
                    try:
                        response = client.responses.create(
                            model="gpt-5-mini",
                            input=question,
                            tools=[{"type": "file_search"}],
                            tool_resources={
                                "file_search": {
                                    "vector_store_ids": [vs_id],
                                }
                            },
                        )
                        answer = response.output[0].content[0].text
                        st.subheader("답변")
                        st.write(answer)
                    except Exception as e:
                        st.error("질문 처리 중 오류가 발생했습니다.")
                        st.write(e)

        # Vector store 삭제 버튼
        if st.button("Vector store 삭제 (Clear)"):
            with st.spinner("Vector store 삭제 중입니다..."):
                try:
                    client.beta.vector_stores.delete(vector_store_id=vs_id)
                except Exception as e:
                    st.error("삭제 중 오류가 발생했습니다.")
                    st.write(e)
                else:
                    st.session_state["pdf_vector_store_id"] = None
                    st.success("Vector store가 삭제되었습니다.")


# -----------------------------------
# 페이지 라우팅
# -----------------------------------
if page.startswith("1."):
    page_qna()
elif page.startswith("2."):
    page_chat()
elif page.startswith("3."):
    page_library_chatbot()
elif page.startswith("4."):
    page_chatpdf()
