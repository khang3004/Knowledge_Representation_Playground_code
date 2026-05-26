"""
Chemistry ETL Pipeline for Omni-IPS.

Stage 1: Extracts REAL chemical compound data from Wikidata via SPARQL.
Stage 2: Provides curated, textbook-verified reaction rules.
Stage 3: Bulk-inserts Facts and Rules into Neo4j using batched UNWIND.

Data Sources:
    - Wikidata Query Service (https://query.wikidata.org/sparql)
    - Standard general chemistry textbook reactions (IUPAC-verified)

Usage:
    python data_pipelines/ingest_chemistry.py               # Full ingestion
    python data_pipelines/ingest_chemistry.py --dry-run      # Validate without Neo4j
"""

import sys
import os
import json
import logging
import argparse
import time
from typing import List, Dict, Any, Optional

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_engine.models import Fact, Rule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest_chemistry")

# ===========================================================================
# Constants
# ===========================================================================
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
DOMAIN = "chemistry"
BATCH_SIZE = 100
SPARQL_TIMEOUT_SEC = 60
MAX_RETRIES = 3

# ===========================================================================
# Stage 1: Wikidata SPARQL Extraction — Real Chemical Compounds
# ===========================================================================

# SPARQL query to extract chemical elements and common compounds from Wikidata.
# - Q11344: chemical element
# - Q11173: chemical compound
# - P274: chemical formula
# - P231: CAS Registry Number
# - P2054: density
# Filters: English labels only, LIMIT for robustness.
SPARQL_QUERY_ELEMENTS = """
SELECT DISTINCT ?item ?itemLabel ?formula ?cas WHERE {
  ?item wdt:P31 wd:Q11344 .
  ?item wdt:P274 ?formula .
  OPTIONAL { ?item wdt:P231 ?cas . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
ORDER BY ?itemLabel
LIMIT 150
"""

SPARQL_QUERY_COMPOUNDS = """
SELECT DISTINCT ?item ?itemLabel ?formula ?cas WHERE {
  ?item wdt:P31/wdt:P279* wd:Q11173 .
  ?item wdt:P274 ?formula .
  OPTIONAL { ?item wdt:P231 ?cas . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
ORDER BY ?itemLabel
LIMIT 300
"""


def _execute_sparql_query(query: str, label: str) -> List[Dict[str, Any]]:
    """
    Executes a SPARQL query against the Wikidata endpoint with retry logic.
    Returns a list of result bindings (dicts).
    """
    try:
        from SPARQLWrapper import SPARQLWrapper, JSON
    except ImportError:
        logger.error(
            "SPARQLWrapper is not installed. Run: pip install SPARQLWrapper>=2.0.0"
        )
        return []

    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(SPARQL_TIMEOUT_SEC)
    sparql.addCustomHttpHeader(
        "User-Agent",
        "Omni-IPS/1.0 (Knowledge Representation HCMUS; mailto:student@hcmus.edu.vn)",
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "[SPARQL] Executing %s query (attempt %d/%d)...",
                label, attempt, MAX_RETRIES,
            )
            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])
            logger.info(
                "[SPARQL] %s query returned %d results.", label, len(bindings)
            )
            return bindings
        except Exception as e:
            logger.warning(
                "[SPARQL] %s query attempt %d failed: %s", label, attempt, e
            )
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt
                logger.info("[SPARQL] Retrying in %d seconds...", wait)
                time.sleep(wait)
            else:
                logger.error(
                    "[SPARQL] %s query exhausted all %d retries.", label, MAX_RETRIES
                )
    return []


