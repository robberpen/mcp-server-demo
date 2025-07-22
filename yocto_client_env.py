import asyncio

#  uv run python ./yocto_client.py

from fastmcp import Client
from fastmcp.client.logging import LogMessage
import os
import os
from fastmcp.client.transports import StdioTransport



async def log_handler(message: LogMessage):
    level = message.level.upper()
    logger = message.logger or 'server'
    data = message.data
    print(f"[{level}] {logger}: {data}")

async def test():
    #required_vars = ["BBPATH", "PYTHONPATH"]
    #env = {
    #    var: os.environ[var] 
    #    for var in required_vars 
    #    if var in os.environ
    #}
    # Pass all environment variables
    env = dict(os.environ)
    transport = StdioTransport(
        command="uv",
        args=["run", "python", "yocto_server.py"],
        env=env
    )
    client = Client(transport, log_handler=log_handler)
    #client = Client("yocto_server.py", log_handler=log_handler)
    print(f'Client ENV: {os.environ.get("BBPATH")}')

    async with client:
        print(await client.ping())
        tools = await client.list_tools()
        print("Tools:", tools)
        #res = await client.call_tool("yocto_build_image", {"recipe": "kernel"})
        res = await client.call_tool("yocto_build_image", {"recipe": "sera-demo"})
        print("Result:", res)
        res = await client.call_tool("get_recipe_build_log_dir", {"recipe": "sera-demo"})
        print("Result:", res)

asyncio.run(test())

