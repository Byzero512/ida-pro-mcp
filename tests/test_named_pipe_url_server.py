import importlib.util
import queue
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class _Connection:
    def __init__(self) -> None:
        self._incoming: queue.Queue[bytes] = queue.Queue()
        self._peer: _Connection | None = None

    def write(self, data: bytes) -> None:
        assert self._peer is not None
        self._peer._incoming.put(data)

    def read(self) -> bytes:
        return self._incoming.get(timeout=2)

    def close(self) -> None:
        pass


class _Listener:
    def __init__(self) -> None:
        self._pending: queue.Queue[_Connection] = queue.Queue()

    def accept(self) -> _Connection:
        return self._pending.get(timeout=2)

    def close(self) -> None:
        pass


class _SyncNamedPipe:
    listeners: dict[str, _Listener] = {}

    @classmethod
    def listen(cls, pipe: str, *, first_instance: bool = False) -> _Listener:
        if first_instance and pipe in cls.listeners:
            raise OSError(5, "pipe already exists")
        listener = _Listener()
        cls.listeners[pipe] = listener
        return listener

    @classmethod
    def connect(cls, pipe: str, timeout_seconds: float = 120.0) -> _Connection:
        listener = cls.listeners[pipe]
        client = _Connection()
        server = _Connection()
        client._peer = server
        server._peer = client
        listener._pending.put(server)
        return client


def _load_plugin_module():
    idaapi = types.ModuleType("idaapi")
    idaapi.Form = type("Form", (), {})
    idaapi.action_handler_t = type("action_handler_t", (), {})
    idaapi.plugin_t = type("plugin_t", (), {})
    idaapi.PLUGIN_KEEP = 1

    ida_kernwin = types.ModuleType("ida_kernwin")
    ida_kernwin.UI_Hooks = type("UI_Hooks", (), {})

    module_path = (
        Path(__file__).parents[1] / "src" / "ida_pro_mcp" / "ida_mcp.py"
    )
    spec = importlib.util.spec_from_file_location("_ida_mcp_plugin_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    stubs = {
        "idaapi": idaapi,
        "ida_kernwin": ida_kernwin,
        "ida_netnode": types.ModuleType("ida_netnode"),
    }
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


class NamedPipeUrlServerTests(unittest.TestCase):
    def setUp(self) -> None:
        _SyncNamedPipe.listeners.clear()

    def test_serves_url_with_synchronous_ifastmcp_api(self) -> None:
        module = _load_plugin_module()
        ifastmcp = types.ModuleType("ifastmcp")
        ifastmcp.NamedPipe = _SyncNamedPipe
        pipe_name = "idamcp$C:/Users/unk/Desktop/AI-worker/hwtools/hdcd.i64"
        url = "http://127.0.0.1:50003/mcp"
        server = module._NamedPipeUrlServer(pipe_name, url)

        with patch.dict(sys.modules, {"ifastmcp": ifastmcp}):
            server.start()
            try:
                connection = _SyncNamedPipe.connect(pipe_name)
                self.assertEqual(connection.read(), url.encode("utf-8"))
                connection.close()
            finally:
                server.stop()

        self.assertFalse(server._thread.is_alive())


if __name__ == "__main__":
    unittest.main()
