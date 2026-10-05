Usage
=============================

Launching lys in remote mode
-----------------------------------

*lys* accepts commands from other processes only when it is launched with ``--remote`` option::

    python -m lys --remote

When lys starts listening, the message below is shown in the lys log::

    lys remote: listening with label 12345 (/tmp/lys-remote-user-12345)

Each lys in remote mode has a *label*, which is used to select lys when several lys are running.
By default, the process id is used as the label. You can give your own label after ``--remote``::

    python -m lys --remote expA

The commands sent from other processes are shown in the lys log with ``[remote] >`` prefix, and they are also added to the command history.
The variables defined by the commands are shared with the lys command line, and vice versa.

.. note::

    The local socket can be accessed only by the same user on the same computer. Note that any Python code can be executed through it.

Controlling lys from Claude Code
-----------------------------------

After :doc:`install`, launch lys in remote mode and start Claude Code. Then ask Claude in natural language, for example:

- "Display a 2D Gaussian in lys and show me the graph."
- "Look at the front graph in lys and make the axis labels larger."
- "Fit the data in variable w with a Gaussian and plot the result."

Claude uses the tools below:

=================== ===================================================================================
Tool                Description
=================== ===================================================================================
``lys_exec``        Execute Python code in the lys shell and return the output (and the value of the last expression).
``lys_image``       Return a PNG image of a lys canvas, a matplotlib figure, or a Qt widget. Claude can see the image directly. The front canvas is used by default.
``lys_list``        List variables in the lys shell.
``lys_instances``   List running lys with their label, process id, and home directory.
``lys_select``      Select lys to be controlled by its label or home directory.
=================== ===================================================================================

If only one lys is running in remote mode, it is selected automatically.
If several lys are running, tell Claude which lys should be used, for example "Use lys launched in ~/data/expA" or "Use lys with label expA".
Claude finds it by ``lys_instances`` and selects it by ``lys_select``.

Controlling lys from command line
-----------------------------------

``lys-remote`` command sends commands to lys by hand. It is useful to check the connection::

    lys-remote --instances                          # list running lys
    lys-remote "w = Wave(np.random.rand(50, 50)); display(w)"
    lys-remote -f script.py                         # execute file
    lys-remote --image out.png                      # save image of the front canvas
    lys-remote --image out.png --target g           # save image of canvas/figure g
    lys-remote --list                               # list variables in lys shell

If several lys are running, select lys by its label or home directory with ``-l`` option, or by ``LYS_REMOTE`` environment variable::

    lys-remote -l expA "a + 1"
    lys-remote -l ~/data/expA "a + 1"
    LYS_REMOTE=expA lys-remote "a + 1"

Controlling lys from Python
-----------------------------------

:class:`lys_mcp.client.LysClient` can be used from Python scripts and Jupyter notebook::

    from lys_mcp.client import LysClient

    with LysClient() as c:                  # or LysClient("expA")
        res = c.exec("a = 1\na + 1")
        print(res["result"])                # 2

See :doc:`api` for details.
