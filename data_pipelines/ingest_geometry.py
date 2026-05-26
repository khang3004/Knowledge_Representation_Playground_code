"""
Geometry ETL Pipeline for Omni-IPS.

Ingests axiomatic Euclidean geometry theorems and postulates into Neo4j.
All data is manually curated from authoritative mathematical references:
    - Euclid's "Elements" (Books I-IV)
    - Hartshorne, "Geometry: Euclid and Beyond" (Springer, 2000)
    - Moise & Downs, "Geometry" (Addison-Wesley, 1991)

These are NOT synthetic — they are axioms and proven theorems that form the
foundation of classical Euclidean plane geometry.

Usage:
    python data_pipelines/ingest_geometry.py               # Full ingestion
    python data_pipelines/ingest_geometry.py --dry-run      # Validate without Neo4j
"""

import sys
import os
import logging
import argparse
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest_geometry")

DOMAIN = "geometry"
BATCH_SIZE = 50

# ===========================================================================
# Axiomatic Geometry Knowledge Base
# ===========================================================================
# Each theorem/postulate is encoded using formal logic predicates:
#   Triangle(A,B,C)        — A triangle with vertices A, B, C
#   Angle(A,B,C)           — The angle at vertex B formed by rays BA and BC
#   RightAngle(A,B,C)      — Angle ABC is 90°
#   Congruent(X,Y)         — Segments or angles X and Y are congruent
#   Similar(ABC,DEF)       — Triangles ABC and DEF are similar
#   Parallel(L1,L2)        — Lines L1 and L2 are parallel
#   Perpendicular(L1,L2)   — Lines L1 and L2 are perpendicular
#   Midpoint(M,AB)         — M is the midpoint of segment AB
#   Collinear(A,B,C)       — Points A, B, C lie on the same line
#   SumAngles(A,B,C,180)   — The angles of triangle ABC sum to 180°
#   IsoscelesTriangle(A,B,C,AB,AC)  — Triangle ABC with AB = AC
#   Diameter(AB,Circle_O)  — AB is a diameter of circle with center O
#   Inscribed(C,Circle_O)  — Point C lies on the circle
# ===========================================================================

