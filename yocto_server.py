#!/usr/bin/env python

# uv run python ./yocto_client_env.py
import subprocess
import os,time
from pathlib import Path
from mcp.server.fastmcp.prompts import base
from mcp.server.fastmcp import Context, FastMCP
import asyncio
import os
#mcp = FastMCP(name="Yocto Bitbake MCP", description="MCP for running Yocto Bitbake commands", version="0.1.0")
mcp = FastMCP(name="Yocto Bitbake MCP")
@mcp.tool(name="run_bitbake", description="Build Yocto recipes by bitbake")
async def run_bitbake(ctx: Context, recipe: str = "sera-demo") -> str:
    """Asynchronously run BitBake to build a Yocto recipe.
    * Streams environment info and progress via ``ctx.debug`` / ``ctx.report_progress``.
    * param:
        recipe: name of recipe to build
    * Returns the last 20 lines of *stdout* on success, or the last 100 lines of
      *stderr* on failure.

    for example - to build recipe "sera-demo" is to
      call tool run_bitbake(..., "sera-demo")

    """

    # --- pre‑flight ---------------------------------------------------------
    await ctx.debug(f"BBPATH = {os.environ.get('BBPATH')}")
    await ctx.debug(f"Building recipe: {recipe}")

    bb_exe = "/sera/share2/sera/SMARC/G700/src/poky/bitbake/bin/bitbake"
    cmd = [
        "python3",
        bb_exe,
        "-v",
        recipe,
        "-c",
        "install",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await ctx.report_progress(progress=0.0, message="Build started")

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    start_ts = time.time()
    last_report = start_ts
    try:
        while True:
            raw_line = await proc.stdout.readline()
            await ctx.debug(f"PTM processed...{time.time():.3f}")
            if not raw_line:
                break
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            stdout_lines.append(line)
            if len(stdout_lines) % 3 == 0:
                await ctx.report_progress(
                    progress=0.5, message=f"{len(stdout_lines)} lines processed..."
                )
                await ctx.debug(f"PTM processed...len{len(stdout_lines)}, {time.time():.3f}")
            now = time.time()
            if now - last_report > 60:
                elapsed = int(now - start_ts)
                await ctx.report_progress(
                    progress=0.5, message=f"Still building after {elapsed}s..."
                )
                await ctx.debug(f"PTM processed...Still building after, {elapsed:.3f}")
                last_report = now
        stderr_tail = await proc.stderr.read()
        if stderr_tail:
            stderr_str = stderr_tail.decode("utf-8", errors="replace")
            stderr_lines.extend(stderr_str.splitlines())
        await proc.wait()
    except asyncio.CancelledError:
        proc.kill()
        await proc.wait()
        raise

    await ctx.report_progress(progress=1.0, message="Build process complete")
    if proc.returncode == 0:
        return "\n".join(stdout_lines[-20:]) or "Build completed successfully (no output)"
    return "\n".join(stderr_lines[-100:]) or f"BitBake exited with code {proc.returncode}"



@mcp.tool(name="get_recipe_build_log_dir", description="Build Yocto recipe using bitbake")
async def get_recipe_build_log_dir(ctx: Context, recipe: str) -> str:
    if not recipe:
        raise ValueError("Recipe name must be provided.")
    cmd = ["bitbake", "-e", recipe]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        out_bytes, _ = await proc.communicate()
    except asyncio.CancelledError:
        proc.kill()
        await proc.wait()
        raise
    stdout = out_bytes.decode("utf-8", errors="replace")
    for line in stdout.splitlines():
        if line.startswith("WORKDIR="):
            workdir = line.split("=", 1)[1].strip()
            break
    else:
        raise ValueError(f"Could not determine WORKDIR for recipe: {recipe}")
    
    workdir = workdir.strip('"')
    if not workdir:
        raise ValueError("WORKDIR is empty or not set correctly.")
    if not os.path.isdir(workdir):
        raise ValueError(f"WORKDIR does not exist: {workdir}")
    build_log_dir = Path(workdir) / "temp" / "log.do_compile"

    if not build_log_dir.exists():
        raise ValueError(f"Build log directory does not exist: {build_log_dir}")
    return str(build_log_dir)



if __name__ == "__main__":
    mcp.run(transport="stdio")
