import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.filters import FunctionInvocationContext


from sk_plugins.ai_search import AiSearch
from sk_plugins.langchain_sql_db import RunSQLLangchain 
from sql_connection.sqlalchemy_authentication import db, _validate_sql, _enforce_single_table

from dotenv import load_dotenv
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
import os

# NEW: Chainlit
import chainlit as cl

# Kernel function-invocation filter (unchanged)
async def function_invocation_filter(context: FunctionInvocationContext, next):
    if "messages" not in context.arguments:
        await next(context)
        return
    print(f"    Agent [{context.function.name}] called with messages: {context.arguments['messages']}")
    await next(context)
    print(f"    Response from agent [{context.function.name}]: {context.result.value}")

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment_name = "gpt-4.1"
openai_key = os.getenv("AZURE_OPENAI_API_KEY")
sqlprompt = r"C:\Users\lananoor\OneDrive - Microsoft\AI Agents\SQLDemo\sql_connection\sql_prompt.txt"

kernel = Kernel()
kernel.add_filter("function_invocation", function_invocation_filter)

sql_agent = ChatCompletionAgent(
    service=AzureChatCompletion(
        deployment_name=deployment_name,
        api_key=openai_key,
        endpoint=endpoint,
        api_version=api_version,
    ),
    name="SQLAgent",
    instructions=sqlprompt,
    plugins=[RunSQLLangchain()],
    kernel=kernel,
    )

# search_agent = ChatCompletionAgent(
#     service=AzureChatCompletion(
#         deployment_name="gpt-4.1",
#         api_key=openai_key,
#         endpoint=endpoint,
#         api_version=api_version,
#     ),
#     kernel=kernel,
#     name="MainSearchAgent",
#     instructions=(
#         """
# Your task is to analyze each user query and route it to the correct capability:
# 1. If the query includes structured constraints, invoke the FilteredQueryAgent.
# 2. Otherwise, invoke the AiSearchHybrid plugin directly for hybrid semantic + vector search.
# Always pick exactly one path.
# """
#     ),
#     plugins=[ AiSearchHybrid()],
# )

router_agent = ChatCompletionAgent(
    service=AzureChatCompletion(
        deployment_name="gpt-4.1",
        api_key=openai_key,
        endpoint=endpoint,
        api_version=api_version,
    ),
    kernel=kernel,
    name="RouterAgent",
    instructions=(
        """
You are an AI Assistant for Abu Dhabi Investment Council (ADIC). Your role is to answer employee questions by selecting the correct tool:

- Invoke AiSearch when the query relates to concepts about organizational change and AI readiness — including topics such as employee experience, leadership practices, transformation strategies, guiding principles for adoption, high-performing organizations, or approaches to change management. Provide grounded answers using this knowledge.

- Invoke sql_agent when the query involves structured data from the TransactionTrades table — such as transactions, amounts, dates, customer IDs, or any other numeric or tabular information. Always return results in a clear markdown table so they are easy to read.

Always choose the tool that best matches the user’s query context. Keep your tone friendly and helpful. 
"""
    ),
    plugins=[AiSearch(), sql_agent],
)

# ---------- CLI loop (unchanged) ----------
thread: ChatHistoryAgentThread = None

async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    response = await router_agent.get_response(
        messages=user_input,
        thread=thread,
    )

    if response:
        print(f"Agent :> {response}")

    return True

async def main() -> None:
    print("Welcome to the chat bot!\n  Type 'exit' to exit.")
    chatting = True
    while chatting:
        chatting = await chat()

if __name__ == "__main__":
    asyncio.run(main())

# ============================
# Chainlit frontend (simple)
# ============================

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("agent", router_agent)
    cl.user_session.set("thread", ChatHistoryAgentThread())
    await cl.Message(content="Hi! Ask me something—I’ll route it to the right search.").send()

@cl.on_message
async def on_message(message: cl.Message):
    agent: ChatCompletionAgent = cl.user_session.get("agent")
    thread: ChatHistoryAgentThread = cl.user_session.get("thread")

    user_text = (message.content or "").strip()
    if not user_text:
        await cl.Message(content="Please enter a message.").send()
        return

    try:
        resp = await agent.get_response(messages=user_text, thread=thread)
        await cl.Message(content=str(resp) if resp else "(no response)").send()
    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()
