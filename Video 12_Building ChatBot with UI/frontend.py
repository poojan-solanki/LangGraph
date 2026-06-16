import streamlit as st
from backend import chat_gemini
from langchain_core.messages import HumanMessage

session = st.session_state
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_config = {"configurable": {"thread_id": "user_1"}}
user_input = st.chat_input("Type message here")

if user_input:
    st.session_state['message_history'].append({"role": 'user', "content": user_input})
    with st.chat_message(name='user'):
        st.text(user_input)

    responce = chat_gemini.invoke({"messages": HumanMessage(content=user_input)}, config=user_config)
    ai_message = responce['messages'][-1].content[0]['text']
    print(responce)
    st.session_state['message_history'].append({'role': "ai", "content": ai_message})
    with st.chat_message('ai'):
        st.text(ai_message)