from src.graph_agent import GraphAgent

def test_manual():
    print("Initializing Agent...")
    agent = GraphAgent()
    
    q = "500동에 엘리베이터 있어?"
    print(f"Testing Query: {q}")
    
    result = agent.process_query(q)
    
    print("\n--- Result ---")
    print(f"Reasoning: {result['reasoning']}")
    print(f"SPARQL: {result['sparql']}")
    print(f"Data:\n{result['data']}")
    print(f"Answer: {result['answer']}")

if __name__ == "__main__":
    test_manual()
