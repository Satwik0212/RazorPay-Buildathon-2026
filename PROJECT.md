# Project: Razorpay AI Commerce Platform Optimization Engine - Step 3 Full Active Catalogue Retrieval

## Architecture
- Database (PostgreSQL) -> ProductRepository.get_active_catalogue_for_merchant(merchant_id)
- ProductService.get_active_catalogue(merchant_id)
- Simulation / What-If Endpoints:
  1. Fetch full active catalogue (~2,977 active products)
  2. Full in-memory candidate simulation over all active products (Hard Constraints -> Soft Friction -> Metadata Normalization -> Deterministic Scoring -> Deterministic Tie-breaking)
  3. Winner selection, summary metrics calculation, recommendation evidence aggregation (all over 100% full active catalogue)
  4. Truncate rankings representation ONLY for serialization/persistence (top 20 passed + top 10 disqualified + winner preservation if absent)
  5. Lean persistence in simulation_results and lean API response payload

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Full Active Catalogue Retrieval Query | Query merchant's active products in ProductRepository without artificial limits/embeddings/caps, preserving inventory & metadata | M1 | ORIGINAL_REQUEST § R1 |
| 2 | Inventory Semantics Preservation | Inspect existing missing inventory row handling & preserve exact application contract without fabricating default quantities | M1 | ORIGINAL_REQUEST § R1 |
| 3 | Merchant Isolation Enforcement | Filter strictly by Product.merchant_id == authenticated_merchant_id; cross-merchant products never enter candidate pool | M1 | ORIGINAL_REQUEST § R1 |
| 4 | Full In-Memory Simulation Evaluation | Pass all retrieved active products (~2,977) to SimulationEngine.evaluate_scenario | M2 | ORIGINAL_REQUEST § R2 |
| 5 | What-If Full Catalogue Evaluation | Update What-If simulation path to evaluate full active catalogue identically across baseline and proposed | M2 | ORIGINAL_REQUEST § R2 |
| 6 | Lean Ranking Serialization Truncation | Truncate rankings to at most top 20 passed + top 10 disqualified + winner preserved, strictly AFTER winner/summary/recommendations computed | M2 | ORIGINAL_REQUEST § R2 |
| 7 | Persistence Integrity & Lean Invariant | Ensure simulation_results persists lean rankings without losing decision summary fields, winner identity, or recommendation evidence | M2 | ORIGINAL_REQUEST § R3 |
| 8 | Recommendation Evidence Completeness | Ensure RecommendationService sees all friction events and out-of-stock products computed from full active catalogue | M2 | ORIGINAL_REQUEST § R3 |
| 9 | Live DB Performance Benchmarks | Measure active PostgreSQL performance across DB retrieval, mapping, simulation, recommendation, serialization, and payload sizes | M3 | ORIGINAL_REQUEST § R4 |
| 10 | Adversarial Inspection & Verification | 24-point adversarial review verifying inventory authenticity, no N+1, no semantic regression, Step 1/2 preservation | M4 | ORIGINAL_REQUEST § R5 |
| 11 | Victory Audit & Scorecard | 30-point Victory Auditor checklist and 20-section Final Consolidated Report | M5 | ORIGINAL_REQUEST § VICTORY AUDITOR |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Survey & Architecture Investigation | Survey repo, inspect inventory semantics, existing query, simulation flow, persistence schema | none | IN_PROGRESS |
| M1 | Full Active Catalogue Retrieval (R1) | Implement ProductRepository & ProductService retrieval methods with strict merchant isolation and inventory semantics | M0 | PLANNED |
| M2 | Simulation Pipeline & Lean Truncation (R2 & R3) | Integrate full catalogue in simulation & What-If; implement post-computation lean ranking truncation; verify persistence | M1 | PLANNED |
| M3 | Performance Benchmarks & Measurements (R4) | Live PostgreSQL benchmark for retrieval, simulation, serialization, latency, and payload sizes | M2 | PLANNED |
| M4 | Adversarial Review & 24-Point Inspection (R5) | Independent adversarial test & inspection across all 24 points | M3 | PLANNED |
| M5 | Victory Auditor & Final Consolidated Report | Complete 30-point audit verification checklist, Before/After scorecard, and 20-section final report | M4 | PLANNED |

## Interface Contracts
### ProductRepository ↔ ProductService
- `get_active_catalogue_for_merchant(db: Session, merchant_id: UUID) -> List[Product] | List[Dict]`
- Returns all active products with inventory available_quantity and metadata preserved.

### ProductService ↔ Simulation / What-If
- `get_active_catalogue(db: Session, merchant_id: UUID) -> List[Product]` or simulation-ready candidate list.

### SimulationEngine ↔ Serialization / Persistence
- Internal evaluation returns full `SimulationResult` or candidates with full summary/winner/friction data.
- Lean truncation applies to `rankings`: top 20 passed + top 10 disqualified (+ selected winner if not already present).

## Code Layout
- `backend/app/repositories/product_repository.py` - Product repository data access
- `backend/app/services/product_service.py` - Product service business logic
- `backend/app/api/v1/optimization/simulations.py` - Simulation endpoint & ranking truncation
- `backend/app/api/v1/optimization/what_if.py` - What-If endpoint full catalogue integration
- `backend/app/simulation/engine.py` - Simulation engine & ranking logic
- `backend/app/services/recommendation_service.py` - Recommendation engine
- `backend/tests/` - Automated test suite
