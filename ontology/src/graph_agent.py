import os
import google.generativeai as genai
from rdflib import Graph, Namespace, URIRef, Literal
from dotenv import load_dotenv
import pandas as pd

# Load env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Namespaces
BASE_URI = "http://snu.ac.kr/barrier-free/"
NS = Namespace(BASE_URI)

class GraphAgent:
    def __init__(self, key=None):
        self.g = Graph()
        self.load_graph()
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash') 
        except:
            pass

    def load_graph(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_graph.ttl")
        print(f"Loading graph from {path}...")
        self.g.parse(path, format="turtle")
        
        # Keep a copy of the original graph structure for UI logic (e.g. valid facilities)
        self.base_g = Graph()
        self.base_g.parse(path, format="turtle")
        
        print(f"Graph loaded with {len(self.g)} triples.")

    def get_schema_summary(self):
        """Introspects the graph to find used predicates and classes."""
        # Get all predicates
        q = """
        SELECT DISTINCT ?p WHERE {
            ?s ?p ?o .
        }
        """
        preds = [str(row.p).replace(BASE_URI, ":") for row in self.g.query(q) if BASE_URI in str(row.p)]
        
        # Get Sample classes (if 'a' or 'rdf:type' is used)
        q_cls = """
        SELECT DISTINCT ?type WHERE {
            ?s a ?type .
        }
        """
        classes = [str(row.type).replace(BASE_URI, ":") for row in self.g.query(q_cls) if BASE_URI in str(row.type)]

        return f"Predicates: {', '.join(preds)}\nClasses: {', '.join(classes)}"

        
    def get_sample_labels(self):
        """Fetches a few sample labels to help the LLM understand the data content."""
        try:
            q = "SELECT DISTINCT ?label WHERE { ?s rdfs:label ?label } LIMIT 10"
            labels = [str(row.label) for row in self.g.query(q)]
            return ", ".join(labels)
        except:
            return "No labels found."

    def generate_sparql(self, user_query):
        schema_info = self.get_schema_summary()
        sample_labels = self.get_sample_labels()
        
        prompt = f"""
        You are an expert SPARQL generator for an RDF Knowledge Graph about SNU Barrier-Free Course Registration.
        NamespacePrefix: : <{BASE_URI}>
        Prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        Current Graph Schema:
        {schema_info}
        
        Sample Labels in Graph (Context):
        {sample_labels}
        
        Task:
        1. Analyze the user's natural language question.
        2. Explain your reasoning for the query logic.
        3. Generate a valid SPARQL 1.1 query.
        
        ---
        ### DATA DICTIONARY & RULES ###
        
        1. **TIME (수업 시간)**
           - `:StartTime`, `:EndTime`: Predicates holding time as "HH:mm" strings (e.g., "09:00", "14:50").
           - **Comparison:** Use string comparison `FILTER(?start >= "10:00")`.
           - **Logic:** "Ends before 10" -> `?s :EndTime ?end . FILTER(?end < "10:00")`.
           
        2. **ACCESSIBILITY (휠체어/이동약자)**
           - **Reference:** Wheelchair users need `Lift` (F_002) or `Ramp` (F_003).
           - **Hazards:** `Curb` (H_001), `Steep` (H_004) are bad.
           - **Strategy:** When asked "where to take a class" for wheelchair, check the Building's facilities using `:hasFacility`.
           - **Pattern:** `OPTIONAL {{ ?bldg :hasFacility ?fac . ?fac rdfs:label ?facLabel }}` to show what is available.
           
        3. **ROUTES (경로)**
           - **Entity:** `:Route` (Class `C004`).
           - **Direction:** `Building` --[:isEndpointOf]--> `Route`. (e.g., `?bldg :isEndpointOf ?route`)
           - **Strategy:** "How to go from A to B" -> Find a common `:Route` `?r` shared by both `?A` and `?B`.
           - **Pattern:** `?bldgA :isEndpointOf ?r . ?bldgB :isEndpointOf ?r`.
           - **Output:** MUST return the route URI `?r` (or `?route`) to display maps. Also return label and distance.
        
        4. **SEARCH STRATEGY**
           - **Labels:** ALWAYS search against `rdfs:label` using `FILTER(REGEX(?label, 'keyword', 'i'))`.
           - **URIs:** NEVER assume keywords exist in the URI.
        
        ---
        ### COMPETENCY QUESTIONS ###
        
        Q1. "10시 전에 끝나는 '수학1' 수업 있어?"
        -> {{
            "reasoning": "Find '수학1' courses. Check their :EndTime. Filter where EndTime < '10:00'.",
            "sparql": "SELECT ?courseName ?classRoom ?endTime WHERE {{ ?course :title '수학1' ; rdfs:label ?courseName ; :EndTime ?endTime ; :isHeldAt ?room . ?room rdfs:label ?classRoom . FILTER(?endTime < '10:00') }}"
           }}
           
        Q2. "휠체어 타는데 '수학1' 어디서 들어야 해?"
        -> {{
            "reasoning": "Find '수학1' rooms and their buildings. Then OPTIONALLY retrieve facility labels to see if they have 'Lift' or 'Ramp'.",
            "sparql": "SELECT ?bldgName ?facLabel WHERE {{ ?course :title '수학1' ; :isHeldAt ?room . ?room :locatedIn ?bldg . ?bldg rdfs:label ?bldgName . OPTIONAL {{ ?bldg :hasFacility ?fac . ?fac rdfs:label ?facLabel }} }}"
           }}
           
        Q3. "25동에서 500동 어떻게 가?"
        -> {{
            "reasoning": "Find a Route entity ?route where both 25동 and 500동 are endpoints. RETURN ?route URI for map display.",
            "sparql": "SELECT ?route ?routeLabel ?dist WHERE {{ ?bldgA rdfs:label '25동' . ?bldgB rdfs:label '500동' . ?bldgA :isEndpointOf ?route . ?bldgB :isEndpointOf ?route . ?route rdfs:label ?routeLabel ; :distance ?dist . }}"
           }}
           
        User Question: "{user_query}"
        JSON:
        """
        
        response = self.model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        try:
            import json
            return json.loads(text)
        except:
            # Fallback if not valid JSON
            return {"reasoning": "Error parsing JSON", "sparql": text}

    def execute_query(self, sparql):
        print(f"Executing: {sparql}")
        try:
            results = self.g.query(sparql)
            res_list = []
            if results.vars:
                columns = [str(v) for v in results.vars]
                for row in results:
                    res_list.append([str(val) for val in row])
                return pd.DataFrame(res_list, columns=columns)
            else:
                # Boolean ASK output
                return pd.DataFrame([bool(results)], columns=["Result"])
        except Exception as e:
            return pd.DataFrame([f"Error: {e}"], columns=["Error"])

    def generate_answer(self, user_query, sparql, df, reasoning):
        data_str = df.to_string() if df is not None and not df.empty else "No results found."
        
        prompt = f"""
        You are a helpful assistant for SNU students.
        User Question: "{user_query}"
        
        You performed a search with this logic:
        {reasoning}
        
        And found this data:
        {data_str}
        
        Task: Provide a natural language answer to the user in Korean.
        If data is found, summarize it. If not, politely explain.
        
        STYLE GUIDELINES:
        - Route/Path Queries: If the result contains a Route (e.g. R_xxx), DO NOT repeat the route's name (e.g. '25동과 500동 사이 경로').
          Instead, simply say "다음과 같은 경로가 있습니다 (거리: X m)." because the system will show a map image automatically.
        - General: Be helpful and concise.
        """
        response = self.model.generate_content(prompt)
        return response.text

    def process_query(self, user_query):
        # 1. Generate SPARQL
        step1 = self.generate_sparql(user_query)
        sparql = step1.get("sparql", "")
        reasoning = step1.get("reasoning", "")
        
        # 2. Execute
        df = self.execute_query(sparql)
        
        # 3. Generate Answer
        final_answer = self.generate_answer(user_query, sparql, df, reasoning)
        
        return {
            "question": user_query,
            "reasoning": reasoning,
            "sparql": sparql,
            "data": df,
            "answer": final_answer
        }


if __name__ == "__main__":
    agent = GraphAgent()
    print(agent.get_schema_summary())
    # Test
    q = "500동에 엘리베이터 있어?"
    # sparql = agent.generate_sparql(q)
    # print(sparql)
    # df = agent.execute_query(sparql)
    # print(df)
