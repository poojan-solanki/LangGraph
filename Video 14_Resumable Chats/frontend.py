import streamlit as st
from backend import chat_gemini, llm
from langchain_core.messages import HumanMessage
import uuid

# -------------------------------------------------------------  Helper Functions  -------------------------------------------------------------------------
# This takes langgraph stream responce generator and yeilds the text
#Generator Object
def streamlit_generator(responce):
    for chunk in responce:
        print (f"Chunk for debug: {chunk}\n")
        if chunk["type"] == "messages":
            message_chunk, metadata = chunk['data']
            if metadata.get("langgraph_node") == "chat":
                if message_chunk.content:
                    print(message_chunk.content[0]["text"])
                    yield message_chunk.content[0]["text"]

# Create new thread_id
def create_new_session():
    id = uuid.uuid4()
    print(f"Returning thread_id: {str(id)}, smart_name: New Chat")
    return {"thread_id": str(id), "smart_name": "New Chat"}

def new_chat():
    conversation_thread = create_new_session()
    add_conversation_thread_in_all_conversations_ids(st.session_state["conversation_thread"])
    st.session_state['all_conversations_ids'].append(conversation_thread)
    st.session_state['conversation_thread'] = conversation_thread
    st.session_state['message_history'] = []
    
def add_conversation_thread_in_all_conversations_ids(conversation_thread):
    if not any(conversation_thread['thread_id'] == item['thread_id'] for item in st.session_state['all_conversations_ids']):
        print(f"Cono appended {conversation_thread}")
        st.session_state['all_conversations_ids'].append(conversation_thread)

def get_conversation(thread_id):
    # print(f"THREAD ID: {thread_id}")
    # print(f"THREAD ID IN SESSION STATE {st.session_state['thread_id']}")
    snapshot = chat_gemini.get_state({'configurable':{"thread_id": thread_id}}).values.get('messages')
    if snapshot is None:
        return []
    # print(f"SNAPSHOT: {snapshot}")
    messages = []
    for msg in snapshot:
        if isinstance(msg, HumanMessage):
            role = "user"
        else:
            role = "ai"
        messages.append({"role": role, "content":msg.content if role == "user" else msg.content[0]["text"]})
    # print(f"Messages: {messages}")
    return messages

def get_smart_name(thread_id):
    print(f"THREAD_ID: {thread_id}")
    snapshot = chat_gemini.get_state({'configurable':{"thread_id": thread_id}})
    print(f"SNAPSHOT {snapshot}")
    print(f"SMART NAME IS {snapshot.values.get('smart_name')}")
    smart_name = snapshot.values.get('smart_name')
    st.session_state["conversation_thread"]["smart_name"] = smart_name
    for item in st.session_state["all_conversations_ids"]:
        if item["thread_id"] == st.session_state["conversation_thread"]["thread_id"]:
            item["smart_name"] = smart_name
            break
    # return snapshot.values.get('smart_name')

# def update_smart_name(smart_name):
#     st.session_state['conversation_thread']["smart_name"] = smart_name
   
#     for item in st.session_state["all_conversations_ids"]:
#         if item["thread_id"] == st.session_state['conversation_thread']['thread_id']:
#             item["smart_name"] = smart_name
#             break
#     print(f"All converssation state debug {st.session_state["all_conversations_ids"]}")

# def give_smart_name(thread_id):
#     snapshot = chat_gemini.get_state({'configurable':{"thread_id": thread_id}}).values.get('messages')
#     if snapshot is None:
#         return "New Chat"
#     responce = llm.invoke(f"Return one short title for this conversation: {snapshot}").content[0]["text"]
#     update_smart_name(responce)
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------  Session Startup  --------------------------------------------------------------------------
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if "conversation_thread" not in st.session_state:
    st.session_state['conversation_thread'] = create_new_session()

# print(st.session_state['conversation_thread'])


if 'all_conversations_ids' not in st.session_state:
    st.session_state['all_conversations_ids'] = []

add_conversation_thread_in_all_conversations_ids(st.session_state["conversation_thread"])
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------  Side Bar UI  ------------------------------------------------------------------------------
with st.sidebar:
    if st.button(label="Start a New Chat",use_container_width=True, type='primary'):
        conversation_thread = new_chat()

    st.title("Chat History")

    for conversation_thread in st.session_state["all_conversations_ids"][::-1]:
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

    # responce = chat_gemini.invoke({"messages": HumanMessage(content=user_input)}, config=user_config)
    # ai_message = responce['messages'][-1].content[0]['text']
    # print(responce)
    # st.session_state['message_history'].append({'role': "ai", "content": ai_message})
    # with st.chat_message('ai'):
    #     st.text(ai_message)

    generate_smart_name = True if st.session_state["conversation_thread"]['smart_name'].lower() == "New Chat".lower() else False
    print(f"Generate smart name {generate_smart_name}")
    responce = chat_gemini.stream(
            input={"messages": HumanMessage(content=user_input), "boolean_to_create_smart_name": generate_smart_name},
            config=user_config,
            stream_mode='messages',
            version='v2'
        )
    

    ai_message = st.write_stream(streamlit_generator(responce))
    print(f"RESPONSE for debug: {ai_message}")
    if generate_smart_name: get_smart_name(st.session_state['conversation_thread']['thread_id'])
    print(f"All converssation state debug {st.session_state['all_conversations_ids']}")

    print(f"Current conversation thread debug {st.session_state['conversation_thread']}")
    st.session_state['message_history'].append({'role': "ai", "content": ai_message})
    

    # if st.session_state['conversation_thread']["smart_name"] == "New Chat":
    #     give_smart_name(st.session_state['conversation_thread']["thread_id"])