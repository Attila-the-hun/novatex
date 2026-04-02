# NovateX — Product Roadmap

**Product:** NovateX — Novated Lease Soft Contract Platform
**Status:** Pre-build (Architecture & Research Complete)
**Start Date:** TBD
**Target MVP:** ~5-6 months from start
**Owner:** Tim Messieh / Newport Pembury & Co

---

## Vision

A multi-party automated financial agreement platform for Australian novated leases, replacing PDF forms, email chains, and spreadsheet reconciliation with cryptographically signed event ledgers, automated obligation tracking, and real-time payroll integration.

**Market:** ~400,000 active novated leases in Australia. AUD 6-8B annual origination. 15-25% YoY growth driven by EV FBT exemption. Incumbents (MMS/Maxxia, SG Fleet) running 1990s technology with call-centre operations.

**Architecture Decision:** Signed event ledger + Ricardian contract templates. NOT blockchain. Corda evaluated and rejected — known parties under Australian law don't need Byzantine fault tolerance. ASX CHESS failure (A$250M write-off) makes DLT a credibility risk in AU financial services.

---

## Phase 0: Contract Kernel (Weeks 1-6)

The foundation. YAML contract templates, Pydantic models, state machine, and signed event ledger.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 0.1 | Define YAML contract template schema (parties, vehicle, terms, FBT, running costs, obligations) | 1 week | None | Not started |
| 0.2 | Pydantic models — NovatedLease, Vehicle, LeaseTerms, FBTConfig, RunningCostPool, Party | 1 week | 0.1 | Not started |
| 0.3 | State machine engine — DRAFT → ACTIVE → RECONCILIATION → MATURITY/TERMINATION with guard conditions | 1 week | 0.2 | Not started |
| 0.4 | Signed event ledger — append-only PostgreSQL log, Ed25519 signatures per event, Merkle tree chain | 1.5 weeks | 0.2 | Not started |
| 0.5 | Contract template parser — load YAML, validate against schema, bind to legal document hash | 0.5 weeks | 0.1, 0.2 | Not started |
| 0.6 | Obligation engine v1 — track deadlines per party, flag overdue, emit escalation events | 1 week | 0.3, 0.4 | Not started |
| 0.7 | Unit test suite — state machine transitions, event signing/verification, obligation triggers | Throughout | All | Not started |
| 0.8 | ATO residual value table — minimum residual percentages by lease term (12-60 months) | 0.5 weeks | None | Not started |

**Phase 0 Exit Criteria:** Can instantiate a novated lease from YAML, transition through lifecycle states, log signed events, and track obligations with deadlines.

---

## Phase 1: Single Lease Demo (Weeks 7-10)

One real novated lease with real numbers. Manual payroll (no API yet). Employee-facing portal.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 1.1 | Seed data — one real or realistic novated lease (EV, 36-month, ECM) | 0.5 weeks | Phase 0 | Not started |
| 1.2 | Employee portal v1 — deduction breakdown, running cost balance, FBT impact, residual countdown | 2 weeks | 1.1 | Not started |
| 1.3 | Manual payroll cycle flow — HR enters deduction confirmation, system logs event | 1 week | 0.4 | Not started |
| 1.4 | Running cost claim submission — receipt upload, category selection, budget check | 1 week | 0.6 | Not started |
| 1.5 | Tamper evidence demo — show Merkle tree verification, demonstrate event chain integrity | 0.5 weeks | 0.4 | Not started |

**Phase 1 Exit Criteria:** A single lease visible in a portal, with manual payroll cycles logged, running cost claims submitted, and tamper-evident event history browsable.

---

## Phase 2: Payroll Integration (Weeks 11-14)

Automated salary sacrifice deductions via Xero API. MYOB as second integration.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 2.1 | Xero payroll API adapter — OAuth2, poll pay runs, match to active leases | 1.5 weeks | Phase 1 | Not started |
| 2.2 | Deduction engine — calculate pre-tax/post-tax split, handle leave proration | 1 week | 0.2 | Not started |
| 2.3 | Remittance tracking — employer→financier payment confirmation, reconciliation | 1 week | 0.4, 2.1 | Not started |
| 2.4 | MYOB payroll API adapter (same interface, different backend) | 1 week | 2.1 | Not started |
| 2.5 | Payroll adapter abstraction — clean interface for future payroll systems (KeyPay, etc.) | 0.5 weeks | 2.1, 2.4 | Not started |

**Phase 2 Exit Criteria:** Payroll deductions automatically detected from Xero, matched to leases, events logged, remittance tracked. MYOB supported as second adapter.

---

## Phase 3: Running Cost Management (Weeks 15-17)

