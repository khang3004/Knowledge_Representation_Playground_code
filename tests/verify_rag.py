"""
Integration Test Suite for the Omni-IPS GraphRAG Pipeline and Explainability Agent.

Validates:
1. NLP query parsing (LLM / offline fallback).
2. ChromaDB semantic vector search and Neo4j Fact mapping.
3. Core Inference Engine execution on mapped nodes.
4. Explanation Agent templating/LLM proof explanation.
"""

import sys
import os
import traceback
import logging
import asyncio

# Append project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_agent.router import route_query, fallback_query_parser
from rag_agent.embed_knowledge import get_neo4j_facts_and_rules, ingest_to_qdrant
from core_engine import ForwardChainingEngine
from core_engine.models import Fact
from api.main import explain_proof, ExplainRequest, ExecutionStepResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_rag")


def test_offline_query_parsing():
    print("\n--- Test 1: Offline NLP Parser (Regex & Keywords) ---")
    
    # Chemistry query test
    chem_query = "I have sodium and water, how do I synthesize sodium hydroxide?"
    facts, goal = fallback_query_parser(chem_query, "chemistry")
    
    print(f"Chemistry Query: '{chem_query}'")
    print(f"Extracted Facts: {facts}")
    print(f"Extracted Goal:  {goal}")
    
    assert "Na" in facts or "sodium" in facts or "H2O" in facts or "water" in facts, "Chemistry facts extraction failed"
    assert goal in ["NaOH", "sodium hydroxide", "NaCl"], "Chemistry goal extraction failed"

    # Geometry query test
    geom_query = "Prove Congruent(AB, EF) given Congruent(AB, CD) and Congruent(CD, EF)"
    facts, goal = fallback_query_parser(geom_query, "geometry")
    
    print(f"\nGeometry Query: '{geom_query}'")
    print(f"Extracted Facts: {facts}")
    print(f"Extracted Goal:  {goal}")
    
    assert "Congruent(AB,CD)" in facts and "Congruent(CD,EF)" in facts, "Geometry facts extraction failed"
    assert goal == "Congruent(AB,EF)", "Geometry goal extraction failed"
    
    print("✅ NLP Parser Verification Passed.")


def test_qdrant_embedding_and_routing():
    print("\n--- Test 2: Ingestion & Qdrant Semantic Routing ---")
    
    # 1. Fetch from Neo4j (will run or use fallbacks if Neo4j is blank)
    try:
        facts, rules = get_neo4j_facts_and_rules()
    except Exception as e:
        print(f"[NOTE] Neo4j fetch skipped/unreachable ({e}). Creating mock dataset for Vector Store synchronization...")
        facts = [
            {"id": "chem_Na", "value": "Na", "domain": "chemistry", "label": "sodium", "formula": "Na"},
            {"id": "chem_H2O", "value": "H2O", "domain": "chemistry", "label": "water", "formula": "H2O"},
            {"id": "chem_NaOH", "value": "NaOH", "domain": "chemistry", "label": "sodium hydroxide", "formula": "NaOH"},
            {"id": "chem_HCl", "value": "HCl", "domain": "chemistry", "label": "hydrochloric acid", "formula": "HCl"},
            {"id": "chem_NaCl", "value": "NaCl", "domain": "chemistry", "label": "sodium chloride", "formula": "NaCl"},
        ]
        rules = [
            {"id": "r1", "name": "Sodium Hydration", "domain": "chemistry", "description": "Sodium reacting with water.", "source": "Textbook"}
        ]
        
    # 2. Ingest to Qdrant
    print("Synchronizing vectors in Qdrant...")
    ingest_to_qdrant(facts, rules)
    
    # 3. Route Query
    print("\nExecuting routing search for: 'I have sodium and water, how do I make sodium hydroxide?'")
    mapped_facts, mapped_goal = route_query(
        "I have sodium and water, how do I make sodium hydroxide?", 
        "chemistry"
    )
    
    print(f"Mapped Initial Facts in Graph: {[f.value for f in mapped_facts]}")
    print(f"Mapped Goal in Graph:          {mapped_goal.value}")
    
    assert any(f.value == "Na" for f in mapped_facts), "Failed to semantically map 'sodium' to graph node 'Na'"
    assert any(f.value == "H2O" for f in mapped_facts), "Failed to semantically map 'water' to graph node 'H2O'"
    assert mapped_goal.value == "NaOH", "Failed to semantically map 'sodium hydroxide' to graph goal 'NaOH'"
    
    print("✅ Qdrant Semantic Routing Verification Passed.")


def test_full_neuro_symbolic_solving_and_explanation():
    print("\n--- Test 3: Full Neuro-Symbolic Solve & Explanation ---")
    
    # 1. Route natural language query
    mapped_facts, mapped_goal = route_query(
        "I have sodium, water, and hydrochloric acid. Can I synthesize sodium chloride salt?", 
        "chemistry"
    )
    
    # 2. Predefined chemistry rules for reasoning
    from domains.chemistry import ChemistryParser
    parser = ChemistryParser()
    
    raw_rules = [
        {"id": "r1", "name": "Sodium Hydration", "inputs": ["Na", "H2O"], "outputs": ["NaOH", "H2"], "description": ""},
        {"id": "r3", "name": "Neutralization", "inputs": ["NaOH", "HCl"], "outputs": ["NaCl", "H2O"], "description": ""}
    ]
    rules = [parser.parse_rule(r) for r in raw_rules]
    
    # 3. Solve using symbolic core engine
    print(f"Initial State: {[f.value for f in mapped_facts]}")
    print(f"Target Goal:   {mapped_goal.value}")
    
    engine = ForwardChainingEngine(rules)
    result = engine.solve(mapped_facts, mapped_goal)
    
    print(f"Symbolic Solver Goal Reached: {result.goal_reached}")
    print(f"Applied Rules Trace:           {result.applied_rule_ids}")
    
    assert result.goal_reached is True, "Symbolic solver failed to prove NaCl synthesis!"
    
    # 4. Generate explanation
    steps = [
        ExecutionStepResponse(
            rule_id=step.rule_id,
            fired_rule_repr=step.fired_rule_repr,
            new_facts=[f.value for f in step.new_facts]
        ) for step in result.execution_trace
    ]
    
    request = ExplainRequest(
        query="I have sodium, water, and hydrochloric acid. Can I synthesize sodium chloride salt?",
        domain="chemistry",
        execution_trace=steps
    )
    
    print("\nTriggering Explanation Agent...")
    explanation_response = asyncio.run(explain_proof(request))
    
    print("\n--- Generated Explanation ---")
    print(explanation_response.explanation)
    print("-----------------------------")
    print(f"Generated via LLM (Structured): {explanation_response.structured}")
    
    assert len(explanation_response.explanation) > 100, "Explanation generated was empty or too short."
    print("✅ Neuro-Symbolic Chaining & Explanation Verification Passed.")


if __name__ == "__main__":
    print("==================================================")
    print("       OMNI-IPS PHASE 3 PIPELINE SCAFFOLD TEST     ")
    print("==================================================")
    try:
        test_offline_query_parsing()
        test_qdrant_embedding_and_routing()
        # Only run solver integration if we succeeded mapping (needs active containers)
        test_full_neuro_symbolic_solving_and_explanation()
        print("\n🎉 ALL PHASE 3 INTEGRATION AND GRAPHRAG PIPELINE TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ PIPELINE SCAFFOLD TEST FAILED: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
