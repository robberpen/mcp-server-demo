#!/usr/bin/env python
import subprocess
import os,time
from pathlib import Path
# create a mcp server class to run bitbake commands
# this class will provided async @tool to run bitbake commands and return the results
# it will also handle the environment variables and paths
from mcp.server.fastmcp.prompts import base
from mcp.server.fastmcp import Context, FastMCP
import asyncio
import os
import shlex
mcp = FastMCP(name="Yocto Bitbake MCP", description="MCP for running Yocto Bitbake commands", version="0.1.0")
with open("/tmp/mcp_yocto.log", "a") as logfile:
    print(f"Starting MCP server at {time.strftime('%Y-%m-%d %H:%M:%S')} env: {os.environ.get('PATH')}", file=logfile, flush=True)
#@mcp.tool(name="yocto_build_image", description="Build Yocto image using bitbake")
#@base
@mcp.tool(name="yocto_build_image", description="Build Yocto image using bitbake")
async def yocto_build_image(ctx: Context, recipe: str = "sera-demo") -> str:
    """Asynchronously run BitBake to build a Yocto recipe.

    * Streams environment info and progress via ``ctx.debug`` / ``ctx.report_progress``.
    * Returns the last 20 lines of *stdout* on success, or the last 100 lines of
      *stderr* on failure.
    """

    # --- pre‑flight ---------------------------------------------------------
    await ctx.debug(f"BBPATH = {os.environ.get('BBPATH')}")
    await ctx.debug(f"Building recipe: {recipe}")

    bb_exe = "/sera/share2/sera/SMARC/G700/src/poky/bitbake/bin/bitbake"
    cmd = [
        "python3",
        bb_exe,
        "-v",
        shlex.quote(recipe),  # basic shell‑escape for safety
        "-c",
        "install",
    ]

    # --- launch subprocess asynchronously ----------------------------------
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    # Read stdout as it comes in; you could parse for real progress tokens here
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        stdout_lines.append(line.rstrip())
        if len(stdout_lines) % 100 == 0:
            await ctx.report_progress(progress=None, message=f"{len(stdout_lines)} lines processed …")

    # Drain remaining stderr (if any) and wait for completion
    stderr_tail = await proc.stderr.read()
    if stderr_tail:
        stderr_lines.extend(stderr_tail.splitlines())
    await proc.wait()

    # --- final result -------------------------------------------------------
    if proc.returncode == 0:
        return "\n".join(stdout_lines[-20:]) or "Build completed successfully (no output)"
    else:
        return "\n".join(stderr_lines[-100:]) or f"BitBake exited with code {proc.returncode}"



@mcp.tool(name="get_recipe_build_log_dir", description="Build Yocto recipe using bitbake")
def get_recipe_build_log_dir(ctx: Context, recipe: str) -> str:
    ctx.debug(f'env: {os.environ.get("PYTHONPATH")}')
    return f'env: {os.environ.get("BBPATH")}'

class mcp_bitbake:
    def __init__(self, bbdir: str):
        if bbdir is None:
            self.bbdir = os.environ.get('BBPATH')
        else:
            self.bbdir = bbdir
        if self.bbdir is None:
            raise ValueError("BBPATH environment variable is not set and no directory provided.")

    @staticmethod
    async def yocto_build_image(ctx: Context) -> str:
        '''
        Execute "bitbake rity-demo-image" and check if the build is successful.
        Returns "Build completed successfully" if successful,
        otherwise returns the last 100 lines of stderr.
        '''
        #yyreturn "Build completed successfully"
        await ctx.debug(f' callback env: {os.environ.get("BBPATH")}')
        try:
            #["bitbake", "sera-demo"],
            #ctx.debug
            result = subprocess.run(
                ["python3", "/sera/share2/sera/SMARC/G700/src/poky/bitbake/bin/bitbake", "-v", "sera-demo", "-c", "install"],
                check=False,
                capture_output=True,
                text=True
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr

            if exit_code == 0:
                return "\n".join(stdout.splitlines(keepends=True)[-5:])
                #return f"Build completed successfully\n".join(stdout.splitlines()[-100:])
            else:
                #return "NGNG"
                return "\n".join(stdout.splitlines()[-100:])
        except subprocess.CalledProcessError as e:
            return f"bitbake exception {e}"
            #return "\n".join(e.stderr.splitlines()[-100:])
        return "Thanks"

    def get_recipe_build_log_dir(self, recipe: str) -> str:
        '''
        Get the build log directory for a given recipe.
        '''
        if not recipe:
            raise ValueError("Recipe name must be provided.")
        if self.bbdir is None:
            raise ValueError("BBPATH environment variable is not set.")
        # Assuming the build log directory is structured as follows:
        # /path/to/build/logs/<recipe>
        # use subprocess run  bitbake -e <recipe> | grep ^WORKDIR=
        try:
            result = subprocess.run(
                ["bitbake", "-e", recipe],
                check=True,
                capture_output=True,
                text=True
            )
            workdir_line = next(line for line in result.stdout.splitlines() if line.startswith("WORKDIR="))
            workdir = workdir_line.split("=", 1)[1].strip()
        except (subprocess.CalledProcessError, StopIteration):
            raise ValueError(f"Could not determine WORKDIR for recipe: {recipe}")    
        # check if the build log directory exists
        build_log_dir = Path(workdir) / "temp" / "log.do_compile"
        if not build_log_dir.exists():
            raise ValueError(f"Build log directory does not exist: {build_log_dir}")
        return str(build_log_dir)


if __name__ == "__main__":
    mcp.run(transport="stdio")
