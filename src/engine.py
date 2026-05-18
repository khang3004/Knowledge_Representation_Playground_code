import json
from typing import List, Set, Dict, Any, Optional

class Rule:
    """
    Represents a chemical reaction rule within the Knowledge Base.
    Maps a set of antecedent facts (reactants) to a set of consequent facts (products).
    """
    def __init__(self, rule_id: str, inputs: List[str], outputs: List[str]):
        """
        Initializes a chemical reaction rule.

        Args:
            rule_id (str): Unique identifier for the rule (e.g., 'r1').
            inputs (List[str]): List of reactant chemicals (antecedents).
            outputs (List[str]): List of product chemicals (consequents).
        """
        self.rule_id = rule_id
        self.inputs = set(inputs)
        self.outputs = set(outputs)

    def __repr__(self) -> str:
        return f"Rule({self.rule_id}: {' + '.join(self.inputs)} -> {' + '.join(self.outputs)})"


class InferenceEngine:
    """
    Production-grade Inference Engine implementing the Forward Chaining algorithm
    over a Rule-Based Expert System for Chemical Equations.
    """
    def __init__(self, knowledge_base_path: str):
        """
        Initializes the Inference Engine by loading rules from a JSON Knowledge Base.

        Args:
            knowledge_base_path (str): File path to the knowledge base JSON.
        """
        self.rules: List[Rule] = []
        self._load_knowledge_base(knowledge_base_path)

    def _load_knowledge_base(self, path: str) -> None:
        """
        Parses and loads the rules from the JSON configuration.

        Args:
            path (str): File path to the knowledge base JSON.
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                rule = Rule(
                    rule_id=item['id'],
                    inputs=item['inputs'],
                    outputs=item['outputs']
                )
                self.rules.append(rule)

    def forward_chaining(self, initial_facts: List[str], goal: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the Forward Chaining deduction algorithm.
        Starts with a set of initial facts (working memory) and iteratively applies matching rules.

        Args:
            initial_facts (List[str]): Starting set of confirmed facts (reactants).
            goal (Optional[str]): Target fact (chemical product) to deduce. Defaults to None.

        Returns:
            Dict[str, Any]: Execution summary containing:
                - "goal_reached": bool (or None if no goal specified)
                - "known_facts": List of all deduced and initial facts
                - "path": List of rule IDs triggered during deduction in sequence
        """
        # Working Memory representing currently known facts
        known_facts: Set[str] = set(initial_facts)
        applied_rules: List[str] = []
        
        new_facts_inferred = True
        goal_reached = False
        
        # Guard check: Goal is already present in the initial fact set
        if goal and goal in known_facts:
            return {
                "goal_reached": True,
                "known_facts": list(known_facts),
                "path": applied_rules
            }

        # Main Forward Chaining loop
        while new_facts_inferred:
            new_facts_inferred = False
            
            for rule in self.rules:
                # Match Phase: Check if rule is unapplied and all antecedents are present in Working Memory
                if rule.rule_id not in applied_rules and rule.inputs.issubset(known_facts):
                    # Conflict Resolution & Action Phase: Fire the rule, update Working Memory
                    known_facts.update(rule.outputs)
                    applied_rules.append(rule.rule_id)
                    new_facts_inferred = True
                    
                    # Goal Check Phase
                    if goal and goal in known_facts:
                        goal_reached = True
                        break
            
            if goal_reached:
                break
                
        return {
            "goal_reached": goal_reached if goal else None,
            "known_facts": list(known_facts),
            "path": applied_rules
        }
