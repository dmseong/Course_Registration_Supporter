import streamlit as st
import pandas as pd
from rdflib import URIRef, Literal, Namespace
from graph_agent import GraphAgent
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import re

# Page Config
st.set_page_config(
    page_title="SNU Barrier-Free Course Helper",
    page_icon="♿",
    layout="wide"
)

# Initialize Agent (Cached Resource)
@st.cache_resource
def get_agent():
    # v1.1 Force cache reload for base_g
    return GraphAgent()

try:
    agent = get_agent()
    # Ensure base_g exists (hotfix for cached instances)
    if not hasattr(agent, 'base_g'):
         agent.load_graph()
except Exception as e:
    st.error(f"Failed to initialize Agent: {e}")
    st.stop()

# Namespace for RDF operations (Must match graph_agent.py)
NS = Namespace("http://snu.ac.kr/barrier-free/")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reports" not in st.session_state:
    st.session_state.reports = [] 

# --- Navigation ---
st.sidebar.title("메뉴")
page = st.sidebar.radio("이동", ["🔍 수강신청 도우미 (Chat)", "🛠️ 시설 관리 (Maintenance)", "📊 지식 그래프 시각화 (Visualization)"])

# --- Page 1: Chat ---
if page == "🔍 수강신청 도우미 (Chat)":
    st.title("♿ SNU Barrier-Free 수강신청 도우미")
    st.markdown("지체 장애 학우를 위한 배리어프리 정보를 제공합니다.")

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "data" in msg and msg["data"] is not None:
                with st.expander("🔍 근거 데이터 & SPARQL 확인"):
                     st.markdown(f"**Reasoning:**\n{msg.get('reasoning', '')}")
                     st.code(msg.get('sparql', ''), language='sparql')
                     st.dataframe(msg["data"])
            
            # Show images if present in history history handling logic needs improvement but for now ok
            # Actually, standard Streamlit chat doesn't persist st.image in history automatically well unless we rerun
            # But let's keep it simple. The below logic re-renders context. 
            pass

    # Chat Input
    if prompt := st.chat_input("질문을 입력하세요 (예: 500동에 엘리베이터 있어?)"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("지식 그래프 검색 중..."):
                try:
                    result = agent.process_query(prompt)
                    response_text = result["answer"]
                    
                    st.markdown(response_text)
                    
                    # Show details
                    with st.expander("🔍 근거 데이터 & SPARQL 확인"):
                        st.markdown(f"**Reasoning:**\n{result['reasoning']}")
                        st.code(result['sparql'], language='sparql')
                        st.dataframe(result['data'])
                    
                    # Dynamic Image Display
                    found_routes = []
                    if result.get("data") is not None and not result["data"].empty:
                        for col in result["data"].columns:
                            for val in result["data"][col]:
                                val_str = str(val)
                                match = re.search(r'(R_\d+)', val_str)
                                if match:
                                    found_routes.append(match.group(1))
                    
                    found_routes = list(set(found_routes))
                    if found_routes:
                        img_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "images")
                        for route_id in found_routes:
                            for ext in [".png", ".jpg", ".jpeg"]:
                                img_path = os.path.join(img_dir, route_id + ext)
                                if os.path.exists(img_path):
                                    st.image(img_path, caption=f"🗺️ 경로 지도: {route_id}")
                                    break
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response_text,
                        "data": result["data"],
                        "sparql": result["sparql"],
                        "reasoning": result["reasoning"]
                    })
                except Exception as e:
                    st.error(f"Error processing query: {e}")

