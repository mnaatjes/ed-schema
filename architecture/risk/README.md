---
title: "Master Risk Register"
tags: ["architecture", "risk", "up"]
created_at: "2026-10-29"
last_updated_at: "2026-10-29"
---

# Master Risk Register

This directory contains the Master Risk Register and associated risk assessment ledgers for `ed-schema`.

## Risk Quantification Methodology

Risks are quantified using the Barry Boehm Unified Process Risk Exposure formula:

$$RE = P \times I$$

Where:
- **Probability ($P$):** Scale of $0.00$ to $1.00$ indicating likelihood of occurrence.
- **Impact ($I$):** Scale of $1$ (negligible) to $10$ (catastrophic architectural failure).
- **Risk Exposure ($RE$):** Product of probability and impact ($0.00$ to $10.00$).

## Severity Thresholds

- **Critical ($RE \ge 6.0$):** Inception/Elaboration milestone blocker. Mandatory architectural spike or mitigation artifact required before phase transition.
- **High ($4.0 \le RE < 6.0$):** Requires proactive mitigation plan and tracking across iterations.
- **Medium ($2.0 \le RE < 4.0$):** Monitored within regular iteration planning.
- **Low ($RE < 2.0$):** Accepted technical debt or minor operational overhead.

## Canonical Files

- `risk-list.md`: Living Master Risk Register tracking identified risks, owners, status, mitigation strategies, and exposure vectors.
