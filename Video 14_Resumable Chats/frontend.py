import streamlit as st
from backend import chat_gemini
from langchain_core.messages import HumanMessage
import uuid

# -------------------------------------------------------------  Helper Functions  -------------------------------------------------------------------------
# This takes langgraph stream responce generator and yeilds the text
#Generator Object
def streamlit_generator(responce):
    for chunk in responce:
        message_chunk, metadata = chunk['data']
        if message_chunk.content:
            yield message_chunk.content[0]["text"]

# Create new thread_id
def create_new_session():
    uuid = uuid.uuid4()
    return {"thread_id": uuid, "smart_name": "New Chat"}

def new_chat():
    conversation_thread = create_new_session()
    add_conversation_thread_in_all_conversations_ids(st.session_state["thread_id"])
    st.session_state['all_conversations_ids'].append(thread_id)
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    
def add_conversation_thread_in_all_conversations_ids(conversation_thread):
    if conversation_thread not in st.session_state['all_conversations_ids']:
        st.session_state['all_conversations_ids'].append(conversation_thread)
def get_conversation(thread_id):
    print(f"THREAD ID: {thread_id}")
    print(f"THREAD ID IN SESSION STATE {st.session_state['thread_id']}")
    snapshot = chat_gemini.get_state({'configurable':{"thread_id": thread_id}}).values.get('messages')
    if snapshot is None:
        return []
    print(f"SNAPSHOT: {snapshot}")
    messages = []
    for msg in snapshot:
        if isinstance(msg, HumanMessage):
            role = "user"
        else:
            role = "ai"
        messages.append({"role": role, "content":msg.content if role == "user" else msg.content[0]["text"]})
    print(f"Messages: {messages}")
    return messages

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------  Session Startup  --------------------------------------------------------------------------
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "conversation_thread" not in st.session_state:
    st.session_state['conversation_thread'] = create_new_session()

if 'all_conversations_ids' not in st.session_state:
    st.session_state['all_conversations_ids'] = []

add_conversation_thread_in_all_conversations_ids(st.session_state["conversation_thread"])
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------  Side Bar UI  ------------------------------------------------------------------------------
with st.sidebar:
    if st.button(label="Start a New Chat",use_container_width=True, type='primary'):
        thread_id = new_chat()

    st.title("Chat History")

    for thread_id in st.session_state["all_conversations_ids"][::-1]:
        if st.button(str(thread_id)):
            st.session_state["thread_id"] = thread_id
            messages = get_conversation(str(thread_id))
            st.session_state["message_history"] = messages

# ----------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------  Main UI  ---------------------------------------------------------------------------------
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'],unsafe_allow_html=True, width="auto", text_alignment="left")

user_config = {"configurable": {"thread_id": st.session_state['thread_id']}}
user_input = st.chat_input("Type message here")

if user_input:
    st.session_state['message_history'].append({"role": 'user', "content": user_input})
    with st.chat_message(name='user'):
        st.text(user_input)

    # responce = chat_gemini.invoke({"messages": HumanMessage(content=user_input)}, config=user_config)
    # ai_message = responce['messages'][-1].content[0]['text']
    # print(responce)
    # st.session_state['message_history'].append({'role': "ai", "content": ai_message})
    # with st.chat_message('ai'):
    #     st.text(ai_message)


    responce = chat_gemini.stream(
            input={"messages": HumanMessage(content=user_input)},
            config=user_config,
            stream_mode='messages',
            version='v2'
        )
    

    ai_message = st.write_stream(streamlit_generator(responce))
    st.session_state['message_history'].append({'role': "ai", "content": ai_message})
