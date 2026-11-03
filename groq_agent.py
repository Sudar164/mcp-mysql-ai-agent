
import asyncio
import json
import os

from dotenv import load_dotenv
from groq import Groq

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from the .env file")


# --------------------------------------------------
# 2. Initialize Groq client
# --------------------------------------------------

client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-120b"


# --------------------------------------------------
# 3. System Prompt
# --------------------------------------------------

SYSTEM_PROMPT = """
You are an intelligent Marketing and Sales Data Analyst.

You answer users' questions using the connected MySQL database
through MCP tools.

Your responsibilities:

1. Understand the user's question.
2. Inspect the database schema when necessary.
3. Generate valid MySQL SELECT queries.
4. Execute queries using the available MCP tools.
5. Interpret the query results and answer the user.

Response style:

- Give only the final answer in natural language.
- Keep responses short, clear and direct.
- Prefer one or two sentences.
- Include relevant numbers, names and key findings.
- Do not explain how the SQL query works.
- Do not display SQL queries.
- Do not provide step-by-step reasoning.
- Do not use tables.
- Do not add unnecessary introductions or conclusions.

Security:

- Only perform read-only database operations.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER
  or other modification queries.
- Never invent database results.
- Always use the actual database schema.

Error handling:

- If a database tool returns an error, never invent results.
- If query execution fails, explain that the requested data
  could not be retrieved.
- If the query returns no records, clearly state that no
  matching records were found.
- If the database connection fails, inform the user that
  the database is temporarily unavailable.
- Never present an error message as a successful result.
- If the question cannot be answered using the available
  database information, explain this to the user.
"""


# --------------------------------------------------
# 4. Main Agent Function
# --------------------------------------------------

async def main():

    # Start MCP server
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

            # Initialize MCP session
            await session.initialize()

            print("Connected to MCP Server!")

            # ------------------------------------------
            # 5. Discover MCP tools
            # ------------------------------------------

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

            print("\nAvailable MCP tools:")

            for tool in tools_response.tools:
                print(f"- {tool.name}")

            # ------------------------------------------
            # 6. Initialize conversation
            # ------------------------------------------

            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]

            print("\nMarketing & Sales AI Agent is ready!")
            print("Type 'exit' to stop.\n")

            # ------------------------------------------
            # 7. User conversation loop
            # ------------------------------------------

            while True:

                user_question = input("You: ").strip()

                if user_question.lower() in ["exit", "quit"]:
                    print("\nAgent: Goodbye!")
                    break

                if not user_question:
                    continue

                messages.append({
                    "role": "user",
                    "content": user_question
                })

                # --------------------------------------
                # 8. Groq tool-calling loop
                # --------------------------------------

                for step in range(5):

                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        tools=groq_tools,
                        tool_choice="auto",
                        temperature=0.2,
                        max_completion_tokens=1500
                    )

                    assistant_message = response.choices[0].message

                    # ----------------------------------
                    # 9. Check whether Groq requested
                    #    an MCP tool
                    # ----------------------------------

                    if not assistant_message.tool_calls:

                        final_answer = (
                            assistant_message.content or
                            "I couldn't generate a response."
                        )

                        print(f"\nAgent: {final_answer}\n")

                        messages.append({
                            "role": "assistant",
                            "content": final_answer
                        })

                        break

                    # Add assistant tool-call message
                    messages.append(
                        assistant_message.model_dump(
                            exclude_none=True
                        )
                    )

                    # ----------------------------------
                    # 10. Execute requested MCP tools
                    # ----------------------------------

                    for tool_call in assistant_message.tool_calls:

                        tool_name = tool_call.function.name

                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                        print(f"\nCalling MCP tool: {tool_name}")

                        # Developer debugging output
                        if "sql_query" in arguments:
                            print("\nGenerated SQL:")
                            print(arguments["sql_query"])

                        try:

                            result = await session.call_tool(
                                tool_name,
                                arguments=arguments
                            )

                            # Extract tool response
                            tool_output = []

                            for item in result.content:

                                if item.type == "text":
                                    tool_output.append(item.text)

                            result_text = "\n".join(tool_output)

                            # ----------------------------------
                            # 11. Handle MCP execution errors
                            # ----------------------------------

                            if result.is_error:

                                print(
                                    f"\nMCP Tool Error: {result_text}"
                                )

                                result_text = (
                                    "The database tool execution "
                                    "failed. Do not invent or assume "
                                    "any results. Explain the failure "
                                    "to the user."
                                )

                            # ----------------------------------
                            # 12. Handle empty tool responses
                            # ----------------------------------

                            elif not result_text.strip():

                                result_text = (
                                    "The database tool returned "
                                    "no data. Do not invent any "
                                    "results."
                                )

                            # ----------------------------------
                            # 13. Send result back to Groq
                            # ----------------------------------

                        except Exception as error:

                            print(
                                f"\nTool execution failed: {error}"
                            )

                            result_text = (
                                "The MCP tool execution failed. "
                                "Do not invent results. Explain "
                                "that the requested data could "
                                "not be retrieved."
                            )

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_text
                        })

                else:

                    print(
                        "\nAgent: I reached the maximum number "
                        "of tool-calling steps. Please try a "
                        "simpler question.\n"
                    )


# --------------------------------------------------
# 14. Run the application
# --------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
