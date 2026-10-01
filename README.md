# lys_mcp

Control [lys](https://github.com/lys-devel/lys) from Claude Code (MCP) or the command line.

```
Claude Code ⇄ (MCP) ⇄ lys_mcp.server ⇄ lys_mcp.client ⇄ (local socket) ⇄ lys --remote
```

## Install

```
pip install -e .          # client only (lys-remote command)
pip install -e ".[mcp]"   # with MCP server (lys-mcp command)
```

## Launch lys

```
python -m lys --remote          # label = process id
python -m lys --remote expA     # label = expA
```

## Command line

```
lys-remote --instances                 # list running lys
lys-remote "w = Wave(np.random.rand(50, 50)); display(w)"
lys-remote -l expA "a + 1"             # select lys by label (or LYS_REMOTE=expA)
lys-remote --image out.png             # image of the front canvas
lys-remote --image out.png --target g  # image of canvas/figure g
lys-remote --list                      # variables in lys shell
```

If only one lys is running, it is selected automatically.

## Claude Code

```
claude mcp add --scope user lys -- lys-mcp
```

Tools: `lys_instances`, `lys_select`, `lys_exec`, `lys_image`, `lys_list`.
