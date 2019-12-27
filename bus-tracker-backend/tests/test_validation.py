import json
from typing import Dict, Any

from trio_websocket import WebSocketConnection
import pytest


@pytest.mark.parametrize("msg,desired_resp", [
    (
            "some text",
            {"msgType": "Error", "errors": ["requires valid JSON"]}
    ),
    (
        json.dumps({"some": "json"}),
        {
            "msgType": "Error",
            "errors": ["Unexpected keys, ['data', 'msgType'] expected"]
        }
    ),
    (
        json.dumps({"msgType": "QwertyMessage", "data": None}),
        {
            "msgType": "Error",
            "errors": ["Unsupported msgType"]
        }
    ),
    (
        json.dumps({"msgType": "newBounds", "data": None}),
        {
            "msgType": "Error",
            "errors": ["invalid bounds data"]
        }
    ),
    (
        json.dumps({"msgType": "newBounds", "data": {"some": "json"}}),
        {
            "msgType": "Error",
            "errors": ["invalid bounds data"]
        }
    )

])
async def test_webclient(
        msg: str,
        desired_resp: Dict[str, Any],
        webclient_socket: WebSocketConnection
):
    await webclient_socket.get_message()  # skip empty bus info
    await webclient_socket.send_message(msg)
    msg = await webclient_socket.get_message()
    got = json.loads(msg)
    assert got == desired_resp


@pytest.mark.parametrize("msg,desired_resp", [
    (
        "obviously not a json",
        {"msgType": "Error", "errors": ["requires valid JSON"]}
    ),
    (
        json.dumps(None),
        {"msgType": "Error", "errors": ["invalid bus data"]}
    ),
    (
        json.dumps({"wrong": "json"}),
        {"msgType": "Error", "errors": ["invalid bus data"]}
    )
])
async def test_tracking(
        msg: str,
        desired_resp: Dict[str, Any],
        tracking_socket: WebSocketConnection
):
    await tracking_socket.send_message(msg)
    msg = await tracking_socket.get_message()
    got = json.loads(msg)
    assert got == desired_resp
