# NovateX

**Novated Lease Soft Contract Platform**

Multi-party automated financial agreements for Australian novated leases. Replaces PDF forms, email chains, and spreadsheet reconciliation with cryptographically signed event ledgers, automated obligation tracking, and real-time payroll integration.

## What is this?

A novated lease involves 3-4 parties (employee, employer, finance company, fleet manager) with complex recurring financial flows — salary sacrifice splits, GST claims, FBT reconciliation, running cost pools. Today this is managed with spreadsheets, phone calls, and 5-10 day turnarounds.

NovateX automates the coordination with:

- **Ricardian contract templates** — human-readable + machine-executable lease agreements (YAML + legal PDF hash-bound)
- **Signed event ledger** — every deduction, claim, and state transition is cryptographically signed and Merkle-chained
- **Obligation engine** — tracks who owes what to whom, auto-triggers on events, escalates on deadline breach
- **Multi-party portals** — role-based views for employee, employer, financier, and fleet manager
- **Payroll integration** — Xero/MYOB API adapters for automated salary sacrifice deductions
- **FBT engine** — statutory formula, operating cost method, ECM, EV exemption, STP2 output

## Architecture Decision

**Signed event ledger, NOT blockchain.** Corda was evaluated and rejected:

- Known parties under Australian law don't need Byzantine fault tolerance
- ASX CHESS failure (A$250M write-off) makes DLT a credibility risk in AU financial services
- 95% of auditability at 10% of complexity
- PostgreSQL at $50/mo vs Corda cluster at $500+/mo

Tamper evidence via Ed25519 signatures + Merkle tree + optional hash anchoring to Ethereum.

## Market

- ~400,000 active novated leases in Australia
- ~130,000 new originations/year, AUD 6-8B annual volume
- 15-25% YoY growth driven by EV FBT exemption (July 2022)
- Incumbents (MMS/Maxxia, SG Fleet) running call-centre operations with 1990s technology

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Contract templates | YAML + Pydantic |
| Rules engine | Python |
| Event ledger | PostgreSQL (append-only) |
| Cryptographic signing | Ed25519 |
| Tamper evidence | Merkle tree |
| API | FastAPI |
| Frontend | HTMX + Alpine.js |
| Payroll | Xero API, MYOB API |
| Documents | S3 + SHA-256 content addressing |

## Status

**Pre-build** — Architecture and research complete. See [ROADMAP.md](ROADMAP.md) and [roadmap-dashboard.html](roadmap-dashboard.html).

## Part of NPC Product Family

NovateX integrates with the Newport Pembury & Co moat stack — Field Library for financial semantics, Governance Memory for audit trails, Omega for governed contract compilation, AI Intent for natural language queries.

---

Newport Pembury & Co
