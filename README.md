# SignalIQ

AI-Driven Traffic Optimization System

SignalIQ is an incremental, rule-first traffic optimization backend that models
a city as a graph of connected intersections and roads, optimizes signal timings
using real-time traffic data, and supports emergency vehicle prioritization.

The system is designed to be:

- Deterministic first, intelligent later
- Explainable and testable
- Safe against congestion spillback
- Incrementally extensible

---

## Development Rules (Must Follow)

- Build incrementally; never generate the full project at once
- Each section must result in a working system
- Do not touch completed sections unless explicitly required
- Prefer simple, deterministic logic first
- AI/ML is optional and added only after rule-based logic is stable
- Logging is mandatory for every major action
- No speculative features or overengineering
- MongoDB is the authoritative datastore

---

## Tech Stack

- Backend: FastAPI
- Database: MongoDB
- Architecture: Decentralized, graph-based intersections
- Signal logic: Rule-based (AI optional later)

---

## Section-Wise Backend Development Plan

### Section 0 — Project Skeleton ✅

- Repo structure
- FastAPI app setup
- Health check endpoint
- Logging setup

---

### Section 1 — Traffic Data Ingestion ✅

- POST `/traffic/update`
- Input validation
- Data persistence
- Logging

---

### Section 2 — Traffic State Aggregation ✅

- Aggregate traffic data
- In-memory state
- Deterministic logic

---

### Section 3 — Congestion Detection (Rule-Based) ✅

- Threshold-based congestion detection
- Configurable thresholds
- Event logging

---

### Section 4 — Signal Timing Engine (Local) ✅

- Base signal timing
- Green extension logic
- Safety limits
- Starvation prevention

---

### Section 5 — City Topology & Graph Modeling

**Goal:** Represent the city as a directed graph

- `intersections` collection (junction metadata)
- `roads` collection (directed edges)
- Road → intersection connectivity via `from` and `to`
- Dummy city graph seed (e.g., 3×3 grid)
- Utilities:
  - get incoming roads
  - get outgoing roads
- Read-only topology APIs

_No traffic logic or signal logic in this section_

---

### Section 6 — Road-Level Real-Time Traffic State

**Goal:** Attach live traffic to roads

- `traffic_state` collection (per road)
- POST `/traffic/update` (road-scoped)
- GET `/traffic/road/{road_id}`
- Timestamp freshness validation
- Logging for every update

_No aggregation or optimization yet_

---

### Section 7 — Intersection State Aggregation

**Goal:** Local intersection awareness

- Aggregate incoming road traffic per intersection
- Compute:
  - total queue
  - average wait
  - load score
- GET `/traffic/intersection/{id}/snapshot`
- Structured logs

_No signal decisions yet_

---

### Section 8 — Congestion Detection (Graph-Aware)

**Goal:** Detect and prevent spillback congestion

- Road congestion score (queue / capacity)
- Intersection congestion level (LOW / MED / HIGH)
- One-hop downstream congestion lookup
- Penalize blocked downstream paths
- GET `/traffic/congestion/{intersection_id}`

_Rule-based only, fully explainable_

---

### Section 9 — Signal Timing Engine (Graph-Safe)

**Goal:** Safe, local optimization

- Signal phase definitions (NS, EW, turns)
- Priority scoring per phase:
  - queue pressure
  - waiting time
  - downstream clearance
- Starvation prevention
- Safety caps on green duration
- `signal_state` collection
- GET `/signal/{intersection_id}`

_No emergency handling yet_

---

# Section 10 — Multi-Intersection Signal Coordination (Green-Wave Engine)

## Goal

Section 10 introduces **multi-intersection coordination** to SignalIQ, enabling upstream traffic signals to adapt their active signal axis based on downstream congestion and blockage. This prevents spillback, improves traffic flow continuity, and makes the system behavior realistic and city-scale.

- This section builds on **Sections 7–9**
- Does **not modify the frontend contract**

---

## Motivation

### Without coordination

- Each intersection operates independently
- Congestion propagates upstream
- Vehicles stop frequently, causing spillback and gridlock

### With coordination

- Upstream intersections react to downstream conditions
- Green waves form naturally
- Spillback is prevented
- Signal behavior becomes explainable and realistic

---

## Design Principles

- Backend-only logic (frontend remains passive)
- Deterministic and graph-safe
- No timers, no background loops
- No frontend inference
- No database persistence
- No API contract changes
- Backend remains the single source of truth

---

## Inputs Used

Section 10 reuses existing backend components:

- Topology graph (Section 1)
- Intersection aggregation (Section 7)
- Congestion detection, including `downstream_blocked` (Section 8)
- Local signal timing and phase state (Section 9)

---

## Coordination Logic (Ordered Rules)

### Rule 1 — Downstream Block Dominance (Highest Priority)

If **any downstream intersection** is marked as `downstream_blocked = true`,  
the upstream intersection **inherits the downstream intersection’s `active_axis`**.

**Purpose:** Prevent spillback and gridlock.

---

### Rule 2 — Green-Wave Alignment

If a downstream intersection:

- Is directly connected
- Has an active signal axis (`X` or `Z`)
- And the road from the current intersection feeds that axis

Then **align the upstream intersection’s `active_axis`** to match.

**Purpose:** Enable smooth vehicle platoons across multiple intersections.

---

### Rule 3 — Local Default (Fallback)

If no coordination rule applies, retain the **local `active_axis`** computed in Section 9.

---

## Phase Stability Rules

- `active_axis` must not toggle automatically
- Phase must persist across requests
- Coordination may override phase **only when rules apply**
- Otherwise, the phase remains unchanged

---

### Logging

[SignalCoordination]
intersection=I11
reason=DOWNSTREAM_BLOCKED
inherited_from=I12
active_axis=X

## API Contract (Unchanged)

### Endpoint

- GET /traffic/signal/{intersection_id}

### Response

```json
{
  "intersection_id": "I11",
  "active_axis": "X",
  "green_time": 15,
  "red_time": 75,
  "level": "HIGH",
  "downstream_blocked": true
}

---



### Section 11 — Emergency Vehicle Priority (Green Corridor)

**Goal:** Realistic emergency handling

- `emergency_vehicles` collection
- Emergency registration API
- Shortest-path routing using road graph
- Temporary signal overrides along route
- Conflict locking
- Automatic override expiry
- Full audit logging

_Normal optimization resumes automatically_

---

### Section 12 — Observability & Safety Guarantees

**Goal:** Make the system judge-safe and debuggable

- Structured decision logs
- Invariant checks (no conflicting greens)
- Fail-safe fallback to base timings
- Health & diagnostics endpoints

---

### Section 13 — AI / ML Integration (Optional)

**Goal:** Predictive assistance only

- Congestion prediction
- Timing recommendations
- ML suggestions never override rule engine
- Hard fallback to deterministic logic

---

## Testing & Debugging Philosophy

- High-level behavior tests over low-level unit tests
- Tests verify outcomes, not implementation details
- Each section must be testable in isolation
- Logs are the primary debugging mechanism
- Error messages should be copied verbatim into the LLM

---

## Instructions for Coding Assistants (Cursor / LLMs)

- Implement ONLY the current section
- Do NOT add features from future sections
- Do NOT refactor unrelated code
- Keep files small and modular
- MongoDB is the source of truth
- Graph logic must use `roads.from → roads.to`
- Every decision must be logged with a reason
- If scope is unclear, STOP and ask
```
