import time
from typing import List, Set, Optional
from core_engine.models import Fact, Rule, ExecutionStep, InferenceResult

class ForwardChainingEngine:
    """
    Domain-agnostic forward-chaining logical solver.
    Matches antecedents iteratively to facts inside Working Memory until saturation or goal completion.
    """
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def solve(self, initial_facts: List[Fact], goal: Optional[Fact] = None) -> InferenceResult:
        working_memory: Set[Fact] = set(initial_facts)
        applied_rule_ids: List[str] = []
        execution_trace: List[ExecutionStep] = []

        # Early termination guard
        if goal and goal in working_memory:
            return InferenceResult(
                goal_reached=True,
                final_facts=list(working_memory),
                execution_trace=execution_trace,
                applied_rule_ids=applied_rule_ids
            )

        new_facts_inferred = True
        while new_facts_inferred:
            new_facts_inferred = False
            for rule in self.rules:
                if rule.id not in applied_rule_ids:
                    # Match Phase: Check if all antecedents are present in Working Memory
                    if set(rule.antecedents).issubset(working_memory):
                        # Act Phase: Fire rule and record new inferred facts
                        new_inferred = [f for f in rule.consequents if f not in working_memory]
                        working_memory.update(rule.consequents)
                        applied_rule_ids.append(rule.id)

                        execution_trace.append(ExecutionStep(
                            rule_id=rule.id,
                            fired_rule_repr=repr(rule),
                            new_facts=new_inferred,
                            timestamp_ms=time.time() * 1000
                        ))
                        new_facts_inferred = True

                        # Goal evaluation
                        if goal and goal in working_memory:
                            return InferenceResult(
                                goal_reached=True,
                                final_facts=list(working_memory),
                                execution_trace=execution_trace,
                                applied_rule_ids=applied_rule_ids
                            )

        return InferenceResult(
            goal_reached=False if goal else None,
            final_facts=list(working_memory),
            execution_trace=execution_trace,
            applied_rule_ids=applied_rule_ids
        )


class BackwardChainingEngine:
    """
    Domain-agnostic backward-chaining logical solver.
    Starts with a goal fact, recursively resolves subgoals using rule outcomes,
    and constructs an explainable inference path.
    """
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def solve(self, initial_facts: List[Fact], goal: Fact) -> InferenceResult:
        working_memory: Set[Fact] = set(initial_facts)
        applied_rule_ids: List[str] = []
        execution_trace: List[ExecutionStep] = []
        visited_subgoals: Set[Fact] = set()

        def prove(subgoal: Fact) -> bool:
            # Base Case 1: Subgoal is already a confirmed fact
            if subgoal in working_memory:
                return True
            # Base Case 2: Subgoal is already being evaluated (preventing circular reference loops)
            if subgoal in visited_subgoals:
                return False

            visited_subgoals.add(subgoal)

            # Find all rules that can produce the target subgoal in their consequents
            candidate_rules = [r for r in self.rules if subgoal in r.consequents]

            for rule in candidate_rules:
                # Recurse: Attempt to prove all antecedents of the rule
                all_antecedents_proven = True
                for antecedent in rule.antecedents:
                    if not prove(antecedent):
                        all_antecedents_proven = False
                        break

                if all_antecedents_proven:
                    # Fire Rule: Add all outputs of the rule to Working Memory
                    new_inferred = [f for f in rule.consequents if f not in working_memory]
                    working_memory.update(rule.consequents)

                    if rule.id not in applied_rule_ids:
                        applied_rule_ids.append(rule.id)
                        execution_trace.append(ExecutionStep(
                            rule_id=rule.id,
                            fired_rule_repr=repr(rule),
                            new_facts=new_inferred,
                            timestamp_ms=time.time() * 1000
                        ))
                    visited_subgoals.remove(subgoal)
                    return True

            visited_subgoals.remove(subgoal)
            return False

        goal_reached = prove(goal)
        return InferenceResult(
            goal_reached=goal_reached,
            final_facts=list(working_memory),
            execution_trace=execution_trace,
            applied_rule_ids=applied_rule_ids
        )
