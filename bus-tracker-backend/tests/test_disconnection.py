import trio
from trio_websocket import WebSocketConnection


async def test_webclient(
        webclient_socket: WebSocketConnection, autojump_clock
):
    await webclient_socket.aclose()  # skip empty bus info
    await trio.sleep(1)  # wait while server send data in closed socket
    assert True  # check if no exceptions happens in server and suite runs fine
