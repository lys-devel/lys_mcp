"""
MCP server to control lys from Claude Code.

lys should be launched with --remote option (python -m lys --remote).
This server is launched by Claude Code and communicates with lys through :mod:`lys_mcp.client`.

Register to Claude Code::

    claude mcp add --scope user lys -- lys-mcp
"""

import json
import base64

try:
    from mcp.server.mcpserver import MCPServer, Image  # mcp >= 2
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer, Image  # mcp 1.x

from .client import LysClient, LysRemoteError, formatResponse, instances, findLabel

mcp = MCPServer("lys")
_label = None  # label of lys selected by lys_select


def _request(op, **kwargs):
    try:
        with LysClient(_label) as c:
            return c.request(op, **kwargs)
    except LysRemoteError as e:
        return {"ok": False, "error": str(e) + "\nUse lys_instances and lys_select to choose lys."}


@mcp.tool()
def lys_instances() -> str:
    """
    List running lys (launched with --remote) with their label, process id, and home directory.

    lys on another computer is listed only when LYS_REMOTE environment variable is set to "tcp://<host>:<port>".

    If several lys are running, select one of them by lys_select before using other tools.
    """
    res = instances()
    if len(res) == 0:
        return "No lys is running. Ask the user to launch lys with: python -m lys --remote (or add --port 8765 for lys on another computer, and connect by lys_select with tcp://<host>:8765)"
    return json.dumps({"selected": _label, "instances": res}, indent=1, ensure_ascii=False)


@mcp.tool()
def lys_select(label: str) -> str:
    """
    Select lys to be controlled by its label or its home directory (the directory where lys was launched, see lys_instances).

    lys on another computer launched with --port can be selected by "tcp://<host>:<port>", e.g. tcp://192.168.1.4:8765.
    Its token is given by LYS_REMOTE_TOKEN environment variable of the MCP server.

    Empty string clears the selection.
    """
    global _label
    _label = findLabel(label) if label else None
    if _label is None:
        return "Selection cleared. The only running lys is used automatically."
    res = _request("info")
    if not res["ok"]:
        _label = None
        return formatResponse(res)
    return "Selected lys: label=" + str(res["label"]) + ", pid=" + str(res["pid"]) + ", home=" + str(res["home"])


@mcp.tool()
def lys_exec(code: str) -> str:
    """
    Execute Python code in the shell of the running lys GUI and return the output.

    The shell namespace is shared with the lys command line (from lys import * is already done).
    If the last statement is an expression, its repr is returned, as in Jupyter.
    Code runs in the GUI main thread, so avoid very long computations.
    Examples: "w = Wave(np.random.rand(100, 100)); display(w)", "frontCanvas().getWaveData()".
    """
    res = _request("exec", code=code)
    return formatResponse(res) or "(no output)"


@mcp.tool()
def lys_image(target: str = "", dpi: int = 100) -> Image | str:
    """
    Return a PNG image of a lys canvas, matplotlib Figure, or Qt widget.

    target is a Python expression evaluated in the lys shell. If empty, frontCanvas() (the most recently focused canvas) is used.
    """
    res = _request("image", target=target or None, dpi=dpi)
    if not res["ok"]:
        return formatResponse(res)
    return Image(data=base64.b64decode(res["image"]), format="png")


@mcp.tool()
def lys_list() -> str:
    """List variables in the lys shell with their types (and shape/dtype for arrays and Waves)."""
    return formatResponse(_request("list"))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
