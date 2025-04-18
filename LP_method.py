import cvxpy as cp
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

# 建立圖與邊屬性
G = nx.DiGraph()
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

# 受災戶需求
demands = {'H1': 8, 'H2': 7}
commodities = list(demands.keys())
edges = list(G.edges())
nodes = list(G.nodes())

# LP 變數：每個災戶對每條邊的流量
flow_vars = {
    (k, u, v): cp.Variable(nonneg=True, name=f"f_{k}_{u}_{v}")
    for k in commodities for (u, v) in edges
}

# 限制條件
constraints = []

# 邊容量限制：總流量 ≤ 邊容量
for (u, v) in edges:
    total_flow = cp.sum([flow_vars[k, u, v] for k in commodities])
    constraints.append(total_flow <= G[u][v]['capacity'])

# 每個節點滿足流量守恆
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

# 目標：總成本最小
objective = cp.Minimize(cp.sum([
    G[u][v]['cost'] * flow_vars[k, u, v]
    for (k, u, v) in flow_vars
]))

# 解問題
prob = cp.Problem(objective, constraints)
prob.solve()

# 彙整結果
edge_flow_total = defaultdict(float)
for (k, u, v), var in flow_vars.items():
    edge_flow_total[(u, v)] += var.value

# 🎨 視覺化結果
pos = nx.spring_layout(G, seed=42)
edge_labels = {(u, v): f"{G[u][v]['capacity']}/{G[u][v]['cost']}" for u, v in G.edges()}
edge_colors, edge_widths = [], []

for (u, v) in G.edges():
    flow = edge_flow_total.get((u, v), 0)
    cap = G[u][v]['capacity']
    usage_ratio = flow / cap if cap > 0 else 0
    color = plt.cm.Blues(usage_ratio)
    width = 1 + 4 * usage_ratio
    edge_colors.append(color)
    edge_widths.append(width)

plt.figure(figsize=(10, 6))
nx.draw(G, pos, with_labels=True, node_size=1000, node_color='lightblue')
nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
plt.title("LP 最佳化後的流量分配（藍色=壅塞，寬度=流量）")
plt.show()
