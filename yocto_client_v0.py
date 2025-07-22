import asyncio

#  uv run python ./yocto_client.py
from fastmcp import Client
async def test():
    client = Client("yocto_server.py")
    async with client:
        print(await client.ping())
        tools = await client.list_tools()
        print("Tools:", tools)
        #res = await client.call_tool("get_compile_log_dir", {"recipe": "kernel"})
        res = await client.call_tool("yocto_build_image")
        print("Result:", res)

asyncio.run(test())