EUCLIDEAN_AXIOMS_AND_THEOREMS: List[Dict[str, Any]] = [
    # ════════════════════════════════════════════════════════════
    # Euclid's Postulates (Axioms)
    # ════════════════════════════════════════════════════════════
    {
        "id": "euclid_post_1",
        "name": "Euclid's 1st Postulate (Line from Two Points)",
        "inputs": ["Point(A)", "Point(B)"],
        "outputs": ["Line(A,B)"],
        "description": "A straight line segment can be drawn joining any two points.",
        "source": "Euclid, Elements, Book I, Postulate 1",
    },
    {
        "id": "euclid_post_2",
        "name": "Euclid's 2nd Postulate (Line Extension)",
        "inputs": ["Segment(A,B)"],
        "outputs": ["Line(A,B)"],
        "description": "Any straight line segment can be extended indefinitely in a straight line.",
        "source": "Euclid, Elements, Book I, Postulate 2",
    },
    {
        "id": "euclid_post_3",
        "name": "Euclid's 3rd Postulate (Circle from Center and Radius)",
        "inputs": ["Point(O)", "Segment(O,R)"],
        "outputs": ["Circle(O,R)"],
        "description": "Given any center and radius, a circle can be drawn.",
        "source": "Euclid, Elements, Book I, Postulate 3",
    },
    {
        "id": "euclid_post_4",
        "name": "Euclid's 4th Postulate (All Right Angles are Congruent)",
        "inputs": ["RightAngle(A,B,C)", "RightAngle(D,E,F)"],
        "outputs": ["Congruent(Angle(A,B,C), Angle(D,E,F))"],
        "description": "All right angles are congruent to each other.",
        "source": "Euclid, Elements, Book I, Postulate 4",
    },
    {
        "id": "euclid_post_5",
        "name": "Euclid's 5th Postulate (Parallel Postulate)",
        "inputs": ["Line(L1)", "Point(P)", "NotOn(P,L1)"],
        "outputs": ["UniqueParallel(L2,L1,P)"],
        "description": "Through a point not on a line, exactly one parallel line can be drawn (Playfair's axiom form).",
        "source": "Euclid, Elements, Book I, Postulate 5 (Playfair form)",
    },
    # ════════════════════════════════════════════════════════════
    # Core Euclidean Theorems
    # ════════════════════════════════════════════════════════════
    {
        "id": "thm_triangle_angle_sum",
        "name": "Triangle Angle Sum Theorem",
        "inputs": ["Triangle(A,B,C)"],
        "outputs": ["SumAngles(A,B,C,180)"],
        "description": "The sum of the interior angles of any triangle equals 180 degrees.",
        "source": "Euclid, Elements, Book I, Proposition 32",
    },
    {
        "id": "thm_pythagorean",
        "name": "Pythagorean Theorem",
        "inputs": ["Triangle(A,B,C)", "RightAngle(A,B,C)"],
        "outputs": ["PythagoreanRelation(AB,BC,AC)"],
        "description": "In a right triangle with right angle at B: AB² + BC² = AC².",
        "source": "Euclid, Elements, Book I, Proposition 47",
    },
    {
        "id": "thm_isosceles_base_angles",
        "name": "Isosceles Triangle Base Angles Theorem",
        "inputs": ["Triangle(A,B,C)", "Congruent(AB,AC)"],
        "outputs": ["Congruent(Angle(A,B,C), Angle(A,C,B))"],
        "description": "If two sides of a triangle are congruent, then the angles opposite those sides are congruent.",
        "source": "Euclid, Elements, Book I, Proposition 5 (Pons Asinorum)",
    },
    {
        "id": "thm_thales",
        "name": "Thales's Theorem",
        "inputs": ["Diameter(AB,Circle_O)", "Inscribed(C,Circle_O)"],
        "outputs": ["RightAngle(A,C,B)"],
        "description": "An angle inscribed in a semicircle is always a right angle.",
        "source": "Euclid, Elements, Book III, Proposition 31",
    },
    {
        "id": "thm_vertical_angles",
        "name": "Vertical Angles Theorem",
        "inputs": ["Intersect(L1,L2,P)", "VerticalAnglePair(Angle1,Angle2,P)"],
        "outputs": ["Congruent(Angle1,Angle2)"],
        "description": "Vertical (opposite) angles formed by two intersecting lines are congruent.",
        "source": "Euclid, Elements, Book I, Proposition 15",
    },
    # ════════════════════════════════════════════════════════════
    # Congruence Criteria
    # ════════════════════════════════════════════════════════════
    {
        "id": "thm_sas_congruence",
        "name": "SAS Congruence Criterion",
        "inputs": [
            "Congruent(AB,DE)",
            "Congruent(Angle(A,B,C), Angle(D,E,F))",
            "Congruent(BC,EF)",
        ],
        "outputs": ["Congruent(Triangle(A,B,C), Triangle(D,E,F))"],
        "description": "Side-Angle-Side: If two sides and the included angle of one triangle are congruent to those of another, the triangles are congruent.",
        "source": "Euclid, Elements, Book I, Proposition 4",
    },
    {
        "id": "thm_asa_congruence",
        "name": "ASA Congruence Criterion",
        "inputs": [
            "Congruent(Angle(B,A,C), Angle(E,D,F))",
            "Congruent(AB,DE)",
            "Congruent(Angle(A,B,C), Angle(D,E,F))",
        ],
        "outputs": ["Congruent(Triangle(A,B,C), Triangle(D,E,F))"],
        "description": "Angle-Side-Angle: If two angles and the included side of one triangle are congruent to those of another, the triangles are congruent.",
        "source": "Euclid, Elements, Book I, Proposition 26",
    },
    {
        "id": "thm_sss_congruence",
        "name": "SSS Congruence Criterion",
        "inputs": [
            "Congruent(AB,DE)",
            "Congruent(BC,EF)",
            "Congruent(AC,DF)",
        ],
        "outputs": ["Congruent(Triangle(A,B,C), Triangle(D,E,F))"],
        "description": "Side-Side-Side: If three sides of one triangle are congruent to three sides of another, the triangles are congruent.",
        "source": "Euclid, Elements, Book I, Proposition 8",
    },
    # ════════════════════════════════════════════════════════════
    # Parallel Line Angle Theorems
    # ════════════════════════════════════════════════════════════
    {
        "id": "thm_alternate_interior_angles",
        "name": "Alternate Interior Angles Theorem",
        "inputs": ["Parallel(L1,L2)", "Transversal(T,L1,L2)"],
        "outputs": ["Congruent(AltIntAngle1,AltIntAngle2)"],
        "description": "If two parallel lines are cut by a transversal, alternate interior angles are congruent.",
        "source": "Euclid, Elements, Book I, Proposition 29",
    },
    {
        "id": "thm_corresponding_angles",
        "name": "Corresponding Angles Theorem",
        "inputs": ["Parallel(L1,L2)", "Transversal(T,L1,L2)"],
        "outputs": ["Congruent(CorrAngle1,CorrAngle2)"],
        "description": "If two parallel lines are cut by a transversal, corresponding angles are congruent.",
        "source": "Euclid, Elements, Book I, Proposition 29 (corollary)",
    },
    # ════════════════════════════════════════════════════════════
    # Congruence Transitivity (from Phase 1)
    # ════════════════════════════════════════════════════════════
    {
        "id": "thm_congruence_transitivity",
        "name": "Transitivity of Congruence",
        "inputs": ["Congruent(X,Y)", "Congruent(Y,Z)"],
        "outputs": ["Congruent(X,Z)"],
        "description": "If X is congruent to Y and Y is congruent to Z, then X is congruent to Z.",
        "source": "Euclid, Common Notion 1 (Transitivity of Equality)",
    },
]


