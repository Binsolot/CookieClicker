# ------- Package Import ------- #
import websocket
import requests
import json
import time
# ------- Package Import ------- #

CLICK_SHIMMERS_JS = """
(() => {
    const shimmers = [...Game.shimmers];
    shimmers.forEach(s => s.pop());
    return shimmers.length;
})()
"""


class CDPClient:


    def __init__(self, port: int = 9222, title_suffix: str = "Cookie Clicker"):
        tabs = requests.get(f"http://localhost:{port}/json").json()
        tab = next(t for t in tabs if t["type"] == "page" and t["title"].endswith(title_suffix))
        self.conn = websocket.create_connection(tab["webSocketDebuggerUrl"])
        self._next_id = 1


    def evaluate(self, expression: str):
        msg_id, self._next_id = self._next_id, self._next_id + 1
        self.conn.send(json.dumps({
            "id": msg_id,
            "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True},
        }))
        response = json.loads(self.conn.recv())
        if response["id"] != msg_id:
            raise RuntimeError("Response id mismatch")
        result = response["result"]
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"])
        return result["result"].get("value")


    def close(self):
        self.conn.close()


client= CDPClient()
try:
    while True:
        clicked = client.evaluate(CLICK_SHIMMERS_JS)
        time.sleep(0.5 if clicked else 5)
finally:
    client.close()
