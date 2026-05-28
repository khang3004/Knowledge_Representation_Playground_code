
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_agent.router import route_query

# Configure logging to see the output
logging.basicConfig(level=logging.INFO)

def test_semantic_parsing():
    test_cases = [
        {
            "query": "Tôi có natri và nước, làm sao tạo ra NaOH?",
            "domain": "chemistry",
            "expected_facts": ["Na", "H2O"],
            "expected_goal": "NaOH"
        },
        {
            "query": "Chứng minh AB bằng EF biết AB bằng CD và CD bằng EF",
            "domain": "geometry",
            "expected_facts": ["Congruent(AB,CD)", "Congruent(CD,EF)"],
            "expected_goal": "Congruent(AB,EF)"
        },
        {
            "query": "Giải phương trình x+2=5",
            "domain": "algebra",
            "expected_facts": ["x+2=5"],
            "expected_goal": "x=3"
        }
    ]

    print("\n--- Testing LLM Semantic Parsing (Vietnamese) ---")
    for case in test_cases:
        print(f"\nQuery: {case['query']}")
        print(f"Domain: {case['domain']}")
        try:
            facts, goal = route_query(case['query'], case['domain'])
            print(f"Parsed Facts: {[f.value for f in facts]}")
            print(f"Parsed Goal: {goal.value}")
        except Exception as e:
            print(f"Error parsing query: {e}")

if __name__ == "__main__":
    test_semantic_parsing()
