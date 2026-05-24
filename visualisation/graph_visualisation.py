import json
import networkx as nx
from pyvis.network import Network

# 1. Load your actual data
with open("legal_graph.json", "r", encoding="utf-8") as f:
    graph_data = json.load(f)

net = Network(height="900px", width="100%", bgcolor="#1a1a1a", font_color="white", directed=True)

# 2. Add Nodes with Strict Act-Based Color Palettes
for node in graph_data.get("nodes", []):
    node_id = node.get("id")
    title = node.get("title", node_id)
    node_type = node.get("type", "")
    act = node.get("act", "")
    
    # Define colors based on the Act
    if act == "BNS":
        color = "#0047ab" if node_type == "Chapter" else "#4b8bff" # Dark/Light Blue
    elif act == "BNSS":
        color = "#006400" if node_type == "Chapter" else "#00cc96" # Dark/Light Green
    elif act == "BSA":
        color = "#cc5500" if node_type == "Chapter" else "#ffa500" # Dark/Light Orange
    else:
        color = "#555555" # Fallback Gray
        
    size = 35 if node_type == "Chapter" else 15
    shape = "hexagon" if node_type == "Chapter" else "dot"
        
    net.add_node(node_id, label=title, title=title, color=color, size=size, shape=shape)

# 3. Add Edges with Clustering Physics (The Secret Sauce)
for edge in graph_data.get("links", []):
    source = edge.get("source")
    target = edge.get("target")
    label = edge.get("label", "")
    
    # Figure out which act the source and target belong to
    # (e.g., extracting "BNS" from "BNS_S1")
    source_act = source.split("_")[0]
    target_act = target.split("_")[0]
    
    if label == "PART_OF_CHAPTER":
        edge_color = "rgba(255, 255, 255, 0.2)"
        spring_length = 50  # Very tight: Keeps leaves close to their chapter hub
    else:
        # It's a "REFERENCES" cross-link
        if source_act == target_act:
            # Internal Reference (e.g., BNS section references another BNS section)
            edge_color = "rgba(255, 255, 255, 0.1)" # Subtle line
            spring_length = 150 # Keep it tight inside the same cluster
        else:
            # External Reference (e.g., BNS references BNSS)
            # This is a bridge between two different clusters
            edge_color = "rgba(255, 75, 75, 0.4)" # Red line bridging the islands
            spring_length = 800 # VERY LONG: Pushes the 3 clusters far away from each other!
            
    net.add_edge(source, target, title=label, color=edge_color, length=spring_length)

# 4. Physics configuration to allow the clusters to drift apart
net.set_options("""
var options = {
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -50,
      "centralGravity": 0.005,
      "springConstant": 0.08,
      "avoidOverlap": 0.5
    },
    "maxVelocity": 50,
    "solver": "forceAtlas2Based",
    "timestep": 0.35,
    "stabilization": {"iterations": 200}
  }
}
""")

# 5. Save and render
output_file = "clustered_presentation_graph.html"
net.write_html(output_file)
print(f"✅ Clustered Graph generated! Open '{output_file}' in your web browser.")