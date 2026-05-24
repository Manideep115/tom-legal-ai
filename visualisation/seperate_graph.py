import json
import random
from pyvis.network import Network

# 1. Load your actual data
with open("legal_graph.json", "r", encoding="utf-8") as f:
    graph_data = json.load(f)

# 2. Initialize Network
# We turn physics OFF at the start so our exact X/Y coordinates lock into place
net = Network(height="900px", width="100%", bgcolor="#1a1a1a", font_color="white", directed=True)
net.toggle_physics(False) 

# 3. Define the Triangular Focal Points (X, Y)
centers = {
    "BNS": (-700, -500),  # Top-Left Quadrant
    "BNSS": (700, -500),  # Top-Right Quadrant
    "BSA": (0, 600)       # Bottom-Center
}

# 4. Add Nodes with Fixed Coordinates
for node in graph_data.get("nodes", []):
    node_id = node.get("id")
    title = node.get("title", node_id)
    node_type = node.get("type", "")
    act = node.get("act", "")
    
    # Identify which cluster this node belongs to
    base_x, base_y = centers.get(act, (0, 0))
    
    # Add a random scatter (radius of ~300) so they form a "cloud" around the center
    # Chapters stay closer to the exact center, Sections scatter wider
    scatter_radius = 100 if node_type == "Chapter" else 350
    x = base_x + random.randint(-scatter_radius, scatter_radius)
    y = base_y + random.randint(-scatter_radius, scatter_radius)

    # Color Palette matching the Acts
    if act == "BNS": color = "#0047ab" if node_type == "Chapter" else "#4b8bff"
    elif act == "BNSS": color = "#006400" if node_type == "Chapter" else "#00cc96"
    elif act == "BSA": color = "#cc5500" if node_type == "Chapter" else "#ffa500"
    else: color = "#555555"

    size = 35 if node_type == "Chapter" else 15
    shape = "hexagon" if node_type == "Chapter" else "dot"

    # Crucial: We explicitly pass the x and y coordinates here
    net.add_node(node_id, label=title, title=title, color=color, size=size, shape=shape, x=x, y=y)

# 5. Add the Edges (The Bridges)
for edge in graph_data.get("links", []):
    source = edge.get("source")
    target = edge.get("target")
    label = edge.get("label", "")
    
    source_act = source.split("_")[0]
    target_act = target.split("_")[0]
    
    if label == "PART_OF_CHAPTER":
        edge_color = "rgba(255, 255, 255, 0.15)" # Subtle gray for internal hierarchy
    else:
        if source_act == target_act:
            edge_color = "rgba(255, 255, 255, 0.1)" # Subtle gray for internal references
        else:
            # THE BRIDGES: Strong red lines spanning across the empty space between clusters
            edge_color = "rgba(255, 75, 75, 0.7)" 

    net.add_edge(source, target, title=label, color=edge_color)

# 6. Save to HTML
output_file = "triangular_sketch_graph.html"
net.write_html(output_file)
print(f"✅ Triangular Sketch Graph generated! Open '{output_file}' in your web browser.")