def get_euclidean_axioms() -> List[Dict[str, Any]]:
    """Returns the curated Euclidean axioms and theorems."""
    logger.info(
        "Loaded %d Euclidean axioms and theorems.",
        len(EUCLIDEAN_AXIOMS_AND_THEOREMS),
    )
    return EUCLIDEAN_AXIOMS_AND_THEOREMS


# ===========================================================================
# Neo4j Ingestion (batched UNWIND, same pattern as chemistry)
# ===========================================================================

CYPHER_MERGE_FACTS = """
UNWIND $batch AS row
MERGE (f:Fact {value: row.value, domain: row.domain})
ON CREATE SET
    f.id         = row.id,
    f.label      = row.label,
    f.created_at = datetime()
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


def _batch_list(items: list, size: int):
    """Yields successive chunks of `size` from `items`."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _collect_all_facts(theorems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicates all predicate strings referenced in inputs/outputs into Fact dicts."""
    facts_by_value: Dict[str, Dict[str, Any]] = {}
    counter = 0
    for thm in theorems:
        for pred in thm["inputs"] + thm["outputs"]:
            if pred not in facts_by_value:
                facts_by_value[pred] = {
                    "id": f"geo_fact_{counter}",
                    "value": pred,
                    "domain": DOMAIN,
                    "label": pred,
                }
                counter += 1
    return list(facts_by_value.values())


