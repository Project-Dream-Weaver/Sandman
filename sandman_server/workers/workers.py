import typing
import asyncio
import importlib

from aiohttp import ClientWebSocketResponse

from .websocket import AutoShardedWorker
from .responses import dumps_data
from ..utils.helpers import find_free_port
from ..adapters.asgi import ASGIAdapter
from ..adapters.wsgi import WSGIAdapter
from ..adapters.raw import RawAdapter


def _get_app(app_path: str) -> typing.Callable:
    fp, app_name = app_path.split(":")
    fp = fp.replace("/", ".").replace("\\", ".")
    module = importlib.import_module(fp)
    app = getattr(module, app_name, None)
    if app is None:
        raise ImportError("No app named {} in file {}".format(app_name, fp))
    return app


class Worker:
    def __init__(
            self,
            app: str,
            host_addr: str,
            port: int,
            shard_count: int,
            sandman_path: str,
            failed_shard_callback: typing.Callable,
            adapter: typing.Union[WSGIAdapter, ASGIAdapter, RawAdapter],
    ):
        self.host_addr = host_addr
        self.port = port
        self._app = _get_app(app_path=app)

        self._free_port = 1234 # find_free_port()
        self._exe_path = sandman_path
        self._clear_to_shard = False

        worker_addr = "ws://127.0.0.1:{}/workers".format(self._free_port)
        self._shard_count = shard_count
        self.shard_manager = AutoShardedWorker(
            binding_addr=worker_addr,
            request_callback=self._on_http_request,
            msg_callback=self._on_internal_message,
            shard_count=shard_count,
            failed_callback=failed_shard_callback
        )

        self._adapter = adapter

    async def run(self):
        #await self._spawn_rust()
        #await asyncio.sleep(1)
        #if self._clear_to_shard:
            await self.shard_manager.run()

    async def _spawn_rust(self):
        raise NotImplementedError()

    async def _on_http_request(self, ws: ClientWebSocketResponse, msg: dict):
        outgoing = await self._adapter(self._app, msg)
        await ws.send_bytes(dumps_data(outgoing.to_dict()))

    async def _on_internal_message(self, ws: ClientWebSocketResponse, msg: str):
        pass








