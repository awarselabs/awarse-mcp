---
title: "SeatPrune Quickstart: Automated SaaS Seat Reclamation"
description: "Eliminate zombie licenses and cut developer SaaS spend. Set up SeatPrune to audit and reclaim inactive seats across GitHub, Slack, and Jira."
keywords: ["saas seat reclamation", "finops developer tools", "seatprune quickstart", "audit inactive github seats", "cut ci cd saas spend"]
category: "seatprune"
lastModified: 2026-09-09
---

# SeatPrune Quickstart: Automated SaaS Seat Reclamation

Unused enterprise seats represent one of the fastest-growing lines of wasted engineering spend. Developer turnover, contractors rolling off, and forgotten evaluations leave high-tier licenses assigned to inactive accounts.

`seatprune` is a local-first, ephemeral FinOps agent built to inspect activity logs across developer tooling platforms, surface reclaimable seats, and automate de-provisioning workflows without requiring invasive third-party SaaS access.

---

## Key Capabilities

* **Multi-Provider Inspection:** Connects to GitHub Enterprise, Slack, Jira, and Google Workspace via standard API tokens.
* **Heuristic Inactivity Scoring:** Distinguishes between truly dormant users and periodic contributors using commit history, PR reviews, and SSO login timestamps.
* **Dry-Run by Default:** Generates actionable remediation reports before revoking access or modifying memberships.
* **Local-First Execution:** Runs entirely inside your terminal, local runner, or scheduled CI workflow—no company user lists leave your infrastructure.

---

## Installation

Install `seatprune` via PyPI:

```bash
pip install seatprune
```
