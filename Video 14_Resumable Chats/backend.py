from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
load_dotenv()

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

def chat(state: ChatState) -> ChatState:
    messages = state["messages"]
    
    responce = llm.invoke(messages)

    return {"messages": responce}

graph = StateGraph(ChatState)

graph.add_node("chat", chat)

graph.add_edge(START, 'chat')
graph.add_edge('chat', END)

checkpoint = InMemorySaver()

chat_gemini = graph.compile(checkpointer=checkpoint)



# user_config = {"configurable": {"thread_id": 'thread_1'}}
# responce = chat_gemini.invoke(
#             input={"messages": HumanMessage(content="Hii")},
#             config=user_config
#         )

# convos = chat_gemini.get_state(config=user_config)
# print(convos.values['messages'][0].content)
