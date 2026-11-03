
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    # Step 1: Configure the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mysql_mcp_server.py"],
    )

    # Step 2: Start the server and establish communication
    async with stdio_client(server_params) as (read_stream, write_stream):

        # Step 3: Create an MCP client session
        async with ClientSession(read_stream, write_stream) as session:

            # Step 4: Initialize the MCP connection
            await session.initialize()

            print("Connected to MCP server!")

            # Step 5: Discover available tools
            tools = await session.list_tools()

            print("\nAvailable tools:")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            # Step 6: Test list_tables tool
            tables_result = await session.call_tool(
                "list_tables",
                arguments={}
            )

            print("\nDatabase Tables:")

            for item in tables_result.content:
                if item.type == "text":
                    print(item.text)

            # Step 7: Test get_database_schema tool
            schema_result = await session.call_tool(
                "get_database_schema",
                arguments={}
            )

            print("\nDatabase Schema:")

            for item in schema_result.content:
                if item.type == "text":
                    print(item.text)

            # Step 8: Test execute_readonly_query tool
            query_result = await session.call_tool(
                "execute_readonly_query",
                arguments={
                    "sql_query": """
                        SELECT COUNT(*) AS total_sales 
                        FROM sales;
                    """
                }
            )

            print("\nSQL Query Result:")

            for item in query_result.content:
                if item.type == "text":
                    print(item.text)


# Step 9: Run the main function
if __name__ == "__main__":
    asyncio.run(main())
