from domains.base import DomainParser
from core_engine.models import Fact, Rule

class AlgebraParser(DomainParser):
    """
    Concrete syntax parser for Elementary Algebra.
    Parses equations, operations, and variables like x + 2 = 5 or Solve(x).
    """
    @property
    def domain_name(self) -> str:
        return "algebra"

    def parse_fact(self, raw_input: str, fact_id: str) -> Fact:
        cleaned = raw_input.replace(" ", "")
        attributes = {}
        if "=" in cleaned:
            parts = cleaned.split("=")
            attributes["lhs"] = parts[0]
            attributes["rhs"] = parts[1]
            attributes["is_equation"] = True
        else:
            attributes["is_equation"] = False

        return Fact(
            id=fact_id,
            value=cleaned,
            domain=self.domain_name,
            attributes=attributes
        )

    def parse_rule(self, raw_rule: dict) -> Rule:
        rule_id = raw_rule["id"]
        name = raw_rule.get("name", f"Algebraic Law {rule_id}")
        description = raw_rule.get("description", f"Algebraic Transformation: {raw_rule['inputs']} -> {raw_rule['outputs']}")

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