Full running cost lifecycle — claims, approvals, budget tracking, surplus/deficit calculation.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 3.1 | Running cost pool engine — monthly budget allocation, category breakdown (fuel, insurance, rego, tyres, maintenance, roadside) | 1 week | 0.2 | Not started |
| 3.2 | Claim workflow — submit, auto-validate against budget, approve/reject, reimburse | 1 week | 1.4, 3.1 | Not started |
| 3.3 | Receipt handling — SHA-256 content-addressed storage (S3), hash logged in event ledger | 0.5 weeks | 0.4 | Not started |
| 3.4 | Budget forecast — project surplus/deficit at lease end based on burn rate | 0.5 weeks | 3.1 | Not started |
| 3.5 | EV running cost profile — charging costs, reduced maintenance schedule, no fuel category | 0.5 weeks | 3.1 | Not started |
| 3.6 | Fleet manager portal v1 — claim queue, budget overview, vendor payment status | 1 week | 3.2 | Not started |

**Phase 3 Exit Criteria:** Running costs managed end-to-end. Employee submits receipt → auto-validated → reimbursed → event logged. Budget surplus/deficit projected.

---

## Phase 4: FBT Engine (Weeks 18-21)

Full Australian FBT calculation — statutory formula, operating cost method, ECM, STP2 output.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 4.1 | Statutory formula calculator — 20% × base value, ECM post-tax contribution to zero FBT | 1 week | 0.2 | Not started |
| 4.2 | Operating cost method — logbook input, odometer tracking, private-use % calculation | 1 week | 4.1 | Not started |
| 4.3 | EV FBT exemption logic — vehicle type check, LCT threshold validation, zero-rate application | 0.5 weeks | 4.1 | Not started |
| 4.4 | Annual reconciliation workflow — odometer collection (deadline Mar 15), FBT calc, ECM shortfall detection | 1 week | 4.1, 4.2, 0.6 | Not started |
| 4.5 | STP Phase 2 output — salary sacrifice amounts, reportable fringe benefits in ATO-compliant format | 1 week | 4.4, 2.1 | Not started |
| 4.6 | FBT year-end report — per-employee breakdown, employer aggregate, ATO submission-ready | 0.5 weeks | 4.4, 4.5 | Not started |

**Phase 4 Exit Criteria:** Both FBT methods calculated correctly. Annual reconciliation automated. STP2-compliant output generated. EV exemption handled.

---

## Phase 5: Multi-Party Portals (Weeks 22-25)

Role-based views for all four parties. Each sees only what they should.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 5.1 | Employer/HR dashboard — active leases, FBT exposure, fleet composition, compliance status, payroll integration health | 1.5 weeks | Phase 2, 4 | Not started |
| 5.2 | Financier portal — payment receipts, asset status, portfolio overview, residual schedule | 1 week | Phase 2 | Not started |
| 5.3 | Employee portal v2 — upgrade with FBT impact calculator, "what-if" scenarios (method comparison), residual planning | 1 week | 1.2, Phase 4 | Not started |
| 5.4 | Role-based access control — party-specific data visibility, API-level enforcement | 0.5 weeks | All portals | Not started |
| 5.5 | Notification system — email/SMS for obligations, escalations, deadlines | 0.5 weeks | 0.6 | Not started |

**Phase 5 Exit Criteria:** All four party types have dedicated portals with appropriate data visibility. Notifications working for obligation deadlines.

---

## Phase 6: Obligation Engine v2 + Multi-Party Workflows (Weeks 26-27)

Advanced coordination — novation transfers, termination, maturity handling.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 6.1 | Novation transfer workflow — 3-of-3 consent protocol (employee + new employer + financier), atomic execution | 1 week | 0.3, 5.4 | Not started |
| 6.2 | Employment termination flow — novation unwind, lease reversion to personal, final deduction | 0.5 weeks | 0.3, 2.1 | Not started |
| 6.3 | Lease maturity handling — residual payment, trade-in valuation (Redbook API), re-lease option | 0.5 weeks | 0.3, 0.8 | Not started |
| 6.4 | Total loss / insurance event — gap insurance coordination, payout calculation, running cost settlement | 0.5 weeks | 0.3, 3.1 | Not started |
| 6.5 | Escalation engine — configurable escalation chains, SLA tracking, breach reporting | 0.5 weeks | 0.6 | Not started |

**Phase 6 Exit Criteria:** All lifecycle events (transfer, termination, maturity, total loss) handled with multi-party consent where required. Escalation chains working.

---

## Phase 7: External Integrations & Oracle Feeds (Weeks 28-30)

Connect to Australian data sources for real-time accuracy.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 7.1 | ATO rate feed — FBT rates, LCT thresholds, minimum residual tables (annual refresh) | 0.5 weeks | Phase 4 | Not started |
| 7.2 | Redbook / Glass's API — vehicle residual market values for maturity planning | 1 week | 6.3 | Not started |
| 7.3 | Insurance API adapter — premium quotes, renewal tracking, claim status | 1 week | 3.1 | Not started |
| 7.4 | Fuel price index — ACCC data for running cost projections | 0.5 weeks | 3.4 | Not started |
| 7.5 | CDR readiness — data sharing consent framework for future open banking/payroll integration | 0.5 weeks | 5.4 | Not started |

**Phase 7 Exit Criteria:** Live data feeds for ATO rates, vehicle valuations, and fuel prices. Insurance integration functional. CDR-ready consent architecture.

