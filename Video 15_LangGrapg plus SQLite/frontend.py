import streamlit as st
from backend import chat_gemini, checkpoint
from langchain_core.messages import HumanMessage
import uuid

# -------------------------------------------------------------  Helper Functions  -------------------------------------------------------------------------
# This takes langgraph stream responce generator and yeilds the text
#Generator Object
def streamlit_generator(responce):
    for chunk in responce:
        if chunk["type"] == "messages":
            message_chunk, metadata = chunk['data']
            if metadata.get("langgraph_node") == "chat":
                if message_chunk.content:
                    yield message_chunk.content[0]["text"]

# Create new thread_id
def create_new_session():
    id = uuid.uuid4()
    return {"thread_id": str(id), "smart_name": "New Chat"}

def new_chat():
    conversation_thread = create_new_session()
    add_conversation_thread_in_all_conversations_ids(st.session_state["conversation_thread"])
    st.session_state['all_conversations_ids'].append(conversation_thread)
    st.session_state['conversation_thread'] = conversation_thread
    st.session_state['message_history'] = []
    
def add_conversation_thread_in_all_conversations_ids(conversation_thread):
    if not any(conversation_thread['thread_id'] == item['thread_id'] for item in st.session_state['all_conversations_ids']):
        st.session_state['all_conversations_ids'].append(conversation_thread)

def get_conversation(thread_id):
    snapshot = chat_gemini.get_state({'configurable':{"thread_id": thread_id}}).values.get('messages')
    if snapshot is None:
        return []
    messages = []
    for msg in snapshot:
        if isinstance(msg, HumanMessage):
            role = "user"
        else:
            role = "ai"
        messages.append({"role": role, "content":msg.content if role == "user" else msg.content[0]["text"]})
    return messages

def get_smart_name(thread_id):
    snapshot = chat_gemini.get_state({'configurable':{"thread_id": thread_id}})
    smart_name = snapshot.values.get('smart_name')
    st.session_state["conversation_thread"]["smart_name"] = smart_name
    for item in st.session_state["all_conversations_ids"]:
        if item["thread_id"] == st.session_state["conversation_thread"]["thread_id"]:
            item["smart_name"] = smart_name
            break

def retrive_all_threads():
    data = []
    temp = []
    for i in checkpoint.list(None):
        if i.config['configurable']['thread_id'] not in temp:
            data.append({"thread_id": i.config['configurable']['thread_id'], "smart_name": i.checkpoint['channel_values']['smart_name']})
            temp.append(i.config['configurable']['thread_id'])
    return data
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------  Session Startup  --------------------------------------------------------------------------
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "conversation_thread" not in st.session_state:
    st.session_state['conversation_thread'] = create_new_session()

if 'all_conversations_ids' not in st.session_state:
    st.session_state['all_conversations_ids'] = retrive_all_threads()

add_conversation_thread_in_all_conversations_ids(st.session_state["conversation_thread"])
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------  Side Bar UI  ------------------------------------------------------------------------------
with st.sidebar:
    if st.button(label="Start a New Chat",use_container_width=True, type='primary'):
        conversation_thread = new_chat()

    st.title("Chat History")

    for conversation_thread in st.session_state["all_conversations_ids"]:
        if st.button(label=conversation_thread['smart_name'], key=conversation_thread['thread_id'], use_container_width=True):
            st.session_state["conversation_thread"] = conversation_thread
            messages = get_conversation(str(conversation_thread["thread_id"]))
            st.session_state["message_history"] = messages

# ----------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------  Main UI  ---------------------------------------------------------------------------------
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'],unsafe_allow_html=True, width="auto", text_alignment="left")

user_config = {"configurable": {"thread_id": st.session_state['conversation_thread']["thread_id"]}}
user_input = st.chat_input("Type message here")

if user_input:
    st.session_state['message_history'].append({"role": 'user', "content": user_input})
    with st.chat_message(name='user'):
        st.text(user_input)

    generate_smart_name = True if st.session_state["conversation_thread"]['smart_name'].lower() == "New Chat".lower() else False
    responce = chat_gemini.stream(
            input={"messages": HumanMessage(content=user_input), "boolean_to_create_smart_name": generate_smart_name},
            config=user_config,
            stream_mode='messages',
            version='v2'
        )
    

    ai_message = st.write_stream(streamlit_generator(responce))
    if generate_smart_name: get_smart_name(st.session_state['conversation_thread']['thread_id'])

    st.session_state['message_history'].append({'role': "ai", "content": ai_message})