# --- Page 2: Maintenance ---
elif page == "🛠️ 시설 관리 (Maintenance)":
    st.title("🛠️ 시설 관리 및 고장 신고")
    st.markdown("관리자가 **실시간으로 시설 상태를 온톨로지에 반영**합니다.")

    # 1. User Report Section
    st.header("📢 고장 신고 게시판")
    with st.form("report_form"):
        report_text = st.text_input("신고 내용", placeholder="예: 25동 엘리베이터가 고장났어요.")
        submitted = st.form_submit_button("신고하기")
        if submitted and report_text:
            st.session_state.reports.append(report_text)
            st.success("신고가 접수되었습니다.")
    
    if st.session_state.reports:
        st.write("### 최근 신고 목록")
        for idx, report in enumerate(reversed(st.session_state.reports[-5:])):
            st.info(f"{idx+1}. {report}")

    st.divider()

    # 2. Admin Dashboard (Graph Mutation)
    st.header("⚙️ 관리자 대시보드 (Facility Control)")
    
    # Get all buildings with Labels
    q_bldgs = f"""
    PREFIX : <{NS}>
    SELECT DISTINCT ?b ?label
    WHERE {{ 
        ?b :instanceOf :C001 . 
        OPTIONAL {{ ?b rdfs:label ?label }}
    }}
    ORDER BY ?label
    """
    res_bldgs = agent.g.query(q_bldgs)
    
    # Create mapping: "Name (ID)" -> URI
    bldg_map = {}
    for r in res_bldgs:
        uri = str(r.b)
        parts = uri.split('/')
        id_part = parts[-1]
        name = str(r.label) if r.label else id_part
        
        display_name = f"{name} ({id_part})"
        bldg_map[display_name] = uri
    
    sorted_names = sorted(bldg_map.keys())
    selected_name = st.selectbox("건물 선택", sorted_names)
    
    if selected_name:
        selected_bldg_uri = URIRef(bldg_map[selected_name])
        # Extract simple name for header
        simple_name = selected_name.split('(')[0].strip()
        
        st.subheader(f"{simple_name} 시설 상태 관리")
        
        # Standard Facilities to manage
        # Mapped to our real Facility instances
        # Need to know which URIs correspond to 'Lift', 'Ramp'.
        # In our graph, F_002 is Lift, F_003 is Ramp, etc.
        # Let's verify with labels if we can, or hardcode based on data inspection.
        # From knowledge_graph.ttl:
        # :F_001 label "장애인화장실"
        # :F_002 label "승강기" (Lift)
        # :F_003 label "경사로" (Ramp)
        # :F_004 label "자동문"
        
        standard_facilities = {
            "승강기 (Lift)": "F_002",
            "경사로 (Ramp)": "F_003",
            "장애인화장실 (WC)": "F_001",
            "자동문 (AutoDoor)": "F_004"
        }
        
        # Helper to toggle
        def toggle_facility(bldg_uri, fac_id, is_active):
            fac_uri = URIRef(NS + fac_id)
            if is_active:
                # Add triple: bldg :hasFacility fac
                agent.g.add((bldg_uri, NS.hasFacility, fac_uri))
            else:
                # Remove triple
                agent.g.remove((bldg_uri, NS.hasFacility, fac_uri))
        
        for label, fac_id in standard_facilities.items():
            fac_uri = URIRef(NS + fac_id)
            
            # Check if currently active
            # (bldg, :hasFacility, fac)
            is_currently_active = (selected_bldg_uri, NS.hasFacility, fac_uri) in agent.g
            
            # Check if originally present (in base graph)
            is_originally_present = (selected_bldg_uri, NS.hasFacility, fac_uri) in agent.base_g
            
            # Toggle Button
            # Only enable if it was originally present in the graph structure
            new_state = st.toggle(
                label, 
                value=is_currently_active, 
                key=f"{selected_name}_{fac_id}",
                disabled=not is_originally_present
            )
            
            if new_state != is_currently_active:
                toggle_facility(selected_bldg_uri, fac_id, new_state)
                st.rerun() 

        st.caption("※ 시설을 끄면(OFF) 지식 그래프에서 연결이 끊어지며, AI가 해당 시설이 없다고 판단합니다.")

