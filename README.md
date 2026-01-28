# signal_iq
AI Driven Traffic Optimization System



# SignalIQ

SignalIQ is an AI-driven traffic optimization system built incrementally.
This repository follows strict step-by-step development with testing after
each feature and no one-shot generation.



## Development Rules (Must Follow)

- Build incrementally; never generate the full project at once
- Each section must result in a working system
- Write high-level tests before committing
- Prefer simple, deterministic logic first
- AI/ML is optional and added only after rule-based logic works
- Logging is mandatory for every major action
- No overengineering or future features unless explicitly approved



## Section-Wise Development Plan

### Section 0 — Project Skeleton
- [ ] Repo structure
- [ ] FastAPI app setup
- [ ] Health check endpoint
- [ ] Logging setup

### Section 1 — Traffic Data Ingestion
- [ ] POST /traffic/update API
- [ ] Input validation
- [ ] Data persistence
- [ ] Logging

### Section 2 — Traffic State Aggregation
- [ ] Aggregate per intersection
- [ ] In-memory state
- [ ] Deterministic logic

### Section 3 — Congestion Detection (Rule-Based)
- [ ] Threshold-based congestion detection
- [ ] Configurable thresholds
- [ ] Event emission

### Section 4 — Signal Timing Engine
- [ ] Base signal timing
- [ ] Green extension logic
- [ ] Safety limits

### Section 5 — Priority Handling
- [ ] Emergency override
- [ ] Bus priority
- [ ] Priority expiration

### Section 6 — AI Integration (Future)
- [ ] ML congestion prediction
- [ ] Fallback to rule-based logic

### Section 7 — Dashboard (Future)
- [ ] Live intersection view
- [ ] Signal status



## Testing & Debugging Philosophy

- High-level tests are preferred over low-level tests
- Tests should verify behavior, not implementation
- Every feature must be testable in isolation
- Logs are the primary debugging mechanism
- Error messages should be copied directly into the LLM



## Instructions for Coding Assistants

- Implement only the currently selected section
- Do not add features from future sections
- Do not refactor unrelated code
- Keep files small and modular
- If a feature is complex, build a small prototype first
- Stop and ask for clarification if scope is unclear