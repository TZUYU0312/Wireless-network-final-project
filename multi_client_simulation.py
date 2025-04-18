# simulate_clients.py
import socket
import json
import threading
import time

HOST = '127.0.0.1'
PORT = 9000

# 要模擬的災戶清單（包含一個非法災戶）
clients = ['H1', 'H2', 'H3']

def simulate_client(name):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(json.dumps({'name': name}).encode())
            data = s.recv(1024).decode()
            response = json.loads(data)
            print(f"[Client:{name}] 收到回應：{response}")
    except Exception as e:
        print(f"[Client:{name}] 錯誤：{e}")

# 同時啟動所有 client
threads = []
for name in clients:
    t = threading.Thread(target=simulate_client, args=(name,))
    threads.append(t)
    t.start()
    time.sleep(0.2)  # 小間隔模擬較真實的連線情況

# 等待所有 thread 結束
for t in threads:
    t.join()
