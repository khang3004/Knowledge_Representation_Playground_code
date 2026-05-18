# Contribution Guidelines

Welcome to the **Chemical Inference Engine (CIE)** contribution guide. This document establishes standard workflows, strict code metrics, and data structures required to maintain clean and reliable development practices.

---

## 1. Git Workflow

We adopt a clean, branch-based feature workflow:

1. **Fork** the official repository.
2. Create a new isolated feature branch off of the `main` branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Implement engineering updates exclusively within the `/src` directory.
4. Ensure commit messages follow the **Conventional Commits** standard:
   - `feat(engine):`: Implement a new inference engine enhancement.
   - `fix(cli):`: Resolve CLI argument parsing or formatting issues.
   - `docs(readme):`: Refine README or technical specifications.
5. Push the feature branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
6. Open a **Pull Request (PR)** targeting the upstream `main` branch, explaining the changes and attaching execution logs.

---

## 2. Coding Standards

To ensure long-term codebase health, readability, and maintainability:

- **Unified Language:** The entire codebase—including class/variable names, technical docstrings, code comments, system logs, and documentation—must be written in **professional English**.
- **Formatting Standards:** Strictly adhere to the **PEP 8** style guide. Run auto-formatters like `black` or linters like `flake8` before submitting commits.
- **Type Annotations:** All functions and methods must declare explicit, static type annotations utilizing Python's `typing` module. Avoid using raw `Any` type annotations where possible.
  ```python
  def execute_inference(self, initial_facts: Set[str]) -> List[str]:
  ```
- **Documentation Standards:** Format all docstrings using the **Google Python Style Guide** to facilitate automated document generation.

---

## 3. Extending the Knowledge Base (KB)

To expand chemical reaction rules within [src/knowledge_base.json](file:///Users/KhangDS/Programing/HCMUS_Code/Knowledge_Reprensentation_code/Knowledge_Rep_Playground_code/src/knowledge_base.json), strictly follow this JSON layout:

```json
{
  "id": "rXX",
  "inputs": ["ReactantA", "ReactantB"],
  "outputs": ["ProductC", "ProductD"]
}
```

- Names of compounds and elements are case-sensitive and must conform to exact chemical formulas (e.g., use `H2O` instead of `h2o` or `H2o`).
- Ensure all new rules describe chemically logical reactions and do not introduce logical inconsistencies or infinite matching loops within the system.
