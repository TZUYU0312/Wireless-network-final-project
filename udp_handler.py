# 📁 disaster_alert_web/udp_handler.py
import socket
import uuid
import json
import time

NODE_ID = None
PORT = None
NEIGHBORS = []
SOCKETIO = None

RECEIVED = set()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def init(node_id, port, neighbors, socketio):
    global NODE_ID, PORT, NEIGHBORS, SOCKETIO
    NODE_ID = node_id
    PORT = port
    NEIGHBORS = neighbors
    SOCKETIO = socketio
    sock.bind(("0.0.0.0", PORT))

def create_message(content, ttl=3):
    return {
        "msg_id": str(uuid.uuid4()),
        "sender": NODE_ID,
        "content": content,
        "ttl": ttl,
        "timestamp": time.strftime("%H:%M:%S")
    }

def send_message(message, exclude_addr=None):
    msg_bytes = json.dumps(message).encode()
    for ip, port in NEIGHBORS:
        if exclude_addr and (ip, port) == exclude_addr:
            continue
        sock.sendto(msg_bytes, (ip, port))

def handle_message(data, addr):
    try:
        message = json.loads(data.decode())
    except:
        return
    if message[\"msg_id\"] in RECEIVED:
        return
    RECEIVED.add(message[\"msg_id\"])

    # 顯示在本節點介面
    SOCKETIO.emit(\"new_message\", message)

    if message[\"ttl\"] > 0:
        message[\"ttl\"] -= 1
        send_message(message, exclude_addr=addr)

def receive_loop():
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            handle_message(data, addr)
        except:
            pass