# --- Page 3: Visualization ---
elif page == "📊 지식 그래프 시각화 (Visualization)":
    st.title("📊 온톨로지 지식 그래프 시각화")
    st.markdown("현재 메모리에 로드된 **지식 그래프(Ontology)**의 상태를 실시간으로 시각화합니다.")
    
    # Initialize Network
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black", notebook=False)
    # net.force_atlas_2based()
    
    # --- Build Graph from RDF ---
    # 1. Buildings (Red)
    # Query: ?b :instanceOf :C001
    # Helper to get Detailed Title (Hover)
    def get_hover_info(g, uri):
        try:
            # Query all properties
            q_props = f"""
            SELECT ?p ?o WHERE {{ <{uri}> ?p ?o }}
            """
            rows = g.query(q_props)
            info = []
            
            def clean_uri(s):
                if not isinstance(s, str): return str(s)
                if "#" in s: return s.split("#")[-1]
                if "/" in s: return s.split("/")[-1]
                return s

            for r in rows:
                p_str = str(r.p)
                o_str = str(r.o)
                
                p_base = clean_uri(p_str)
                
                # 1. Hide instanceOf / type
                if "instanceof" in p_base.lower() or "type" in p_base.lower():
                    continue

                # 2. Special handling for Lat/Long (which seem to be URIs with encoded values)
                if "Lat" in p_base or "Long" in p_base:
                     label = "위도" if "Lat" in p_base else "경도"
                     
                     if "http" in o_str:
                         parts = o_str.split("/")[-1] 
                         # Remove URI encoding chars roughly
                         val = parts.replace("%22", "").replace("%5E", "")
                         # Remove xsd suffix
                         val = val.split("xsd")[0]
                         info.append(f"{label}: {val}")
                         continue
                     else:
                         info.append(f"{label}: {o_str}")
                         continue

                # 3. Filter other Relations
                if o_str.startswith("http"):
                    continue # Skip other relations
                
                # Literal values
                o_display = o_str
                
                # Wrap long text
                if len(o_display) > 50:
                    o_display = o_display[:50] + "..."
                
                info.append(f"{p_base}: {o_display}")
            
            return "\n".join(info)
        except Exception as e:
            return str(uri)

    # --- Build Graph from RDF ---
    # 1. Buildings (Red)
    # Query: ?b :instanceOf :C001
    q_bldgs = f"""
    PREFIX : <{NS}>
    SELECT ?b ?label WHERE {{ 
        ?b :instanceOf :C001 . 
        OPTIONAL {{ ?b rdfs:label ?label }}
    }}
    """
    for row in agent.g.query(q_bldgs):
        b_uri = str(row.b)
        # Use Label if available, else ID
        if row.label:
            b_name = str(row.label)
        else:
            b_name = b_uri.split('/')[-1]
        
        hover_text = get_hover_info(agent.g, b_uri)
        net.add_node(b_uri, label=b_name, title=hover_text, color="#FF6B6B", shape="dot", size=25) 

    # 2. Rooms (Blue)
    q_rooms = f"""
    PREFIX : <{NS}>
    SELECT ?r ?b ?label WHERE {{ 
        ?r :instanceOf :C003 .
        ?r :isLocatedIn ?b .
        OPTIONAL {{ ?r rdfs:label ?label }}
    }}
    """
    for row in agent.g.query(q_rooms):
        r_uri = str(row.r)
        b_uri = str(row.b)
        
        if row.label:
            r_name = str(row.label)
        else:
            r_name = r_uri.split('/')[-1]
            
        hover_text = get_hover_info(agent.g, r_uri)
        
        # Add Room node
        net.add_node(r_uri, label=r_name, title=hover_text, color="#4ECDC4", shape="dot", size=15)
        # Add Edge
        net.add_edge(r_uri, b_uri, title="isLocatedIn")

    # 3. Facilities (Yellow)
    q_facs = f"""
    PREFIX : <{NS}>
    SELECT ?b ?f ?label
    WHERE {{
        ?b :hasFacility ?f .
        ?f rdfs:label ?label .
    }}
    """
    for row in agent.g.query(q_facs):
        b_uri = str(row.b)
        f_uri = str(row.f)
        f_name = str(row.label) if row.label else f_uri.split('/')[-1]
        
        hover_text = get_hover_info(agent.g, f_uri)
        
        net.add_node(f_uri, label=f_name, title=hover_text, color="#FFE66D", shape="diamond", size=20) 
        net.add_edge(b_uri, f_uri, title="hasFacility", color="#FFE66D")

    # 4. Routes (Gray)
    q_routes = f"""
    PREFIX : <{NS}>
    SELECT ?b ?r ?label
    WHERE {{
        ?b :isEndpointOf ?r .
        ?r :instanceOf :C004 .
        OPTIONAL {{ ?r rdfs:label ?label }}
    }}
    """
    for row in agent.g.query(q_routes):
        b_uri = str(row.b)
        r_uri = str(row.r)
        r_name = str(row.label) if row.label else r_uri.split('/')[-1]
        
        hover_text = get_hover_info(agent.g, r_uri)
        
        net.add_node(r_uri, label=r_name, title=hover_text, color="#95A5A6", shape="triangle", size=15)
        net.add_edge(b_uri, r_uri, title="isEndpointOf")

    # --- Render ---
    try:
        # Save to temporary file
        # pyvis generates html
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.save_graph(tmp.name)
            tmp.seek(0)
            html_content = tmp.read().decode("utf-8")
        
        st.caption("🔴 건물 | 🔵 강의실 | 🟡 편의시설 | ⚪ 경로")
        components.html(html_content, height=620)
        st.info("💡 마우스 휠로 확대/축소하거나 노드를 드래그하여 구조를 살펴볼 수 있습니다.")
        
    except Exception as e:
        st.error(f"Visualization Error: {e}")
