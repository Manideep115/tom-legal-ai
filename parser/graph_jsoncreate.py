import json
import re
import os
import networkx as nx
from networkx.readwrite import json_graph

def build_legal_graph():
    master_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\master_legal_v1.json"
    output_graph = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\legal_graph.json"

    with open(master_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    G = nx.MultiDiGraph() # Multi-Directed Graph to handle multiple types of links

    print("🕸️  Building Knowledge Graph...")

    # Pattern to find section numbers in text
    ref_pattern = re.compile(r'section\s+(\d+)', re.IGNORECASE)

    for sec in data:
        u_id = sec['uid']
        
        # 1. Add Section Node with metadata
        G.add_node(u_id, 
                   title=sec['title'], 
                   act=sec['act'], 
                   chapter=sec['chapter'])

        # 2. Add Chapter Node and link Section to it
        chapter_id = f"{sec['act']}_{sec['chapter'].replace(' ', '_')}"
        G.add_node(chapter_id, type="Chapter", act=sec['act'])
        G.add_edge(u_id, chapter_id, label="PART_OF_CHAPTER")

        # 3. Detect Explicit References in content
        content = sec['content']
        mentions = ref_pattern.findall(content)
        
        for ref_num in set(mentions):
            # Try to guess which Act it refers to
            # Default to the same act, unless another act is mentioned nearby
            target_act = sec['act']
            if "Bharatiya Nyaya Sanhita" in content: target_act = "BNS"
            elif "Bharatiya Nagarik Suraksha" in content: target_act = "BNSS"
            elif "Bharatiya Sakshya" in content: target_act = "BSA"
            
            target_id = f"{target_act}_S{ref_num}"
            # We add the edge even if the target node isn't created yet
            G.add_edge(u_id, target_id, label="REFERENCES")

    # Save Graph as JSON
    graph_data = json_graph.node_link_data(G)
    with open(output_graph, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=4)

    print(f"✅ Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} relationships!")

if __name__ == "__main__":
    build_legal_graph()