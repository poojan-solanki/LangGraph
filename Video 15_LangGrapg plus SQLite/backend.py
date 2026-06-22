from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import platform
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
load_dotenv()

db_path  = "/home/poojan/programs/personal-programs/LangGraph CampusX/chatbot.db"
connection = sqlite3.connect(database=db_path, check_same_thread= False)
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    smart_name: str
    boolean_to_create_smart_name: bool

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

def chat(state: ChatState) -> ChatState:
    messages = state["messages"]
    responce = llm.invoke(messages)
    return {"messages": responce}

def generate_smart_name(state: ChatState) -> ChatState:
    messages = state['messages']
    responce = llm.invoke(f"Return one short title for this conversation: {messages}").content[0]["text"]
    return {"smart_name": responce}

def handle_condition(state: ChatState) -> Literal["generate_smart_name", "__end__"]:
    if state['boolean_to_create_smart_name']:
        return "generate_smart_name"
    else:
        return "__end__"
graph = StateGraph(ChatState)

graph.add_node("chat", chat)
graph.add_node("generate_smart_name", generate_smart_name)

graph.add_edge(START, 'chat')
graph.add_conditional_edges("chat", handle_condition)
graph.add_edge('chat', END)
graph.add_edge("generate_smart_name", END)

checkpoint = SqliteSaver(connection)

chat_gemini = graph.compile(checkpointer=checkpoint)