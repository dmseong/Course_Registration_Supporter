import pandas as pd
from rdflib import Graph, Literal, RDF, RDFS, URIRef, Namespace, XSD
import os
import urllib.parse

# Define Namespace
BASE_URI = "http://snu.ac.kr/barrier-free/"
NS = Namespace(BASE_URI)

def sanitize_id(id_str):
    """Encodes string to be safe for URI"""
    if pd.isna(id_str):
        return "Unknown"
    # Ensure it's a string
    id_str = str(id_str).strip()
    return urllib.parse.quote(id_str)

def build_knowledge_graph():
    print("Initializing Graph...")
    g = Graph()
    g.bind("", NS)  # Default prefix

    # File Paths
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "csv")
    nodes_file = os.path.join(data_dir, "안성재팀 - 온톨로지 - Nodes.csv")
    edges_file = os.path.join(data_dir, "안성재팀 - 온톨로지 - Edges.csv")
    courses_file = os.path.join(data_dir, "안성재팀 - 온톨로지 - 교과목.csv")

    # 1. Process Nodes
    print(f"Loading Nodes from {nodes_file}...")
    try:
        nodes_df = pd.read_csv(nodes_file)
        for _, row in nodes_df.iterrows():
            node_id = sanitize_id(row['id'])
            node_uri = NS[node_id]
            
            # Label
            if 'label' in row and not pd.isna(row['label']):
                g.add((node_uri, RDFS.label, Literal(row['label'])))
            
            # Sort (Class vs Instance)
            sort_val = row.get('sort', '').strip()
            if sort_val == 'Class':
                g.add((node_uri, RDF.type, RDFS.Class))
            elif sort_val == 'Instance':
                # If there's a specific class it belongs to, it might be defined in Edges,
                # but for now we basically treat them as instances.
                # If 'subSort' or similar existed, we'd use it.
                # The milestone says: "Instance" -> a :ClassName (referencing label or implied class)
                # However, usually the Class of an Instance is defined via a relation or implied.
                # Let's see if Edges define "isA" or "type".
                # For now, let's assume it's a NamedIndividual or just a generic Resource if class isn't known yet.
                pass 
            
    except Exception as e:
        print(f"Error processing Nodes: {e}")

    # 2. Process Edges (Relationships)
    print(f"Loading Edges from {edges_file}...")
    try:
        edges_df = pd.read_csv(edges_file)
        for _, row in edges_df.iterrows():
            src_id = sanitize_id(row['sourceID'])
            target_raw = str(row['targetID']).strip()
            relation = sanitize_id(row['relation'])
            
            src_uri = NS[src_id]
            rel_uri = NS[relation]
            
            # Skip time relations in Edges.csv as they are better handled in Courses.csv processing
            # This prevents creating URIs like :1000 where Literals "10:00" are expected
            if relation in ['StartTime', 'EndTime']:
                continue
            
            # Check if target is a Literal (e.g., """value"""^^type)
            if target_raw.startswith('"""'):
                # Extract value between triple quotes
                # Expected format: """Note"""^^xsd:string or just """Note"""
                # Simple parsing: find the closing """
                try:
                    content_end = target_raw.rindex('"""')
                    if content_end > 3:
                        content = target_raw[3:content_end]
                        # We could parse type here if needed, but for now just taking the string content is safer/simpler for display
                        # If we really want typed literals, use rdflib.XSD...
                        g.add((src_uri, rel_uri, Literal(content)))
                    else:
                        # Fallback
                        g.add((src_uri, rel_uri, Literal(target_raw)))
                except ValueError:
                     g.add((src_uri, rel_uri, Literal(target_raw)))
            else:
                # It's a resource link
                tgt_id = sanitize_id(target_raw)
                tgt_uri = NS[tgt_id]
                g.add((src_uri, rel_uri, tgt_uri))
                
                # If relation suggests Class type
                if relation.lower() in ['type', 'rdf:type', 'a', 'instanceof']:
                     # Ensure target is labeled as a Class (optional but good for consistency)
                     # But we don't want to force-add type to everything if not needed
                     pass

    except Exception as e:
        print(f"Error processing Edges: {e}")

    # 3. Process Courses (Properties)
    print(f"Loading Courses from {courses_file}...")
    try:
        courses_df = pd.read_csv(courses_file)
        for _, row in courses_df.iterrows():
            # ID matches Node id
            course_id = sanitize_id(row['ID'])
            course_uri = NS[course_id]
            
            # Map columns to constraints/properties
            # Example columns: title, startsAt, endsAt, dayOfWeek, etc.
            # We'll just add all columns as data properties
            # Specific Column Mapping & Formatting
            # Map Korean column names to clean predicates
            COL_MAP = {
                "수업 시작 시간": "StartTime",
                "수업 종료 시간": "EndTime",
                "과목명": "title",
                "강의동": "isHeldAt_BuildingLabel", # Temporary, usually mapped to node
                "강의실": "isHeldAt_RoomLabel"
            }
            
            for col in courses_df.columns:
                if col == 'ID': continue
                
                val = row[col]
                if pd.notna(val):
                    # 1. Determine Predicate URI
                    clean_col = COL_MAP.get(col, col) # Fallback to original if not mapped
                    prop_uri = NS[sanitize_id(clean_col)]
                    
                    # 2. Format Value (Time Padding)
                    # Check if it looks like time "9:50" or "9:00"
                    val_str = str(val).strip()
                    if clean_col in ["StartTime", "EndTime"]:
                        # Pad with zero if needed (9:50 -> 09:50)
                        if ':' in val_str and len(val_str.split(':')[0]) == 1:
                            val_str = "0" + val_str
                    
                    # Add Triple
                    g.add((course_uri, prop_uri, Literal(val_str)))
                    
    except Exception as e:
        print(f"Error processing Courses: {e}")

    # Serialize
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_graph.ttl")
    print(f"Saving graph to {output_path}...")
    g.serialize(destination=output_path, format="turtle")
    print("Done!")

if __name__ == "__main__":
    build_knowledge_graph()
