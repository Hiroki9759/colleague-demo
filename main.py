import os
import openai
import streamlit as st
import langchain
from langchain.callbacks import get_openai_callback
from langchain.chat_models import AzureChatOpenAI
from streamlit_chat import message
from langchain.schema import AIMessage, HumanMessage, SystemMessage
langchain.verbose = False
openai.api_type = "azure"
openai.api_base = "https://colleague-demo-model.openai.azure.com/"
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def init_page():
    st.set_page_config(
        page_title="同期勉強会 Web記事要約サイト",
        page_icon="🤗"
    )
    st.header("同期勉強会 Web記事要約サイト 🤗")
    st.sidebar.title("設定")


def init_messages():
    clear_button = st.sidebar.button("Clear Conversation", key="clear")
    if clear_button or "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content="You are a helpful assistant.")
        ]
        st.session_state.costs = []


def select_model():
    model = st.sidebar.radio("モデルを選んでね！:", ("GPT-3.5", "GPT-3.5-16k"))
    if model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
    else:
        model_name = "gpt-3.5-turbo-16k"

    return AzureChatOpenAI(
        client=None,
        deployment_name="colleague-demo",
        openai_api_base=openai.api_base,
        openai_api_version=openai.api_version,
        openai_api_key=openai.api_key,
        temperature=0,
        request_timeout=180,
    )


def get_url_input():
    url = st.text_input("URL: ", key="input")
    return url


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_content(url):
    try:
        with st.spinner("Fetching Content ..."):
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            # fetch text from main (change the below code to filter page)
            if soup.main:
                return soup.main.get_text()
            elif soup.article:
                return soup.article.get_text()
            else:
                return soup.body.get_text()
    except:
        st.write('something wrong')
        return None


def build_prompt(content, n_chars=300):
    return f"""以下はとあるWebページのコンテンツです。内容を{n_chars}程度でわかりやすく要約してください。

========

{content[:1000]}

========

日本語で書いてね！
"""


def get_answer(llm, messages):
    with get_openai_callback() as cb:
        answer = llm(messages)
    return answer.content, cb.total_cost


def main():
    init_page()

    llm = select_model()
    init_messages()

    container = st.container()
    response_container = st.container()

    with container:
        url = get_url_input()
        is_valid_url = validate_url(url)
        if not is_valid_url:
            st.write('Please input valid url')
            answer = None
        else:
            content = get_content(url)
            if content:
                prompt = build_prompt(content)
                st.session_state.messages.append(HumanMessage(content=prompt))
                with st.spinner("ChatGPT is typing ..."):
                    answer, cost = get_answer(llm, st.session_state.messages)
                st.session_state.costs.append(cost)
            else:
                answer = None

    if answer:
        with response_container:
            st.markdown("## 要約")
            st.write(answer)
            st.markdown("---")
            st.markdown("## 原文はこちら！")
            st.write(content)

    costs = st.session_state.get('いくらかかりました', [])
    st.sidebar.markdown("## 料金")
    st.sidebar.markdown(f"**総額: ${sum(costs):.5f}**")
    for cost in costs:
        st.sidebar.markdown(f"- ${cost:.5f}")

if __name__ == '__main__':
    main()