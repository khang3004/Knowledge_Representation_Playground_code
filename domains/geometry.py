import re
from domains.base import DomainParser
from core_engine.models import Fact, Rule

class GeometryParser(DomainParser):
    """
    Concrete syntax parser for Plane Geometry.
    Parses geometric assertions such as Congruent(AB, CD) or Similar(ABC, DEF)
    and handles relation/arguments canonical forms.
    """
    @property
    def domain_name(self) -> str:
        return "geometry"

    def parse_fact(self, raw_input: str, fact_id: str) -> Fact:
        cleaned = raw_input.replace(" ", "")
        match = re.match(r"(\w+)\(([^)]+)\)", cleaned)
        relation = "Atom"
        args = [cleaned]
        canonical_val = cleaned

        if match:
            relation = match.group(1)
            args = [arg.strip() for arg in match.group(2).split(",")]

            # For commutative geometric relations like Congruent, Similar, Parallel, etc.
            # sort arguments to form a standard canonical representation
            commutative_relations = {"Congruent", "Similar", "Parallel", "Intersect"}
            if relation in commutative_relations:
                sorted_args = sorted(args)
                canonical_val = f"{relation}({', '.join(sorted_args)})"
            else:
                canonical_val = f"{relation}({', '.join(args)})"

        return Fact(
            id=fact_id,
            value=canonical_val,
            domain=self.domain_name,
            attributes={"relation": relation, "args": args}
        )

    def parse_rule(self, raw_rule: dict) -> Rule:
        rule_id = raw_rule["id"]
        name = raw_rule.get("name", f"Geometric Theorem {rule_id}")
        description = raw_rule.get("description", f"Theorem: If {' and '.join(raw_rule['inputs'])} then {' and '.join(raw_rule['outputs'])}")

        antecedents = [
            self.parse_fact(ant, f"{rule_id}_ant_{idx}")
            for idx, ant in enumerate(raw_rule["inputs"])
        ]
        consequents = [
            self.parse_fact(cons, f"{rule_id}_cons_{idx}")
            for idx, cons in enumerate(raw_rule["outputs"])
        ]

        return Rule(
            id=rule_id,
            name=name,
            domain=self.domain_name,
            antecedents=antecedents,
            consequents=consequents,
            description=description
        )

    def format_fact(self, fact: Fact) -> str:
        return fact.value
