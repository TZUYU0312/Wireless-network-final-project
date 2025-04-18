#災戶 H2，連線並接收資源
# client_H2.py
import socket
import json

HOST = 'localhost'
PORT = 9000
my_name = 'H2'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(my_name.encode())
    data = s.recv(1024)
    result = json.loads(data.decode())
    if 'resource' in result:
        print(f"[{my_name}] ✅ 收到資源：{result['resource']} 單位")
    else:
        print(f"[{my_name}] ❌ 錯誤：{result.get('error', '未知錯誤')}")
