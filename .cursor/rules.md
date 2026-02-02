# Cursor Rules — SignalIQ

These rules define how code must be generated and modified in this repository.
They are non-negotiable and must be followed strictly.

---

- Implement ONLY the current section
- Do NOT touch completed sections
- Do NOT refactor unless required
- MongoDB is the authoritative datastore
- Graph logic must use roads.from → roads.to
- Every decision must be logged with reason
- If scope is unclear, STOP

## 1. Core Development Principles

- Build incrementally. Never generate the full project in one step.
- Every change must result in a working implementation.
- Prefer simple, deterministic logic before AI/ML.
- Do not overengineer or add speculative features.
- Stop and ask for clarification if scope is unclear.

---

## 2. Scope Control

- Implement ONLY the currently active section from README.md.
- Do NOT implement features from future sections.
- Do NOT refactor unrelated code.
- Do NOT introduce new technologies unless explicitly requested.
- Assume this is a prototype, not a production system.

---

## 3. Testing Discipline

- Write high-level tests for every new feature.
- Tests should validate behavior, not internal implementation.
- After implementing a feature:
  1. Write tests
  2. Run tests
  3. Fix failures
  4. Only then commit
- Never skip tests, even for small changes.

---

## 4. Code Structure Rules

- Prefer small files with single responsibility.
- Clear API boundaries between modules.
- Avoid large classes and deeply nested logic.
- No monolithic files.
- Readability > cleverness.

---

## 5. Logging & Debugging

- Add logging for all major actions and decisions.
- Logs should be human-readable and informative.
- Do not silently fail; always log errors clearly.
- Assume logs are the primary debugging tool.

---

## 6. AI / ML Specific Rules

- AI/ML components must be optional and replaceable.
- Always keep a rule-based fallback.
- Models must be behind clean interfaces.
- Never let AI logic crash the system.
- If AI fails, system must degrade gracefully.

---

## 7. Error Handling

- Fail fast and loudly.
- Error messages should be explicit and actionable.
- Do not swallow exceptions.
- If an error occurs, explain what failed and why.

---

## 8. Incremental Workflow (Mandatory)

For each section:

1. Implement only the required features
2. Write high-level tests
3. Run tests
4. Fix issues
5. Commit changes

Never skip steps.

---

## 9. When Stuck

- If a feature becomes complex, build a small standalone prototype first.
- Use reference implementations only for understanding, not direct copying.
- Prefer asking for clarification over guessing.

---

## 10. Goal Reminder

The goal is a clean, understandable, working prototype at every step,
not a fully optimized or production-ready system.
