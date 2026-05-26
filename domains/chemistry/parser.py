from domains.base import DomainParser
from core_engine.models import Fact, Rule

class ChemistryParser(DomainParser):
    """
    Concrete syntax parser for the Chemistry domain.
    Represents compounds as facts and chemical reactions as rules.
    """
    @property
    def domain_name(self) -> str:
        return "chemistry"

    def parse_fact(self, raw_input: str, fact_id: str) -> Fact:
        # Standardizing raw compound representation (e.g., stripping spaces)
        cleaned = raw_input.strip()
        return Fact(
            id=fact_id,
            value=cleaned,
            domain=self.domain_name,
            attributes={"molecular_weight": None} # Extendable
        )

    def parse_rule(self, raw_rule: dict) -> Rule:
        rule_id = raw_rule["id"]
        name = raw_rule.get("name", f"Chemical Reaction {rule_id}")
        description = raw_rule.get("description", f"Reaction: {' + '.join(raw_rule['inputs'])} -> {' + '.join(raw_rule['outputs'])}")

        antecedents = [
            self.parse_fact(reactant, f"{rule_id}_ant_{idx}")
            for idx, reactant in enumerate(raw_rule["inputs"])
        ]
        consequents = [
            self.parse_fact(product, f"{rule_id}_cons_{idx}")
            for idx, product in enumerate(raw_rule["outputs"])
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
