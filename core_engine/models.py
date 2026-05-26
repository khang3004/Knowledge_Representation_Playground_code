from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Fact(BaseModel):
    """
    Strictly-typed schema representing a single logical assertion or concept.
    """
    id: str = Field(..., description="Unique identifier for the fact")
    value: str = Field(..., description="Raw string value of the assertion, e.g., 'H2O' or 'Congruent(AB, CD)'")
    domain: str = Field(..., description="Logical domain name, e.g., 'chemistry', 'geometry', 'algebra'")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary for domain-specific attributes")

    def __hash__(self) -> int:
        # Standardizing hash for unique set inclusion in Working Memory (based on semantic content)
        return hash((self.value, self.domain))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Fact):
            return False
        return self.value == other.value and self.domain == other.domain


class Rule(BaseModel):
    """
    Strictly-typed schema representing a symbolic production rule (antecedents -> consequents).
    """
    id: str = Field(..., description="Unique rule identifier, e.g., 'r_substitute'")
    name: str = Field(..., description="Human-readable rule name, e.g., 'Substitution Property'")
    domain: str = Field(..., description="Logical domain name")
    antecedents: List[Fact] = Field(..., description="Reactants or preconditions required for the rule to fire")
    consequents: List[Fact] = Field(..., description="Products or conclusions generated when the rule fires")
    description: Optional[str] = Field(None, description="Detailed explanation of the rule for RAG and UX purposes")

    def __repr__(self) -> str:
        ants = " + ".join([f.value for f in self.antecedents])
        cons = " + ".join([f.value for f in self.consequents])
        return f"{self.id} [{self.name}]: {ants} -> {cons}"


class ExecutionStep(BaseModel):
    """
    Records an individual execution step of the logic solver for post-hoc Explainability.
    """
    rule_id: str = Field(..., description="ID of the fired rule")
    fired_rule_repr: str = Field(..., description="String representation of the fired rule")
    new_facts: List[Fact] = Field(..., description="Facts added to Working Memory by this step")
    timestamp_ms: float = Field(..., description="Timestamp of when the rule was fired")


class InferenceResult(BaseModel):
    """
    Comprehensive execution summary of the solver execution.
    """
    goal_reached: Optional[bool] = Field(None, description="True if goal is satisfied, False if not, None if no goal set")
    final_facts: List[Fact] = Field(..., description="Final state of the working memory facts")
    execution_trace: List[ExecutionStep] = Field(..., description="Sequenced path of rule activations")
    applied_rule_ids: List[str] = Field(..., description="Sequenced list of triggered rule IDs")
