"""
Client of lys remote server (lys/localPlugins/Remote.py in lys).

This module does not depend on lys and Qt, so that it can be used from MCP server and command line.
lys should be launched with --remote option, e.g. python -m lys --remote

Each lys has a label (python -m lys --remote LABEL, default is its process id).
If only one lys is running, it is selected automatically. Otherwise, select it by --label or LYS_REMOTE environment variable.

lys on another computer can be used when it is launched with --port option (python -m lys --remote --port 8765).
Select it by "tcp://<host>:<port>" (e.g. -l tcp://192.168.1.4:8765 or LYS_REMOTE=tcp://192.168.1.4:8765).
If lys is launched with --token, give the token by --token or LYS_REMOTE_TOKEN environment variable.

Command line usage::

    lys-remote --instances                    # list running lys
    lys-remote "a = 1; a + 1"                 # execute code and print the result
    lys-remote -l expA "a = 1; a + 1"         # execute code in lys launched with --remote expA
    lys-remote -l ~/data/expA "a + 1"         # execute code in lys launched in ~/data/expA
    lys-remote -f script.py                   # execute file
    lys-remote --image out.png                # save image of the front canvas
    lys-remote --image out.png --target g     # save image of the canvas/figure g
    lys-remote --list                         # list variables in shell
    lys-remote -l tcp://192.168.1.4:8765 "a"  # lys on another computer launched with --port 8765
"""

import os
import sys
import glob
import json
import base64
import socket
import getpass
import tempfile
import argparse
import itertools

PROTOCOL = 1


def _prefix():
    return "lys-remote-" + getpass.getuser() + "-"


def serverName(label):
    """Return the name of the local socket for *label*. The same rule as serverName in lys/localPlugins/Remote.py."""
    if sys.platform == "win32":
        return _prefix() + label
    return os.path.join(tempfile.gettempdir(), _prefix() + label)


def listLabels():
    """Return the labels of running lys."""
    if sys.platform == "win32":
        names = [n for n in os.listdir("\\\\.\\pipe\\") if n.startswith(_prefix())]
    else:
        names = [os.path.basename(p) for p in glob.glob(os.path.join(tempfile.gettempdir(), _prefix() + "*"))]
    labels = [n[len(_prefix()):] for n in names]
    return sorted([label for label in labels if _isAlive(label)])


def _isTcp(label):
    return label.startswith("tcp://")


def _parseTcp(label):
    """Return (host, port) from "tcp://host:port"."""
    host, _, port = label[len("tcp://"):].rstrip("/").rpartition(":")
    if not host or not port.isdigit():
        raise LysRemoteError("Invalid address " + label + ". Use tcp://<host>:<port>, e.g. tcp://192.168.1.4:8765")
    return host.strip("[]"), int(port)


def _isAlive(label):
    try:
        _connect(serverName(label), timeout=1).close()
        return True
    except OSError:
        return False


def resolveLabel(label=None):
    """
    Return the label of lys to be connected.

    *label* can be the label or the home directory of lys (the directory where lys was launched), or "tcp://<host>:<port>" for lys on another computer.
    If *label* is None, LYS_REMOTE environment variable is used. If it is not set, the running lys is selected when only one lys is running.
    """
    label = label or os.environ.get("LYS_REMOTE")
    if label:
        return findLabel(label)
    labels = listLabels()
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 0:
        raise LysRemoteError("No lys is running. Launch lys with --remote option.")
    raise LysRemoteError("Several lys are running: " + ", ".join(labels) + ". Select one of them by its label.")


def findLabel(key):
    """Return the label of lys whose label or home directory is *key*. If not found, *key* is returned."""
    if _isTcp(key):
        return key
    labels = listLabels()
    if key in labels:
        return key
    path = os.path.realpath(os.path.expanduser(key))
    for info in instances():
        if "home" in info and os.path.realpath(info["home"]) == path:
            return info["label"]
    return key


class LysRemoteError(Exception):
    pass


class LysClient:
    """
    Client to send requests to lys.

    Args:
        label(str): The label of lys. See :func:`resolveLabel`.
        timeout(float): Timeout in seconds.
        token(str): The token for lys launched with --token. If None, LYS_REMOTE_TOKEN environment variable is used.

    Example::

        with LysClient() as c:
            res = c.exec("a = 1; a + 1")
            print(res["result"])   # "2"
    """

    _ids = itertools.count(1)

    def __init__(self, label=None, timeout=600, token=None):
        self._label = label
        self._timeout = timeout
        self._token = token or os.environ.get("LYS_REMOTE_TOKEN")
        self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def label(self):
        return self._label

    def connect(self):
        self._label = resolveLabel(self._label)
        if _isTcp(self._label):
            host, port = _parseTcp(self._label)
            try:
                self._conn = _TcpConnection(host, port, self._timeout)
            except OSError as e:
                raise LysRemoteError("Cannot connect to lys at " + self._label + " (" + str(e) + "). Check that lys is launched with --port " + str(port) + " and the firewall allows the port.") from e
            return
        try:
            self._conn = _connect(serverName(self._label), self._timeout)
        except OSError as e:
            raise LysRemoteError("No lys is found for label or home directory " + self._label + ". Check running lys by lys-remote --instances.") from e

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def request(self, op, **kwargs):
        """Send a request and return the response as dict."""
        if self._conn is None:
            self.connect()
        req = dict(kwargs, op=op, id=next(self._ids))
        if self._token is not None:
            req["token"] = self._token
        self._conn.send(json.dumps(req).encode("utf-8") + b"\n")
        return json.loads(self._conn.readline().decode("utf-8"))

    def exec(self, code):
        """Execute code in lys shell. The value of the last expression is returned as 'result'."""
        return self.request("exec", code=code)

    def image(self, target=None, dpi=100):
        """Return response with png image (base64) of canvas, matplotlib figure or widget as 'image'."""
        return self.request("image", target=target, dpi=dpi)

    def list(self):
        """Return variables in lys shell as 'result'."""
        return self.request("list")

    def info(self):
        """Return label, pid, home directory and protocol version of lys."""
        return self.request("info")


