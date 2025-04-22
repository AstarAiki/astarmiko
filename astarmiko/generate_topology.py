# generate_topology.py
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from astarmiko import base
from astarmiko.base import Activka, setup_config
from collections import defaultdict
import random

def color_by_level(level):
    return {
        'R': 'red',
        'L3': 'orange',
        'L2': 'lightblue'
    }.get(level, 'gray')

def build_topology(config_file="astarmiko.yml", byname_file="activka_byname.yaml", save_as_img="topology.png", save_as_html="topology.html"):
    setup_config(config_file)
    net = Activka(byname_file)
    G = nx.Graph()
    labels = {}
    node_colors_map = {}

    segment_map = defaultdict(list)

    for device in net.devices:
        dev_type = net.dev_type[device]
        level = net.levels.get(device, 'L2')
        segment = net.segment.get(device, 'UNKNOWN')

        G.add_node(device, level=level, segment=segment)
        labels[device] = f"{device}\n({dev_type})"
        node_colors_map[device] = color_by_level(level)
        segment_map[segment].append(device)

        try:
            neighbors = net.getinfo(device, 'neighbor', 'pusto')
            for nb in neighbors:
                neighbor_name = nb[0]
                local_intf = nb[1]
                remote_intf = nb[2]

                if not G.has_edge(device, neighbor_name):
                    G.add_edge(device, neighbor_name, label=f"{local_intf} <-> {remote_intf}")
        except Exception as e:
            print(f"[!] Не удалось получить соседей для {device}: {e}")

    # PNG Visualization
    pos = nx.spring_layout(G, k=0.3, iterations=50)
    node_colors = [node_colors_map[n] for n in G.nodes()]

    plt.figure(figsize=(20, 15))
    nx.draw(G, pos, with_labels=True, labels=labels, node_size=1000, node_color=node_colors, font_size=8)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)
    plt.title("Network Topology")
    plt.savefig(save_as_img, format="PNG")
    plt.close()
    print(f"[+] Топология сохранена как {save_as_img}")

    # HTML Visualization (Plotly)
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')

    node_x, node_y, text, color = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text.append(f"{node}<br>{G.nodes[node]['segment']} - {G.nodes[node]['level']}")
        color.append(color_by_level(G.nodes[node]['level']))

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text', textposition="top center",
        marker=dict(color=color, size=15, line_width=2), text=text, hoverinfo='text')

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='Network Topology (Interactive)',
                titlefont_size=20,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False))
             )

    fig.write_html(save_as_html)
    print(f"[+] Интерактивная топология сохранена как {save_as_html}")

if __name__ == "__main__":
    build_topology()
