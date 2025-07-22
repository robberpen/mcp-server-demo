from mcp.server.fastmcp import FastMCP
import subprocess
import os

mcp = FastMCP(name="YoctoLogFinder")

@mcp.tool()
def get_compile_log_dir(recipe: str) -> str:
    """
    Return the temp directory path containing compile logs for
    the given Yocto recipe name.
    """
    """
    try:
        # 使用 bitbake -e RECIPE 取得 WORKDIR
        cmd = ["bitbake", "-e", recipe]
        env_out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return f"Error: unable to query recipe '{recipe}'"

    # 解析 WORKDIR
    workdir = None
    for line in env_out.splitlines():
        if line.startswith("WORKDIR="):
            workdir = line.split("=", 1)[1]
            break
    if not workdir:
        return f"Error: WORKDIR not found for recipe '{recipe}'"

    # temp/log.do_compile 位置
    temp_dir = os.path.join(workdir, "temp")
    if not os.path.isdir(temp_dir):
        return f"Error: temp directory not found at {temp_dir}"

    return temp_dir
    """
    return "/fake/yocto/kerenl/log/"

if __name__ == "__main__":
    mcp.run(transport="stdio")