def _connect(name, timeout):
    if sys.platform == "win32":
        return _PipeConnection(name)
    return _UnixConnection(name, timeout)


class _SocketConnection:
    def __init__(self, sock):
        self._sock = sock
        self._file = self._sock.makefile("rb")

    def send(self, data):
        self._sock.sendall(data)

    def readline(self):
        line = self._file.readline()
        if not line:
            raise LysRemoteError("Connection closed by lys.")
        return line

    def close(self):
        self._file.close()
        self._sock.close()


class _UnixConnection(_SocketConnection):
    def __init__(self, path, timeout):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect(path)
        except OSError:
            sock.close()
            raise
        super().__init__(sock)


class _TcpConnection(_SocketConnection):
    def __init__(self, host, port, timeout):
        sock = socket.create_connection((host, port), timeout=min(timeout, 10))
        sock.settimeout(timeout)
        super().__init__(sock)


class _PipeConnection:
    def __init__(self, name):
        self._file = open("\\\\.\\pipe\\" + name, "r+b", buffering=0)

    def send(self, data):
        self._file.write(data)

    def readline(self):
        line = b""
        while not line.endswith(b"\n"):
            c = self._file.read(1)
            if not c:
                raise LysRemoteError("Connection closed by lys.")
            line += c
        return line

    def close(self):
        self._file.close()


def formatResponse(res):
    """Format response as text."""
    txt = ""
    if res.get("stdout"):
        txt += res["stdout"]
    if res.get("stderr"):
        txt += "[stderr]\n" + res["stderr"]
    if not res.get("ok"):
        txt += "[error]\n" + res.get("error", "")
    elif res.get("result") is not None:
        txt += res["result"]
    return txt


def instances():
    """
    Return the information of running lys as list of dict.

    lys on another computer is included when it is given by LYS_REMOTE environment variable.
    """
    labels = listLabels()
    remote = os.environ.get("LYS_REMOTE")
    if remote and _isTcp(remote):
        labels.append(remote)
    res = []
    for label in labels:
        try:
            with LysClient(label, timeout=5) as c:
                info = c.info()
            if not info.get("ok", True):
                raise LysRemoteError(info.get("error"))
            if _isTcp(label):
                info["label"] = label  # address is used to select lys on another computer
            if info.get("protocol") != PROTOCOL:
                info["warning"] = "Protocol version mismatch (lys: " + str(info.get("protocol")) + ", lys_mcp: " + str(PROTOCOL) + ")"
        except Exception as e:
            info = {"label": label, "error": str(e)}
        res.append({key: info[key] for key in ["label", "pid", "home", "warning", "error"] if key in info})
    return res


def main():
    parser = argparse.ArgumentParser(prog="lys-remote", description="Send commands to lys launched with --remote option.")
    parser.add_argument("code", nargs="?", help="Python code to be executed in lys")
    parser.add_argument("-l", "--label", help="Label or home directory of lys, or tcp://<host>:<port> for lys on another computer (default: LYS_REMOTE environment variable, or the only running lys)")
    parser.add_argument("--token", help="Token for lys launched with --token (default: LYS_REMOTE_TOKEN environment variable)")
    parser.add_argument("-f", "--file", help="Python file to be executed in lys")
    parser.add_argument("--image", metavar="PNG", help="Save image of the target to PNG")
    parser.add_argument("--target", help="Expression of canvas/figure/widget for --image (default: frontCanvas())")
    parser.add_argument("--dpi", type=int, default=100)
    parser.add_argument("--list", action="store_true", help="List variables in lys shell")
    parser.add_argument("--instances", action="store_true", help="List running lys")
    args = parser.parse_args()

    if args.instances:
        print(json.dumps(instances(), indent=1, ensure_ascii=False))
        return

    code = args.code
    if args.file is not None:
        with open(args.file, encoding="utf-8") as f:
            code = f.read()
    if code is None and args.image is None and not args.list:
        code = sys.stdin.read()

    try:
        with LysClient(args.label, token=args.token) as c:
            ok = True
            if code is not None:
                res = c.exec(code)
                print(formatResponse(res))
                ok &= res["ok"]
            if args.image is not None:
                res = c.image(args.target, args.dpi)
                if res["ok"]:
                    with open(args.image, "wb") as f:
                        f.write(base64.b64decode(res["image"]))
                    print("Saved", args.image)
                else:
                    print(formatResponse(res))
                ok &= res["ok"]
            if args.list:
                res = c.list()
                print(formatResponse(res))
                ok &= res["ok"]
    except LysRemoteError as e:
        print(e, file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
