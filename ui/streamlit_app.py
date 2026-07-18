import time
import uuid

import streamlit as st

from graph.build_graph import build_graph

st.set_page_config(page_title="Mini-Assistente RAG Multi-Agent", page_icon="🤖", layout="wide")


@st.cache_resource
def get_graph():
    return build_graph()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []

graph = get_graph()

st.title("🤖 Mini-Assistente Conversacional (RAG + Multi-Agent)")
st.caption(
    "Pergunte sobre clima, políticas/FAQs da empresa, dados de clientes/pedidos ou "
    "qualquer outro assunto — o agente decide sozinho qual ferramenta usar."
)

with st.sidebar:
    st.header("🔍 Debug / Logs")
    if not st.session_state.debug_logs:
        st.write("Os logs de execução do grafo aparecerão aqui.")
    for entry in st.session_state.debug_logs[-50:]:
        st.text(f"[{entry['node']}] {entry['message']}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Digite sua pergunta...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    final_state = graph.invoke({"question": question}, config=config)

    st.session_state.debug_logs.extend(final_state.get("logs", []))

    answer = final_state.get("answer", "Não foi possível gerar uma resposta.")

    with st.chat_message("assistant"):

        def _stream_words():
            for word in answer.split(" "):
                yield word + " "
                time.sleep(0.02)

        st.write_stream(_stream_words)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
