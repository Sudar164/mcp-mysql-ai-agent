
import asyncio
import json
import os
import re

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ==================================================
# 1. APPLICATION CONFIGURATION
# ==================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-120b"


# ==================================================
# 2. SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
You are a Marketing and Sales Data Analyst.

You answer questions using the connected MySQL database
through MCP tools.

YOUR RESPONSIBILITIES:

1. Understand the user's question.
2. Inspect the database schema when necessary.
3. Generate valid MySQL SELECT queries.
4. Execute queries using MCP tools.
5. Interpret the query results.
6. Give the user the final answer.

RESPONSE STYLE:

- Return exactly ONE concise sentence for database questions.
- Use natural language.
- Include relevant names and numerical values.
- Never repeat or rephrase the same information.
- Never show generated SQL.
- Never explain how the SQL query works.
- Never use tables.
- Never use Markdown code blocks or inline code.
- Never wrap numbers or names in backticks.
- Avoid unnecessary introductions and conclusions.

IMPORTANT RESPONSE RULE:

Return only the final result in one sentence.
Do not provide a second sentence summarizing the first.
Do not add explanations, summaries or conclusions.

SECURITY:

- Only perform read-only database operations.
- Never generate INSERT, UPDATE, DELETE, DROP,
  ALTER or other modification queries.
- Always use the actual database schema.
- Never invent database results.

ERROR HANDLING:

- If a database tool returns an error, never invent results.
- If database access fails, explain that the data
  could not be retrieved.
- If no matching records exist, say so.
- If a question is outside the database domain,
  explain that the available data cannot answer it.
- Never present a failed query as a successful result.
"""


# ==================================================
# 3. RESPONSE CLEANING FUNCTION
# ==================================================

def clean_response(answer):

    if not answer:
        return "I couldn't generate a response."

    # Remove unwanted Markdown formatting
    answer = answer.replace("`", "")
    answer = answer.replace("**", "")
    answer = answer.replace("__", "")

    # Normalize whitespace
    answer = " ".join(answer.split())

    # Split into sentences
    sentences = re.split(
        r'(?<=[.!?])\s+',
        answer
    )

    # Keep only the first meaningful sentence
    for sentence in sentences:

        sentence = sentence.strip()

        if sentence:
            return sentence

    return "I couldn't generate a response."


# ==================================================
# 4. MCP + GROQ AGENT FUNCTION
# ==================================================

async def ask_agent(messages):

    server_params = StdioServerParameters(
        command="python",
        args=["mysql_mcp_server.py"]
    )

    async with stdio_client(server_params) as (
        read_stream,
        write_stream
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            # Initialize MCP connection
            await session.initialize()

            # Discover MCP tools
            tools_response = await session.list_tools()

            groq_tools = []

            for tool in tools_response.tools:

                groq_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema
                    }
                })

            # Maximum five tool-calling rounds
            for step in range(5):

                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=groq_tools,
                    tool_choice="auto",
                    temperature=0,
                    max_completion_tokens=200
                )

                assistant_message = response.choices[0].message

                # --------------------------------------
                # 5. CHECK FOR FINAL ANSWER
                # --------------------------------------

                if not assistant_message.tool_calls:

                    final_answer = (
                        assistant_message.content
                        or "I couldn't generate a response."
                    )

                    return clean_response(final_answer)

                # --------------------------------------
                # 6. SAVE ASSISTANT TOOL-CALL MESSAGE
                # --------------------------------------

                messages.append(
                    assistant_message.model_dump(
                        exclude_none=True
                    )
                )

                # --------------------------------------
                # 7. EXECUTE MCP TOOLS
                # --------------------------------------

                for tool_call in assistant_message.tool_calls:

                    tool_name = tool_call.function.name

                    try:

                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                        print(
                            f"Calling MCP tool: {tool_name}"
                        )

                        # Execute MCP tool
                        result = await session.call_tool(
                            tool_name,
                            arguments=arguments
                        )

                        # Extract tool response
                        tool_output = []

                        for item in result.content or []:

                            if item.type == "text":
                                tool_output.append(item.text)

                        result_text = "\n".join(tool_output)

                        # Handle MCP errors
                        if result.is_error:

                            print(
                                f"MCP Tool Error: {result_text}"
                            )

                            result_text = (
                                "The database tool execution failed. "
                                "Do not invent results. Explain that "
                                "the requested data could not be retrieved."
                            )

                        elif not result_text.strip():

                            result_text = (
                                "The tool returned no output. "
                                "Do not invent any results."
                            )

                    except Exception as error:

                        print(
                            f"MCP execution error: {error}"
                        )

                        result_text = (
                            "The MCP tool execution failed. "
                            "Do not invent results. Explain that "
                            "the requested data could not be retrieved."
                        )

                    # ----------------------------------
                    # 8. SEND TOOL RESULT BACK TO GROQ
                    # ----------------------------------

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    })

            # Maximum tool-calling rounds reached
            return (
                "I couldn't complete the analysis. "
                "Please try a simpler question."
            )


# ==================================================
# 9. STREAMLIT PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Marketing & Sales AI",
    page_icon="📊",
    layout="centered"
)


# ==================================================
# 10. INITIALIZE SESSION STATE
# ==================================================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


# ==================================================
# 11. SIDEBAR
# ==================================================

with st.sidebar:

    st.title("📊 Marketing & Sales AI")

    st.caption("Powered by Groq, MCP and MySQL")

    st.divider()

    st.subheader("About")

    st.write(
        "Ask questions about your marketing and sales "
        "database using natural language."
    )

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        st.rerun()

    st.divider()

    st.caption("Database: marketing_sales_db")

    st.caption(f"AI Model: {MODEL}")


# ==================================================
# 12. MAIN CHAT INTERFACE
# ==================================================

st.title("Marketing & Sales Assistant")

st.write(
    "Ask questions about sales, customers, products, "
    "leads and marketing campaigns."
)

st.divider()


# ==================================================
# 13. DISPLAY CONVERSATION HISTORY
# ==================================================

for message in st.session_state.messages:

    role = message.get("role")

    # Display only user and assistant messages
    if role not in ["user", "assistant"]:
        continue

    # Ignore internal tool-call messages
    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        continue

    with st.chat_message(role):

        st.markdown(content)


# ==================================================
# 14. USER INPUT
# ==================================================

user_question = st.chat_input(
    "Ask something about your marketing and sales data..."
)


if user_question:

    # ----------------------------------------------
    # Save user question
    # ----------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": user_question
    })

    # Display user question
    with st.chat_message("user"):

        st.markdown(user_question)

    # ----------------------------------------------
    # Generate AI response
    # ----------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Analyzing your data..."):

            try:

                answer = asyncio.run(
                    ask_agent(st.session_state.messages)
                )

                answer = clean_response(answer)

                st.markdown(answer)

            except Exception as error:

                print(
                    f"Agent error: {error}"
                )

                answer = (
                    "I'm unable to process your request right now. "
                    "Please check the database connection and try again."
                )

                st.error(answer)

    # ----------------------------------------------
    # SAVE FINAL RESPONSE ONLY ONCE
    # ----------------------------------------------

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