---

## Phase 8: Production Hardening (Weeks 31-34)

Security, scale, compliance, deployment.

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 8.1 | Security audit — OWASP top 10, Privacy Act compliance for salary data, penetration testing | 1 week | All | Not started |
| 8.2 | Key management — Ed25519 key generation, rotation, HSM integration for production signing | 1 week | 0.4 | Not started |
| 8.3 | Performance testing — target: 10,000 active leases, 500 events/day | 0.5 weeks | All | Not started |
| 8.4 | Deployment pipeline — CI/CD, staging environment, database migrations | 1 week | All | Not started |
| 8.5 | Monitoring & alerting — obligation engine health, payroll sync status, event ledger integrity checks | 0.5 weeks | All | Not started |
| 8.6 | Hash anchoring (optional) — periodic Merkle root to Ethereum for external tamper evidence | 0.5 weeks | 0.4 | Not started |
| 8.7 | Compliance documentation — Privacy Impact Assessment, data retention policy, ATO engagement | Throughout | All | Not started |

**Phase 8 Exit Criteria:** Security audit passed. Performance validated at scale. Deployed to production. Monitoring operational.

---

## Phase 9: Go-to-Market (Weeks 35+)

| # | Task | Est. | Dependencies | Status |
|---|------|------|--------------|--------|
| 9.1 | Pilot employer — 1 SME client, 5-20 leases, full lifecycle test | 4 weeks | Phase 8 | Not started |
| 9.2 | White-label package — for smaller lease providers wanting modern infrastructure | 2 weeks | Phase 8 | Not started |
| 9.3 | Employer sales collateral — ROI calculator, compliance automation pitch, STP2 pain-point messaging | 1 week | 9.1 | Not started |
| 9.4 | Financier partnership — one finance company agreement for direct integration | Ongoing | Phase 8 | Not started |
| 9.5 | NPC cross-sell integration — novated lease management as part of fractional CFO offering | 2 weeks | 9.1 | Not started |

---

## Key Metrics

| Metric | Phase 1 Target | MVP Target | Scale Target |
|--------|---------------|------------|--------------|
| Active leases managed | 1 | 50-100 | 10,000+ |
| Payroll integrations | Manual | Xero + MYOB | 5+ systems |
| Event ledger integrity | 100% | 100% | 100% |
| Obligation SLA compliance | N/A | 90% | 99% |
| Running cost claim turnaround | Manual | < 3 business days | < 1 business day |
| FBT calculation accuracy | Manual verification | Automated + verified | Auditor-certified |

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Contract templates | YAML + Pydantic | Simple, testable, hireable skills |
| Rules engine | Python | FBT/GST calculations, obligation logic |
| Event ledger | PostgreSQL (append-only) | Reliable, cheap, well-understood |
| Cryptographic signing | Ed25519 | Fast, secure, no certificate authority needed |
| Tamper evidence | Merkle tree + optional hash anchoring | Blockchain-grade auditability without blockchain |
| Document storage | S3-compatible + SHA-256 content addressing | Receipts, deeds, reports |
| API layer | FastAPI | Async, OpenAPI spec, type-safe |
| Frontend | HTMX + Alpine.js (NPC pattern) OR React | TBD based on team |
| Payroll integration | Xero API, MYOB API, adapter pattern | Extensible to KeyPay, etc. |
| Database | PostgreSQL | Event store + read models |
| Deployment | Docker + managed PostgreSQL | Simple, cheap, scalable |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Employer lock-in to incumbents | High | High | Target employers without current providers, or white-label to providers |
| EV FBT exemption sunsets | Medium | Medium | Build for all vehicle types, not just EV |
| Payroll API instability | Medium | Medium | Adapter pattern, manual fallback, polling with retry |
| "Just a better portal" commoditisation | High | High | Moat is obligation engine + tamper-evident ledger + NPC integration |
| Regulatory change (FBT rules) | Low | Medium | Configurable rules engine, ATO rate feed |
| Privacy Act breach | Low | Critical | Need-to-know data model, encryption at rest, Privacy Impact Assessment |
| Key person risk (small team) | Medium | High | Document everything, use standard tech stack |

---

## NPC Integration Points

If NovateX joins the NPC product family:

| NPC Layer | NovateX Application |
|-----------|-------------------|
| Layer 2: Field Library | Novated lease semantic fields (SalarySacrificePreTax, ECMContribution, RunningCostPool, ATOResidualMinimum) |
| Layer 5: Governance Memory | RunRecordLog = event ledger. EvidencePack = FBT reconciliation proof. |
| Omega Governed Contracts | "Structurally impossible to emit an incorrect payroll deduction" |
| Layer 4: AI Intent | NL queries: "what's my tax saving?" / "what's my residual?" |
| Layer 6: Board Readiness | Employer CFO dashboard: FBT exposure, fleet composition, compliance |
| Reconciliation Engine | Running cost pool reconciliation = bank transaction matching pattern |