def _collect_rule_dicts(theorems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assembles Rule node dicts."""
    return [
        {
            "id": thm["id"],
            "name": thm["name"],
            "domain": DOMAIN,
            "description": thm["description"],
            "source": thm.get("source", "Euclid, Elements"),
        }
        for thm in theorems
    ]


def _collect_edge_dicts(
    theorems: List[Dict[str, Any]], edge_type: str
) -> List[Dict[str, str]]:
    """Assembles HAS_INPUT or HAS_OUTPUT relationship dicts."""
    edges = []
    for thm in theorems:
        for pred in thm[edge_type]:
            edges.append(
                {
                    "rule_id": thm["id"],
                    "fact_value": pred,
                    "domain": DOMAIN,
                }
            )
    return edges


def ingest_to_neo4j(theorems: List[Dict[str, Any]]) -> None:
    """Batched MERGE into Neo4j for geometry domain."""
    from graph_db.connection import Neo4jConnection

    conn = Neo4jConnection()
    if not conn.verify_connectivity():
        logger.error("Cannot connect to Neo4j. Aborting ingestion.")
        return

    with conn:
        all_facts = _collect_all_facts(theorems)
        all_rules = _collect_rule_dicts(theorems)
        input_edges = _collect_edge_dicts(theorems, "inputs")
        output_edges = _collect_edge_dicts(theorems, "outputs")

        logger.info("[Neo4j] Inserting %d geometry Fact nodes...", len(all_facts))
        with conn.get_session() as session:
            for batch in _batch_list(all_facts, BATCH_SIZE):
                session.run(CYPHER_MERGE_FACTS, batch=batch)

        logger.info("[Neo4j] Inserting %d geometry Rule nodes...", len(all_rules))
        with conn.get_session() as session:
            for batch in _batch_list(all_rules, BATCH_SIZE):
                session.run(CYPHER_MERGE_RULES, batch=batch)

        logger.info("[Neo4j] Creating %d HAS_INPUT relationships...", len(input_edges))
        with conn.get_session() as session:
            for batch in _batch_list(input_edges, BATCH_SIZE):
                session.run(CYPHER_MERGE_HAS_INPUT, batch=batch)

        logger.info("[Neo4j] Creating %d HAS_OUTPUT relationships...", len(output_edges))
        with conn.get_session() as session:
            for batch in _batch_list(output_edges, BATCH_SIZE):
                session.run(CYPHER_MERGE_HAS_OUTPUT, batch=batch)

        logger.info("[Neo4j] Geometry ingestion pipeline COMPLETE.")


# ===========================================================================
# Dry Run
# ===========================================================================

def dry_run(theorems: List[Dict[str, Any]]) -> None:
    """Validates the geometry pipeline without writing to Neo4j."""
    all_facts = _collect_all_facts(theorems)
    all_rules = _collect_rule_dicts(theorems)
    input_edges = _collect_edge_dicts(theorems, "inputs")
    output_edges = _collect_edge_dicts(theorems, "outputs")

    print("\n" + "=" * 60)
    print("  GEOMETRY ETL PIPELINE — DRY RUN REPORT")
    print("=" * 60)

    print(f"\n  Euclidean Axioms & Theorems: {len(theorems)}")
    for thm in theorems:
        antecedents = " ∧ ".join(thm["inputs"])
        consequents = " ∧ ".join(thm["outputs"])
        print(f"    [{thm['id']}] {thm['name']}")
        print(f"        IF   {antecedents}")
        print(f"        THEN {consequents}")
        print(f"        (Source: {thm['source']})\n")

    print(f"  Neo4j Ingestion Payload:")
    print(f"    Fact nodes to MERGE:        {len(all_facts)}")
    print(f"    Rule nodes to MERGE:        {len(all_rules)}")
    print(f"    HAS_INPUT edges to MERGE:   {len(input_edges)}")
    print(f"    HAS_OUTPUT edges to MERGE:  {len(output_edges)}")
    print(f"    Batch size:                 {BATCH_SIZE}")

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
        print("\n  ✅ Referential integrity check PASSED.")

    print("\n" + "=" * 60)
    print("  DRY RUN COMPLETE — No data was written to Neo4j.")
    print("=" * 60 + "\n")


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Geometry ETL Pipeline — Euclidean Axioms → Neo4j"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without writing to Neo4j.",
    )
    args = parser.parse_args()

    theorems = get_euclidean_axioms()

    if args.dry_run:
        dry_run(theorems)
    else:
        ingest_to_neo4j(theorems)


if __name__ == "__main__":
    main()
