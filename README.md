# Chemical Inference Engine (CIE)

CIE is a high-performance Symbolic AI Inference Engine designed to automate chemical synthesis pathway discovery and reaction routing. The system implements an optimized **Forward Chaining** algorithm over a **Rule-Based Expert System**, replacing legacy bitset parser architectures with modern set-theoretic operations for production-grade robustness.

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Aesthetics](https://img.shields.io/badge/design-professional-brightgreen.svg)]()

---

## 1. Core Features

- **O(1) Fact Matching:** Leverages set-theory mathematics (`Set subset evaluation`) for the Match Phase instead of linear array traversal, reducing runtime complexity to a minimum.
- **Dynamic Knowledge Base (KB):** Decoupled JSON-based rule storage allowing hot-reloads of reaction rules without source code modification or compilation.
- **Goal-Directed Early Stopping:** Automatically terminates inference as soon as the target compound (Goal) is synthesized, optimizing compute resources.
- **Zero-Dependency Architecture:** Written entirely in pure Python (Standard Library only), ensuring maximum portability across diverse execution runtimes (Cloud, Edge, Containers).
- **Developer-Friendly Interface:** Out-of-the-box support for a clean Command Line Interface (CLI) and automated execution orchestration via `Makefile`.

---

## 2. System Architecture

CIE is structured using a clean, decoupled architecture:

```mermaid
graph TD
    A[User Inputs: Facts & Goal] -->|CLI / Makefile| B(Inference Engine)
    C[knowledge_base.json] -->|Dynamic Load| B
    B -->|Match-Resolve-Act Loop| D{Working Memory}
    D -->|O(1) Subset Check| E[Rule Repository]
    E -->|Fired Rule| D
    D -->|Goal Reached / Saturation| F[Execution Summary & Reaction Path]
```

- **Knowledge Base:** Defines the collection of chemical reactions (production rules) at [src/knowledge_base.json](file:///Users/KhangDS/Programing/HCMUS_Code/Knowledge_Reprensentation_code/Knowledge_Rep_Playground_code/src/knowledge_base.json).
- **Inference Engine:** Handles the main execution and logic at [src/engine.py](file:///Users/KhangDS/Programing/HCMUS_Code/Knowledge_Reprensentation_code/Knowledge_Rep_Playground_code/src/engine.py), utilizing modular `Rule` and `InferenceEngine` abstractions.
- **CLI Entrypoint:** Provides clean parsing, logging, and user feedback at [src/main.py](file:///Users/KhangDS/Programing/HCMUS_Code/Knowledge_Reprensentation_code/Knowledge_Rep_Playground_code/src/main.py).

---

## 3. Theoretical Mapping to Implementation

| Expert System Concept | CIE Implementation | Technical Role / Mechanism |
| :--- | :--- | :--- |
| **Production Rules** | [src/knowledge_base.json](file:///Users/KhangDS/Programing/HCMUS_Code/Knowledge_Reprensentation_code/Knowledge_Rep_Playground_code/src/knowledge_base.json) | Declares reactions in format: $A + B \rightarrow C + D$. Instantiated as `Rule` objects with `inputs` (antecedents) and `outputs` (consequents). |
| **Working Memory** | `known_facts: Set[str]` | An in-memory temporary store representing confirmed facts. Initialized with starting reactants (`--facts`) and updated via `.update()` when rules fire. |
| **Conflict Resolution** | `applied_rules: List[str]` | Records fired rule IDs to ensure each chemical reaction rule is executed at most once, preventing infinite deduction loops. |
| **Match Phase** | `rule.inputs.issubset(known_facts)` | Extremely fast, set-based matching check. Fires the reaction rules immediately when all required antecedents exist in Working Memory. |

---

## 4. Quick Start

Manage and run simulations effortlessly using the provided `Makefile`:

```bash
# Verify environment compatibility
make setup

# Run default single-step synthesis (Na + H2O -> NaOH)
make run

# Run multi-step chain synthesis (Na + H2O + HCl -> NaCl)
make test
```

*For custom simulations and detailed run instructions, refer to the [REPRODUCING.md](file:///Users/KhangDS/Programing/HCMUS_Code/Knowledge_Reprensentation_code/Knowledge_Rep_Playground_code/REPRODUCING.md) guide.*
