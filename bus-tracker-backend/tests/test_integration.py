import json

from trio_websocket import WebSocketConnection


async def test_integration(
        webclient_socket: WebSocketConnection,
        tracking_socket: WebSocketConnection,
        autojump_clock
):
    buses_msg = await webclient_socket.get_message()
    assert json.loads(buses_msg) == {"msgType": "Buses", "buses": []}

    visible_bus = {
        "busId": "007-1",
        "route": "007",
        "lat": 55.649882727955,
        "lng": 37.562481428086,
    }
    await tracking_socket.send_message(json.dumps(visible_bus))
    await tracking_socket.send_message(json.dumps({
        "busId": "008-1",
        "route": "008",
        "lat": -55.649882727955,
        "lng": -37.562481428086,
    }))

    buses = json.loads(await webclient_socket.get_message())
    assert len(buses["buses"]) == 0

    bounds = {
        "msgType": "newBounds",
        "data": {
            "west_lng": 37.5,
            "east_lng": 37.6,
            "north_lat": 55.7,
            "south_lat": 55.5,
        }
    }
    await webclient_socket.send_message(json.dumps(bounds))
    buses = json.loads(await webclient_socket.get_message())
    assert len(buses["buses"]) == 1
    assert buses["buses"][0] == visible_bus
