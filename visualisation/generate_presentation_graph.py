import json
import networkx as nx
from pyvis.network import Network

# 1. Load your actual data
with open("legal_graph.json", "r", encoding="utf-8") as f:
    graph_data = json.load(f)

# 2. Create a massive canvas for presentation
# We use a dark background because it looks much better in PowerPoint
net = Network(height="900px", width="100%", bgcolor="#222222", font_color="white", directed=True)

# 3. Add Nodes with Presentation Styling
# We will make Chapters big and red, and Sections smaller and blue
for node in graph_data.get("nodes", []):
    node_id = node.get("id")
    title = node.get("title", node_id)
    
    # Styling based on node type
    if node.get("type") == "Chapter":
        color = "#ff4b4b" # Bright Red for Chapters
        size = 30
        shape = "hexagon"
    else:
        # Differentiate Acts by color
        act = node.get("act", "")
        if act == "BNS": color = "#4b8bff" # Blue
        elif act == "BNSS": color = "#00cc96" # Green
        elif act == "BSA": color = "#ffa500" # Orange
        else: color = "#aaaaaa" # Gray
        
        size = 15
        shape = "dot"
        
    net.add_node(node_id, label=title, title=title, color=color, size=size, shape=shape)

# 4. Add Edges with clear labels
for edge in graph_data.get("links", []):
    source = edge.get("source")
    target = edge.get("target")
    label = edge.get("label", "")
    
    # Style the lines based on relationship type
    if label == "PART_OF_CHAPTER":
        edge_color = "rgba(255, 255, 255, 0.2)" # Faint white for hierarchy
    else:
        edge_color = "rgba(255, 75, 75, 0.6)" # Stronger red for cross-references
        
    net.add_edge(source, target, title=label, color=edge_color)

# 5. Physics configuration (Crucial for large graphs)
# This settings profile handles 1000+ nodes without exploding your computer
net.set_options("""
var options = {
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -100,
      "centralGravity": 0.01,
      "springLength": 200,
      "springConstant": 0.05
    },
    "maxVelocity": 50,
    "solver": "forceAtlas2Based",
    "timestep": 0.35,
    "stabilization": {"iterations": 150}
  }
}
""")

# 6. Save to HTML
output_file = "presentation_graph.html"
net.write_html(output_file)
print(f"✅ Graph successfully generated! Open '{output_file}' in your web browser.")