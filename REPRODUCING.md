# Operation & Reproduction Guide

This document provides step-by-step instructions to set up the environment, run simulations, and reproduce test results within the **Chemical Inference Engine (CIE)** workspace.

---

## 1. System Requirements

- **Runtime**: Python `3.7` or higher (Python `3.10+` is highly recommended for optimal performance).
- **Orchestration Tool**: `make` (Native on macOS/Linux; available on Windows via Git Bash, WSL, or chocolatey).
- **External Dependencies**: None (Zero third-party library dependencies). The project relies entirely on Python's robust Standard Library.

---

## 2. Quick Setup & Validation

**Step 1:** Open your terminal and navigate to the project root directory:
```bash
cd CIE
```

**Step 2:** Verify python compatibility and initialize the environment:
```bash
make setup
```

---

## 3. Running Integration & Reproduction Simulations

CIE includes pre-configured testing targets managed by the `Makefile` for instant execution and verification:

### 3.1. Scenario 1: NaOH Synthesis (Single-Step Inference)
- **Goal:** Verify the execution of a basic single-step reaction (`Na + H2O -> NaOH + H2`).
- **Command:**
  ```bash
  make run
  ```
- **Description:** Loads the knowledge base, matches rule `r1`, updates Working Memory, and displays the synthesized outputs and paths.

### 3.2. Scenario 2: NaCl Synthesis (Multi-Step Inference Chain)
- **Goal:** Verify multi-step rule chaining and resolution.
- **Command:**
  ```bash
  make test
  ```
- **Description:** Fires `r1` to synthesize intermediate `NaOH`, then triggers `r3` (`NaOH + HCl -> NaCl + H2O`) to yield the target product `NaCl`. Path resolved: `r1 -> r3`.

### 3.3. Scenario 3: Custom Exploratory & Targeted Simulations
Execute tailored scenarios by feeding custom inputs through `FACTS` and `GOAL` arguments inside the Makefile.

- **Exploratory Run (Deduce all possible chemical compounds from given reactants):**
  ```bash
  make run-custom FACTS="NaCl H2O NH3 CO2"
  ```

- **Targeted Run (Validate path feasibility for a specific target compound):**
  ```bash
  make run-custom FACTS="NaHCO3" GOAL="Na2CO3"
  ```

---

## 4. Workspace Housekeeping

To purge cached Python bytecode (`__pycache__`) and restore the workspace to a pristine state:
```bash
make clean
```