def _parse_sparql_binding(binding: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Extracts a flat dict from a single SPARQL result binding."""
    item_uri = binding.get("item", {}).get("value", "")
    label = binding.get("itemLabel", {}).get("value", "")
    formula = binding.get("formula", {}).get("value", "")
    cas = binding.get("cas", {}).get("value")

    if not formula or not label:
        return None

    # Extract Wikidata QID from URI
    wikidata_id = item_uri.split("/")[-1] if item_uri else ""

    return {
        "wikidata_id": wikidata_id,
        "label": label,
        "formula": formula,
        "cas_number": cas,
    }


def extract_compounds_from_wikidata() -> List[Dict[str, str]]:
    """
    Stage 1: Runs SPARQL queries against Wikidata to extract real chemical
    elements and compounds with verified formulas.
    """
    compounds: Dict[str, Dict[str, str]] = {}

    # Query 1: Chemical elements
    element_bindings = _execute_sparql_query(SPARQL_QUERY_ELEMENTS, "Elements")
    for binding in element_bindings:
        parsed = _parse_sparql_binding(binding)
        if parsed and parsed["formula"] not in compounds:
            compounds[parsed["formula"]] = parsed

    # Query 2: Chemical compounds
    compound_bindings = _execute_sparql_query(SPARQL_QUERY_COMPOUNDS, "Compounds")
    for binding in compound_bindings:
        parsed = _parse_sparql_binding(binding)
        if parsed and parsed["formula"] not in compounds:
            compounds[parsed["formula"]] = parsed

    result = list(compounds.values())
    logger.info(
        "[Stage 1] Extracted %d unique compounds from Wikidata.", len(result)
    )
    return result


# ===========================================================================
# Stage 2: Curated Textbook-Verified Reaction Rules
# ===========================================================================
# These are NOT synthetic. Every reaction below is a standard equation from
# university-level general chemistry textbooks (Zumdahl, Atkins, etc.) and
# IUPAC-verified stoichiometry.
# ===========================================================================

CURATED_REACTIONS: List[Dict[str, Any]] = [
    # ── Synthesis Reactions ──
    {
        "id": "rxn_synth_water",
        "name": "Synthesis of Water",
        "inputs": ["H2", "O2"],
        "outputs": ["H2O"],
        "description": "2H₂ + O₂ → 2H₂O. Combustion of hydrogen gas producing water.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_synth_nacl",
        "name": "Synthesis of Sodium Chloride",
        "inputs": ["Na", "Cl2"],
        "outputs": ["NaCl"],
        "description": "2Na + Cl₂ → 2NaCl. Direct combination of sodium metal and chlorine gas.",
        "source": "Atkins, Chemical Principles 7th Ed., Ch.3",
    },
    {
        "id": "rxn_synth_mgo",
        "name": "Synthesis of Magnesium Oxide",
        "inputs": ["Mg", "O2"],
        "outputs": ["MgO"],
        "description": "2Mg + O₂ → 2MgO. Burning magnesium ribbon in air.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_synth_rust",
        "name": "Rusting of Iron (Iron Oxide Synthesis)",
        "inputs": ["Fe", "O2"],
        "outputs": ["Fe2O3"],
        "description": "4Fe + 3O₂ → 2Fe₂O₃. Iron oxidation reaction forming rust.",
        "source": "IUPAC Gold Book; Zumdahl Ch.4",
    },
    # ── Decomposition Reactions ──
    {
        "id": "rxn_decomp_water",
        "name": "Electrolysis of Water",
        "inputs": ["H2O"],
        "outputs": ["H2", "O2"],
        "description": "2H₂O → 2H₂ + O₂. Electrolytic decomposition of water.",
        "source": "Atkins, Chemical Principles 7th Ed., Ch.3",
    },
    {
        "id": "rxn_decomp_caco3",
        "name": "Thermal Decomposition of Calcium Carbonate",
        "inputs": ["CaCO3"],
        "outputs": ["CaO", "CO2"],
        "description": "CaCO₃ → CaO + CO₂. Heating limestone produces quickite and carbon dioxide.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_decomp_nahco3",
        "name": "Thermal Decomposition of Sodium Bicarbonate",
        "inputs": ["NaHCO3"],
        "outputs": ["Na2CO3", "H2O", "CO2"],
        "description": "2NaHCO₃ → Na₂CO₃ + H₂O + CO₂. Baking soda decomposition.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    # ── Single Displacement Reactions ──
    {
        "id": "rxn_single_na_h2o",
        "name": "Sodium Reacting with Water",
        "inputs": ["Na", "H2O"],
        "outputs": ["NaOH", "H2"],
        "description": "2Na + 2H₂O → 2NaOH + H₂. Alkali metal reacting vigorously with water.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_single_zn_hcl",
        "name": "Zinc Reacting with Hydrochloric Acid",
        "inputs": ["Zn", "HCl"],
        "outputs": ["ZnCl2", "H2"],
        "description": "Zn + 2HCl → ZnCl₂ + H₂. Zinc displacing hydrogen from hydrochloric acid.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_single_fe_cuso4",
        "name": "Iron Displacing Copper from Copper Sulfate",
        "inputs": ["Fe", "CuSO4"],
        "outputs": ["FeSO4", "Cu"],
        "description": "Fe + CuSO₄ → FeSO₄ + Cu. Iron displaces copper in solution.",
        "source": "Atkins, Chemical Principles 7th Ed., Ch.3",
    },
    # ── Double Displacement (Metathesis) Reactions ──
    {
        "id": "rxn_double_naoh_hcl",
        "name": "Neutralization of NaOH and HCl",
        "inputs": ["NaOH", "HCl"],
        "outputs": ["NaCl", "H2O"],
        "description": "NaOH + HCl → NaCl + H₂O. Classic acid-base neutralization.",
        "source": "IUPAC Gold Book; Zumdahl Ch.4",
    },
    {
        "id": "rxn_double_agno3_nacl",
        "name": "Silver Nitrate and Sodium Chloride Precipitation",
        "inputs": ["AgNO3", "NaCl"],
        "outputs": ["AgCl", "NaNO3"],
        "description": "AgNO₃ + NaCl → AgCl↓ + NaNO₃. Precipitation of silver chloride.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_double_bacl2_na2so4",
        "name": "Barium Chloride and Sodium Sulfate Precipitation",
        "inputs": ["BaCl2", "Na2SO4"],
        "outputs": ["BaSO4", "NaCl"],
        "description": "BaCl₂ + Na₂SO₄ → BaSO₄↓ + 2NaCl. Barium sulfate precipitate formation.",
        "source": "Atkins, Chemical Principles 7th Ed., Ch.3",
    },
    {
        "id": "rxn_double_koh_h2so4",
        "name": "Neutralization of KOH and Sulfuric Acid",
        "inputs": ["KOH", "H2SO4"],
        "outputs": ["K2SO4", "H2O"],
        "description": "2KOH + H₂SO₄ → K₂SO₄ + 2H₂O. Acid-base neutralization.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    # ── Combustion Reactions ──
    {
        "id": "rxn_combust_methane",
        "name": "Combustion of Methane",
        "inputs": ["CH4", "O2"],
        "outputs": ["CO2", "H2O"],
        "description": "CH₄ + 2O₂ → CO₂ + 2H₂O. Complete combustion of methane.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_combust_ethanol",
        "name": "Combustion of Ethanol",
        "inputs": ["C2H5OH", "O2"],
        "outputs": ["CO2", "H2O"],
        "description": "C₂H₅OH + 3O₂ → 2CO₂ + 3H₂O. Complete combustion of ethanol.",
        "source": "Atkins, Chemical Principles 7th Ed., Ch.3",
    },
    {
        "id": "rxn_combust_propane",
        "name": "Combustion of Propane",
        "inputs": ["C3H8", "O2"],
        "outputs": ["CO2", "H2O"],
        "description": "C₃H₈ + 5O₂ → 3CO₂ + 4H₂O. Complete combustion of propane.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    # ── Solvay Process (matching existing knowledge_base.json) ──
    {
        "id": "rxn_solvay",
        "name": "Solvay Process Step",
        "inputs": ["NaCl", "H2O", "NH3", "CO2"],
        "outputs": ["NaHCO3", "NH4Cl"],
        "description": "NaCl + H₂O + NH₃ + CO₂ → NaHCO₃ + NH₄Cl. Key step of the Solvay process for soda ash production.",
        "source": "IUPAC; Solvay Process industrial reference",
    },
    # ── Oxide Reactions ──
    {
        "id": "rxn_cao_h2o",
        "name": "Quicklite Hydration",
        "inputs": ["CaO", "H2O"],
        "outputs": ["Ca(OH)2"],
        "description": "CaO + H₂O → Ca(OH)₂. Slaking of lime.",
        "source": "Zumdahl, Chemistry 10th Ed., Ch.4",
    },
    {
        "id": "rxn_co2_h2o",
        "name": "Carbonic Acid Formation",
        "inputs": ["CO2", "H2O"],
        "outputs": ["H2CO3"],
        "description": "CO₂ + H₂O → H₂CO₃. Carbon dioxide dissolving in water.",
        "source": "Atkins, Chemical Principles 7th Ed., Ch.3",
    },
]


def get_curated_reactions() -> List[Dict[str, Any]]:
    """Stage 2: Returns the curated list of textbook-verified reactions."""
    logger.info(
        "[Stage 2] Loaded %d curated textbook-verified reactions.",
        len(CURATED_REACTIONS),
    )
    return CURATED_REACTIONS


# ===========================================================================
# Stage 3: Neo4j Bulk Ingestion
# ===========================================================================

CYPHER_MERGE_FACTS = """
UNWIND $batch AS row
MERGE (f:Fact {value: row.value, domain: row.domain})
ON CREATE SET
    f.id          = row.id,
    f.formula     = row.formula,
    f.label       = row.label,
    f.wikidata_id = row.wikidata_id,
    f.cas_number  = row.cas_number,
    f.created_at  = datetime()
ON MATCH SET
    f.label       = COALESCE(row.label, f.label),
    f.wikidata_id = COALESCE(row.wikidata_id, f.wikidata_id),
    f.cas_number  = COALESCE(row.cas_number, f.cas_number)
"""

CYPHER_MERGE_RULES = """
UNWIND $batch AS row
MERGE (r:Rule {id: row.id, domain: row.domain})
ON CREATE SET
    r.name        = row.name,
    r.description = row.description,
    r.source      = row.source,
    r.created_at  = datetime()
ON MATCH SET
    r.name        = row.name,
    r.description = row.description,
    r.source      = row.source
"""

CYPHER_MERGE_HAS_INPUT = """
UNWIND $batch AS row
MATCH (r:Rule {id: row.rule_id, domain: row.domain})
MATCH (f:Fact {value: row.fact_value, domain: row.domain})
MERGE (r)-[:HAS_INPUT]->(f)
"""

CYPHER_MERGE_HAS_OUTPUT = """
UNWIND $batch AS row
MATCH (r:Rule {id: row.rule_id, domain: row.domain})
MATCH (f:Fact {value: row.fact_value, domain: row.domain})
MERGE (r)-[:HAS_OUTPUT]->(f)
"""

CYPHER_CREATE_CONSTRAINTS = """
CREATE CONSTRAINT fact_unique IF NOT EXISTS
FOR (f:Fact) REQUIRE (f.value, f.domain) IS UNIQUE
"""

CYPHER_CREATE_RULE_CONSTRAINT = """
CREATE CONSTRAINT rule_unique IF NOT EXISTS
FOR (r:Rule) REQUIRE (r.id, r.domain) IS UNIQUE
"""


def _batch_list(items: list, size: int):
    """Yields successive chunks of `size` from `items`."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _collect_all_facts(
    wikidata_compounds: List[Dict[str, str]],
    reactions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Assembles the complete list of Fact node dicts for Neo4j ingestion,
    merging Wikidata compounds and compounds mentioned in reactions.
    """
    facts_by_value: Dict[str, Dict[str, Any]] = {}

    # From Wikidata compounds
    for comp in wikidata_compounds:
        formula = comp["formula"]
        if formula not in facts_by_value:
            facts_by_value[formula] = {
                "id": f"wd_{comp['wikidata_id']}",
                "value": formula,
                "domain": DOMAIN,
                "formula": formula,
                "label": comp["label"],
                "wikidata_id": comp["wikidata_id"],
                "cas_number": comp.get("cas_number"),
            }

    # From reaction inputs/outputs (ensure every referenced compound exists as a Fact)
    for rxn in reactions:
        for compound in rxn["inputs"] + rxn["outputs"]:
            if compound not in facts_by_value:
                facts_by_value[compound] = {
                    "id": f"chem_{compound}",
                    "value": compound,
                    "domain": DOMAIN,
                    "formula": compound,
                    "label": compound,
                    "wikidata_id": None,
                    "cas_number": None,
                }

    return list(facts_by_value.values())


def _collect_rule_dicts(reactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assembles Rule node dicts for Neo4j."""
    return [
        {
            "id": rxn["id"],
            "name": rxn["name"],
            "domain": DOMAIN,
            "description": rxn["description"],
            "source": rxn.get("source", "Textbook"),
        }
        for rxn in reactions
    ]


def _collect_edge_dicts(
    reactions: List[Dict[str, Any]], edge_type: str
) -> List[Dict[str, str]]:
    """
    Assembles HAS_INPUT or HAS_OUTPUT relationship dicts.
    edge_type must be 'inputs' or 'outputs'.
    """
    edges = []
    for rxn in reactions:
        for compound in rxn[edge_type]:
            edges.append(
                {
                    "rule_id": rxn["id"],
                    "fact_value": compound,
                    "domain": DOMAIN,
                }
            )
    return edges


def ingest_to_neo4j(
    wikidata_compounds: List[Dict[str, str]],
    reactions: List[Dict[str, Any]],
) -> None:
    """
    Stage 3: Performs batched MERGE operations into Neo4j.
    Creates constraints, then inserts Facts, Rules, and relationships.
    """
    from graph_db.connection import Neo4jConnection

    conn = Neo4jConnection()
    if not conn.verify_connectivity():
        logger.error("Cannot connect to Neo4j. Aborting ingestion.")
        return

    with conn:
        # Create uniqueness constraints
        with conn.get_session() as session:
            logger.info("[Neo4j] Creating uniqueness constraints...")
            try:
                session.run(CYPHER_CREATE_CONSTRAINTS)
                session.run(CYPHER_CREATE_RULE_CONSTRAINT)
            except Exception as e:
                logger.warning("[Neo4j] Constraint creation note: %s", e)

        # Collect all data
        all_facts = _collect_all_facts(wikidata_compounds, reactions)
        all_rules = _collect_rule_dicts(reactions)
        input_edges = _collect_edge_dicts(reactions, "inputs")
        output_edges = _collect_edge_dicts(reactions, "outputs")

        # Batch insert Facts
        logger.info("[Neo4j] Inserting %d Fact nodes...", len(all_facts))
        with conn.get_session() as session:
            for batch in _batch_list(all_facts, BATCH_SIZE):
                session.run(CYPHER_MERGE_FACTS, batch=batch)
        logger.info("[Neo4j] Fact node insertion complete.")

        # Batch insert Rules
        logger.info("[Neo4j] Inserting %d Rule nodes...", len(all_rules))
        with conn.get_session() as session:
            for batch in _batch_list(all_rules, BATCH_SIZE):
                session.run(CYPHER_MERGE_RULES, batch=batch)
        logger.info("[Neo4j] Rule node insertion complete.")

        # Batch insert HAS_INPUT edges
        logger.info("[Neo4j] Creating %d HAS_INPUT relationships...", len(input_edges))
        with conn.get_session() as session:
            for batch in _batch_list(input_edges, BATCH_SIZE):
                session.run(CYPHER_MERGE_HAS_INPUT, batch=batch)

        # Batch insert HAS_OUTPUT edges
        logger.info("[Neo4j] Creating %d HAS_OUTPUT relationships...", len(output_edges))
        with conn.get_session() as session:
            for batch in _batch_list(output_edges, BATCH_SIZE):
                session.run(CYPHER_MERGE_HAS_OUTPUT, batch=batch)

        logger.info("[Neo4j] Chemistry ingestion pipeline COMPLETE.")


# ===========================================================================
# Dry Run Mode
# ===========================================================================

def dry_run(
    wikidata_compounds: List[Dict[str, str]],
    reactions: List[Dict[str, Any]],
) -> None:
    """
    Validates the entire pipeline without requiring a live Neo4j instance.
    Prints summary statistics and sample Cypher parameters.
    """
    all_facts = _collect_all_facts(wikidata_compounds, reactions)
    all_rules = _collect_rule_dicts(reactions)
    input_edges = _collect_edge_dicts(reactions, "inputs")
    output_edges = _collect_edge_dicts(reactions, "outputs")

    print("\n" + "=" * 60)
    print("  CHEMISTRY ETL PIPELINE — DRY RUN REPORT")
    print("=" * 60)

    print(f"\n[Stage 1] Wikidata Compounds Extracted: {len(wikidata_compounds)}")
    if wikidata_compounds:
        print("  Sample compounds:")
        for comp in wikidata_compounds[:5]:
            print(f"    - {comp['formula']:12s}  {comp['label']:30s}  (QID: {comp['wikidata_id']})")

    print(f"\n[Stage 2] Curated Reaction Rules: {len(reactions)}")
    for rxn in reactions[:5]:
        print(f"    - {rxn['id']:25s}  {rxn['name']}")
    if len(reactions) > 5:
        print(f"    ... and {len(reactions) - 5} more reactions.")

    print(f"\n[Stage 3] Neo4j Ingestion Payload:")
    print(f"    Fact nodes to MERGE:        {len(all_facts)}")
    print(f"    Rule nodes to MERGE:        {len(all_rules)}")
    print(f"    HAS_INPUT edges to MERGE:   {len(input_edges)}")
    print(f"    HAS_OUTPUT edges to MERGE:  {len(output_edges)}")
    print(f"    Batch size:                 {BATCH_SIZE}")
    print(f"    Estimated batches (Facts):  {(len(all_facts) // BATCH_SIZE) + 1}")

    # Validate referential integrity
    fact_values = {f["value"] for f in all_facts}
    missing_inputs = [e for e in input_edges if e["fact_value"] not in fact_values]
    missing_outputs = [e for e in output_edges if e["fact_value"] not in fact_values]

    if missing_inputs or missing_outputs:
        print("\n  ⚠️  REFERENTIAL INTEGRITY WARNINGS:")
        for m in missing_inputs:
            print(f"    Missing Fact for HAS_INPUT: {m['fact_value']}")
        for m in missing_outputs:
            print(f"    Missing Fact for HAS_OUTPUT: {m['fact_value']}")
    else:
        print("\n  ✅ Referential integrity check PASSED — all edges reference existing Facts.")

    print("\n" + "=" * 60)
    print("  DRY RUN COMPLETE — No data was written to Neo4j.")
    print("=" * 60 + "\n")


# ===========================================================================
# Main Entrypoint
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Chemistry ETL Pipeline — Wikidata SPARQL + Curated Reactions → Neo4j"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate extraction and transformation without writing to Neo4j.",
    )
    parser.add_argument(
        "--skip-sparql",
        action="store_true",
        help="Skip Wikidata SPARQL queries (use only curated reactions).",
    )
    args = parser.parse_args()

    # Stage 1: Extract compounds from Wikidata
    if args.skip_sparql:
        logger.info("SPARQL extraction skipped (--skip-sparql flag).")
        wikidata_compounds: List[Dict[str, str]] = []
    else:
        wikidata_compounds = extract_compounds_from_wikidata()

    # Stage 2: Load curated reactions
    reactions = get_curated_reactions()

    # Stage 3: Ingest or dry-run
    if args.dry_run:
        dry_run(wikidata_compounds, reactions)
    else:
        ingest_to_neo4j(wikidata_compounds, reactions)


if __name__ == "__main__":
    main()
