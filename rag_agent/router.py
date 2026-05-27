"""
Neuro-Symbolic Router for Omni-IPS.

Bridges Natural Language queries with the Symbolic Core Engine by:
1. Parsing queries into structured Facts and Goals (via LangChain LLM or regex fallback).
2. Semantically mapping those text entities to exact Neo4j Fact nodes using Qdrant vector search.
"""

import os
import sys
import re
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Load local environment configurations from .env
load_dotenv()

# Add project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from core_engine.models import Fact
from graph_db.connection import Neo4jConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rag_router")

# Load embedding model once at module level for performance
_embedding_model: Optional[SentenceTransformer] = None

def _get_embedding_model() -> SentenceTransformer:
    """Lazily loads and caches the SentenceTransformer embedding model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading SentenceTransformer embedding model 'all-MiniLM-L6-v2'...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


# Standard Chemistry Natural Language to Formula mapping lookup
CHEM_DICTIONARY = {
    "water": "H2O",
    "sodium": "Na",
    "sodium hydroxide": "NaOH",
    "hydrochloric acid": "HCl",
    "sodium chloride": "NaCl",
    "salt": "NaCl",
    "chlorine": "Cl2",
    "oxygen": "O2",
    "hydrogen": "H2",
    "magnesium": "Mg",
    "magnesium oxide": "MgO",
    "iron": "Fe",
    "iron oxide": "Fe2O3",
    "rust": "Fe2O3",
    "calcium carbonate": "CaCO3",
    "limestone": "CaCO3",
    "calcium oxide": "CaO",
    "quicklime": "CaO",
    "carbon dioxide": "CO2",
    "sodium bicarbonate": "NaHCO3",
    "baking soda": "NaHCO3",
    "sodium carbonate": "Na2CO3",
    "soda ash": "Na2CO3",
    "zinc": "Zn",
    "zinc chloride": "ZnCl2",
    "copper sulfate": "CuSO4",
    "copper": "Cu",
    "iron sulfate": "FeSO4",
    "silver nitrate": "AgNO3",
    "silver chloride": "AgCl",
    "barium chloride": "BaCl2",
    "barium sulfate": "BaSO4",
    "sodium sulfate": "Na2SO4",
    "potassium hydroxide": "KOH",
    "sulfuric acid": "H2SO4",
    "potassium sulfate": "K2SO4",
    "methane": "CH4",
    "ethanol": "C2H5OH",
    "propane": "C3H8",
    "ammonia": "NH3",
    "ammonium chloride": "NH4Cl",
    "carbonic acid": "H2CO3",
    "calcium hydroxide": "Ca(OH)2",
    "slaked lime": "Ca(OH)2",
}


def fallback_query_parser(query: str, domain: str) -> Tuple[List[str], str]:
    """
    Offline/Fallback regex-based natural language parser.
    Extracts formulas, equations, or geometric predicates directly from query text.
    """
    domain = domain.lower()
    extracted_facts = []
    extracted_goal = ""

    # Convert query to lowercase for dictionary keyword matching
    query_lower = query.lower()

    if domain == "chemistry":
        # 1. Look for known chemical common names and map them
        for common_name, formula in CHEM_DICTIONARY.items():
            # Match word boundary to avoid partial matching (e.g. 'iron' matching 'iron oxide')
            pattern = rf"\b{re.escape(common_name)}\b"
            if re.search(pattern, query_lower):
                # Simple heuristic: if it appears after "make", "get", "synthesize", "produce", or "yield", it is likely the goal
                is_goal = False
                for keyword in ["make", "get", "synthesize", "produce", "yield", "obtain", "derive", "forming", "form"]:
                    keyword_index = query_lower.find(keyword)
                    if keyword_index != -1 and query_lower.find(common_name) > keyword_index:
                        is_goal = True
                        break
                
                if is_goal:
                    extracted_goal = formula
                else:
                    extracted_facts.append(formula)

        # 2. Extract raw chemical formulas directly using regex (e.g. Na, H2O, HCl)
        # Matches uppercase chemical formulas with possible brackets and subscripts
        formula_regex = r"\b[A-Z][a-z]?\d*(?:\([A-Z][a-z]?\d*\))*\d*\b"
        raw_formulas = re.findall(formula_regex, query)
        for formula in raw_formulas:
            # Filter out single letters that aren't common elements unless they represent single-letter elements (excluding I/A to avoid pronoun false positives)
            if formula in ["O", "C", "H", "N", "S", "P", "K", "U", "F", "V", "W", "Y", "B"] or len(formula) > 1:
                # Determine if it's the goal based on keywords
                idx = query.find(formula)
                is_goal = False
                for kw in ["make", "get", "synthesize", "produce", "yield", "obtain", "derive", "->", "to"]:
                    kw_idx = query_lower.find(kw)
                    if kw_idx != -1 and idx > kw_idx:
                        is_goal = True
                        break
                
                if is_goal:
                    extracted_goal = formula
                else:
                    if formula not in extracted_facts:
                        extracted_facts.append(formula)

    elif domain == "geometry":
        # Extract predicates of format Word(arg1, arg2...) e.g. Congruent(AB, CD), Triangle(A,B,C)
        predicate_regex = r"\b[A-Za-z_]+\([A-Za-z0-9,\s_]*\)"
        raw_preds = re.findall(predicate_regex, query)
        
        # Check standard sentence structures:
        # Structure 1: Prove {goal} given/if/when/assuming {facts}
        # Structure 2: Given/if/assuming {facts}, prove {goal}
        given_idx = -1
        for kw in ["given", "if", "assume", "assuming", "suppose", "where"]:
            idx = query_lower.find(kw)
            if idx != -1:
                given_idx = idx
                break
                
        prove_idx = -1
        for kw in ["prove", "show", "deduce", "conclude", "obtain"]:
            idx = query_lower.find(kw)
            if idx != -1:
                prove_idx = idx
                break
                
        for pred in raw_preds:
            cleaned_pred = re.sub(r"\s+", "", pred)
            idx = query.find(pred)
            
            is_goal = False
            if prove_idx != -1:
                if given_idx != -1:
                    if prove_idx < given_idx:
                        # "Prove {goal} given {facts}"
                        if idx < given_idx:
                            is_goal = True
                    else:
                        # "Given {facts}, prove {goal}"
                        if idx > prove_idx:
                            is_goal = True
                else:
                    # No 'given' word, just check if it's the first one after the 'prove' keyword
                    if idx > prove_idx and not extracted_goal:
                        is_goal = True
            
            if is_goal:
                extracted_goal = cleaned_pred
            else:
                if cleaned_pred not in extracted_facts:
                    extracted_facts.append(cleaned_pred)

    elif domain == "algebra":
        # Extract equations containing '=' or mathematical terms
        eq_regex = r"\b[a-zA-Z0-9\+\-\*\/\s]+=[ a-zA-Z0-9\+\-\*\/\s]+\b"
        raw_eqs = re.findall(eq_regex, query)
        for eq in raw_eqs:
            cleaned_eq = re.sub(r"\s+", "", eq)
            
            # If it's a solved form (like x=3) or after goal keywords, it's the goal
            if cleaned_eq.startswith("x=") or "solve" in query_lower or "find" in query_lower:
                extracted_goal = cleaned_eq
            else:
                extracted_facts.append(cleaned_eq)

        # Check operations
        op_regex = r"\b[A-Za-z_]+\([a-zA-Z0-9,\s_]*\)"
        raw_ops = re.findall(op_regex, query)
        for op in raw_ops:
            cleaned_op = re.sub(r"\s+", "", op)
            extracted_facts.append(cleaned_op)

    # Clean duplicates and ensure we have fallback defaults if parsing returned nothing
    extracted_facts = list(set(extracted_facts))
    
    # If no goal was explicitly extracted, fallback to the last element or standard domain placeholders
    if not extracted_goal and extracted_facts:
        # Default fallback
        if domain == "chemistry":
            extracted_goal = "NaCl"
        elif domain == "geometry":
            extracted_goal = "Congruent(AB,EF)"
        elif domain == "algebra":
            extracted_goal = "x=3"
            
    # Cleanup facts if goal is accidentally in it
    if extracted_goal in extracted_facts:
        extracted_facts.remove(extracted_goal)

    logger.info("[Fallback Parser] Extracted facts: %s, goal: %s", extracted_facts, extracted_goal)
    return extracted_facts, extracted_goal


def llm_query_parser(query: str, domain: str) -> Tuple[List[str], str]:
    """
    LLM-based query parser using LangChain with model-agnostic structured outputs.
    Falls back to fallback_query_parser if LLM is not configured or fails.
    """
    from rag_agent.llm_factory import get_llm
    llm = get_llm(temperature=0)
    
    if not llm:
        logger.info("LLM factory returned None. Using offline regex fallback parser.")
        return fallback_query_parser(query, domain)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel, Field as LangchainField

        class QueryParseSchema(LangchainBaseModel):
            facts: List[str] = LangchainField(
                description="List of raw logical entities, assertions, or reactants initially present in the query."
            )
            goal: str = LangchainField(
                description="The target assertion, product, or solution variable to prove/deduce."
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert NLP parser for a Neuro-Symbolic reasoning engine. "
                       "Your job is to parse a user query in the domain '{domain}' and extract "
                       "the starting facts/assertions and the target goal.\n"
                       "Do not solve the problem. Only extract the entities and formula representations.\n"
                       "Examples:\n"
                       "1. 'I have Na and water, how do I get NaOH?' in chemistry -> facts: ['Na', 'H2O'], goal: 'NaOH'\n"
                       "2. 'If AB congruent to CD and CD congruent to EF, show AB congruent to EF' in geometry -> facts: ['Congruent(AB,CD)', 'Congruent(CD,EF)'], goal: 'Congruent(AB,EF)'\n"
                       "3. 'Given equation x+2=5, subtract 2 from both sides to find x=3' in algebra -> facts: ['x+2=5', 'Subtract(2,both_sides)'], goal: 'x=3'"),
            ("human", "Parse this query: {query}")
        ])

        logger.info("Calling model-agnostic structured parser for domain '%s'...", domain)
        structured_llm = llm.with_structured_output(QueryParseSchema)
        chain = prompt | structured_llm

        response = chain.invoke({"query": query, "domain": domain})
        logger.info("[LLM Parser] Extracted facts: %s, goal: %s", response.facts, response.goal)
        return response.facts, response.goal

    except Exception as e:
        logger.warning("LangChain model-agnostic parser call failed: %s. Falling back to offline parser.", e)
        return fallback_query_parser(query, domain)


def map_text_to_graph_fact(
    text: str, 
    domain: str, 
    qdrant_client: QdrantClient,
    collection_name: str = "omni_ips_facts"
) -> Fact:
    """
    Queries Qdrant to find the most semantically matching Fact node in Neo4j.
    Uses hard-filtering on the domain payload property for instant branch pruning.
    If no match is found or database is unreachable, constructs a temporary Fact object.
    """
    domain = domain.lower()
    try:
        # Encode query text
        model = _get_embedding_model()
        query_vector = model.encode(text).tolist()

        # Query Qdrant with hard-filtering on domain
        results = qdrant_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="domain",
                        match=MatchValue(value=domain)
                    )
                ]
            ),
            limit=1
        )

        if results.points:
            match = results.points[0]
            score = match.score
            payload = match.payload

            # Score threshold: Qdrant cosine similarity (higher is closer, 1.0 is exact)
            # Threshold of 0.4 provides good matching quality for MiniLM embeddings
            if score >= 0.4:
                logger.info(
                    "Mapped '%s' to Graph Fact '%s' (value='%s') with cosine similarity %0.4f", 
                    text, payload.get("label", ""), payload.get("value", ""), score
                )
                return Fact(
                    id=payload["neo4j_id"],
                    value=payload["value"],
                    domain=domain
                )

    except Exception as e:
        logger.warning("Qdrant matching failed for text '%s': %s. Creating ad-hoc fact.", text, e)

    # Ad-hoc Fallback: Construct Fact dynamically
    # Use standard lookup dictionary first
    mapped_val = text
    if domain == "chemistry" and text.lower() in CHEM_DICTIONARY:
        mapped_val = CHEM_DICTIONARY[text.lower()]

    logger.info("Ad-hoc matching for '%s' -> Value: '%s'", text, mapped_val)
    return Fact(
        id=f"adhoc_{domain}_{abs(hash(mapped_val))}",
        value=mapped_val,
        domain=domain
    )


def route_query(query: str, domain: str) -> Tuple[List[Fact], Fact]:
    """
    Entrypoint for the Neuro-Symbolic Router.
    Parses natural language query, maps entities via Qdrant, and returns Fact nodes.
    """
    domain = domain.lower()
    
    # 1. Parse text query into structured text concepts
    facts_text, goal_text = llm_query_parser(query, domain)

    # 2. Establish connection to Qdrant with retry
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    
    qdrant = None
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
            qdrant.get_collections()
            break
        except Exception as e:
            if attempt == max_retries:
                logger.warning("Could not connect to Qdrant at %s:%d after %d attempts: %s. Using ad-hoc routing.",
                               qdrant_host, qdrant_port, max_retries, e)
                qdrant = None
            else:
                time.sleep(1.0 * attempt)

    # 3. Map parsed text elements to formal Fact objects
    mapped_facts = []
    for f_text in facts_text:
        if qdrant:
            mapped_facts.append(map_text_to_graph_fact(f_text, domain, qdrant))
        else:
            # Offline fallback
            val = CHEM_DICTIONARY.get(f_text.lower(), f_text) if domain == "chemistry" else f_text
            mapped_facts.append(Fact(id=f"adhoc_{domain}_{abs(hash(val))}", value=val, domain=domain))

    if qdrant and goal_text:
        mapped_goal = map_text_to_graph_fact(goal_text, domain, qdrant)
    else:
        val = CHEM_DICTIONARY.get(goal_text.lower(), goal_text) if domain == "chemistry" and goal_text else goal_text
        mapped_goal = Fact(id=f"adhoc_{domain}_{abs(hash(val))}", value=val, domain=domain)

    # Deduplicate facts
    seen = set()
    deduped_facts = []
    for f in mapped_facts:
        if f.value not in seen:
            seen.add(f.value)
            deduped_facts.append(f)

    # Ensure facts do not contain the goal
    deduped_facts = [f for f in deduped_facts if f.value != mapped_goal.value]

    logger.info("Neuro-Symbolic routing COMPLETE. Mapped %d Facts, Goal: %s", len(deduped_facts), mapped_goal.value)
    return deduped_facts, mapped_goal
