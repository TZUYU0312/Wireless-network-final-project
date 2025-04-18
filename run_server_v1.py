# 多執行緒處理：使用 threading.Thread 處理每個 client。

# JSON 通訊格式：client 傳送格式 { "name": "H1" }，server 回傳格式 { "resource": 8 } 或 { "error": "未知災戶" }。

# 保留 LP 計算邏輯：指揮中心在啟動時就先完成資源配置。

# 支援同時連線多災戶：不會依序等待。
# run_server.py（多 client 多任務 + JSON 格式）
import socket
import json
import cvxpy as cp
import networkx as nx
import threading

HOST = '0.0.0.0'
PORT = 9000

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

print("🧠 我的 IP 是：", get_local_ip())

# 建立圖與流量 LP 求解
G = nx.DiGraph()
edges = [
    ('S', 'A', {'capacity': 15, 'cost': 5}),
    ('S', 'C', {'capacity': 10, 'cost': 3}),
    ('A', 'B', {'capacity': 10, 'cost': 2}),
    ('C', 'D', {'capacity': 10, 'cost': 4}),
    ('B', 'H1', {'capacity': 10, 'cost': 1}),
    ('D', 'H2', {'capacity': 10, 'cost': 1}),
    ('A', 'D', {'capacity': 5, 'cost': 3}),
    ('C', 'B', {'capacity': 5, 'cost': 2}),
]
G.add_edges_from([(u, v, attr) for u, v, attr in edges])

demands = {'H1': 8, 'H2': 7}
commodities = list(demands.keys())
edges = list(G.edges())
nodes = list(G.nodes())

flow_vars = {
    (k, u, v): cp.Variable(nonneg=True)
    for k in commodities for (u, v) in edges
}

constraints = []
for (u, v) in edges:
    total_flow = cp.sum([flow_vars[k, u, v] for k in commodities])
    constraints.append(total_flow <= G[u][v]['capacity'])

for k in commodities:
    for n in nodes:
        inflow = cp.sum([flow_vars[k, u, n] for (u, v) in edges if v == n])
        outflow = cp.sum([flow_vars[k, n, v] for (u, v) in edges if u == n])
        if n == 'S':
            constraints.append(outflow - inflow == demands[k])
        elif n == k:
            constraints.append(inflow - outflow == demands[k])
        else:
            constraints.append(inflow == outflow)

objective = cp.Minimize(cp.sum([
    G[u][v]['cost'] * flow_vars[k, u, v]
    for (k, u, v) in flow_vars
]))
prob = cp.Problem(objective, constraints)
prob.solve()

allocation = {k: demands[k] for k in demands}


# 處理每個 client 的執行緒
def handle_client(conn, addr):
    print(f"[Server] 已連線：{addr}")
    try:
        msg = conn.recv(1024).decode()
        data = json.loads(msg)
        name = data.get("name")

        if name in allocation:
            response = {'resource': allocation[name]}
            print(f"[Server] 已送出 {allocation[name]} 單位資源給 {name}")
        else:
            response = {'error': '未知災戶'}
            print(f"[Server] 無法識別災戶：{name}")

        conn.sendall(json.dumps(response).encode())
    except Exception as e:
        print(f"[Server] 發生錯誤：{e}")
    finally:
        conn.close()


# 啟動多 client server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("[Server] 指揮中心啟動，等待災戶連線...")

    while True:
        conn, addr = s.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()
