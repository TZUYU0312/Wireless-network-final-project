import networkx as nx
import matplotlib.pyplot as plt
import heapq
from collections import defaultdict

# 建立有向圖
G = nx.DiGraph()

# 節點與邊（容量/成本）
nodes = ['S', 'A', 'B', 'C', 'D', 'H1', 'H2']
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

G.add_nodes_from(nodes)
G.add_edges_from([(u, v, attr) for u, v, attr in edges])

# 需求設定
demands = {'H1': 8, 'H2': 7}
residual_capacity = { (u, v): G[u][v]['capacity'] for u, v in G.edges() }
edge_flow = defaultdict(float)

# Dijkstra + 容量限制
def find_shortest_path_with_capacity(G, source, target, demand):
    visited = set()
    dist = {node: float('inf') for node in G.nodes()}
    prev = {node: None for node in G.nodes()}
    dist[source] = 0
    queue = [(0, source)]

    while queue:
        d, u = heapq.heappop(queue)
        if u in visited:
            continue
        visited.add(u)
        for v in G.successors(u):
            cap = residual_capacity.get((u, v), 0)
            if cap >= demand:
                cost = G[u][v]['cost']
                if dist[u] + cost < dist[v]:
                    dist[v] = dist[u] + cost
                    prev[v] = u
                    heapq.heappush(queue, (dist[v], v))

    path = []
    node = target
    while prev[node] is not None:
        path.append((prev[node], node))
        node = prev[node]
    path.reverse()
    return path if node == source else None

# 流量分配流程
sorted_demand_nodes = sorted(demands.items(), key=lambda x: -x[1])
for node, demand in sorted_demand_nodes:
    path = find_shortest_path_with_capacity(G, 'S', node, demand)
    if path:
        for u, v in path:
            residual_capacity[(u, v)] -= demand
            edge_flow[(u, v)] += demand
    else:
        print(f"⚠️ 找不到容量足夠的路徑送達 {node}（需求 {demand}）")

# 視覺化
pos = nx.spring_layout(G, seed=42)
edge_labels = {(u, v): f"{G[u][v]['capacity']}/{G[u][v]['cost']}" for u, v in G.edges()}
edge_colors, edge_widths = [], []

for (u, v) in G.edges():
    flow = edge_flow.get((u, v), 0)
    cap = G[u][v]['capacity']
    usage_ratio = flow / cap if cap > 0 else 0
    color = plt.cm.Reds(usage_ratio)
    width = 1 + 4 * usage_ratio
    edge_colors.append(color)
    edge_widths.append(width)

plt.figure(figsize=(10, 6))
nx.draw(G, pos, with_labels=True, node_size=1000, node_color='lightgreen')
nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
plt.title("啟發式流量分配視覺化（紅色=壅塞，寬度=流量）")
plt.show()
