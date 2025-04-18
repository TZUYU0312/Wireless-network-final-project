#指揮中心：解 LP 最佳化後，根據需求分發資源給災戶
# run_server.py
import socket
import json
import cvxpy as cp
import networkx as nx
from collections import defaultdict

HOST = 'localhost'
PORT = 9000

import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 不需真的連線，這裡只是用來抓預設網卡的 IP
        s.connect(('8.8.8.8', 80))  # Google DNS 作為目標
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

print("🧠 我的 IP 是：", get_local_ip())

# 建立圖
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

# LP 變數
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

# 彙總結果：每戶應收總流量
allocation = {k: demands[k] for k in demands}

# 啟動 socket server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("[Server] 指揮中心啟動，等待災戶連線...")
    for _ in range(len(allocation)):
        conn, addr = s.accept()
        with conn:
            print(f"[Server] 已連線：{addr}")
            name = conn.recv(1024).decode()
            if name in allocation:
                data = {'resource': allocation[name]}
                conn.sendall(json.dumps(data).encode())
                print(f"[Server] 已送出 {allocation[name]} 單位資源給 {name}")
            else:
                conn.sendall(json.dumps({'error': '未知災戶'}).encode())
