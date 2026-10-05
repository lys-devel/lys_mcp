# lys_mcp

lys_mcp enables [Claude Code](https://claude.com/claude-code) and other processes to control [lys](https://github.com/lys-devel/lys), an interactive multi-dimensional data analysis and visualization platform. With lys_mcp, Claude can execute Python commands in lys and see the graphs drawn by lys and matplotlib.

```
Claude Code ⇄ (MCP) ⇄ lys-mcp ⇄ (local socket) ⇄ lys (python -m lys --remote)
```

Check out the [documentation](https://lys-devel.github.io/lys_mcp/index.html) for more information.

## Installation

```
git clone https://github.com/lys-devel/lys_mcp.git
cd lys_mcp
pip install -e ".[mcp]"
claude mcp add --scope user lys -- lys-mcp
```

Then launch lys in remote mode:

```
python -m lys --remote
```

See the [install documentation](https://lys-devel.github.io/lys_mcp/install.html) and [usage](https://lys-devel.github.io/lys_mcp/usage.html) for details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
