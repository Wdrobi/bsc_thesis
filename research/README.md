# MEDUSA — Research Workspace

Q1-journal research project: a hybrid **Federated Learning + Blockchain + Optimized Homomorphic Encryption** framework for privacy-preserving healthcare analytics.

## Contents
- `01_literature_matrix.md` — side-by-side comparison of the 4 base papers + per-paper analysis index.
- `papers/P1_HE_survey_attacks_defenses.md` — Lee, Lim, Eswaran (2025) — survey of HE attacks/defenses.
- `papers/P2_BCFL_HE_healthcare.md` — Firdaus, Larasati, Rhee (2025) — closest competitor, Elsevier IoT.
- `papers/P3_FHE_LR_heart_disease.md` — Naresh & Reddi (2025) — single-silo CKKS-LR baseline.
- `papers/P4_HE_healthcare_industry.md` — Rauthan (2024) — FHE benchmarking in healthcare.
- `02_gap_analysis.md` — 17 cross-paper gaps (G1–G17), Tier-1 highlights P1's unresolved CKKS precision/security conflict.
- `03_framework_proposals.md` — three candidate frameworks (HEPHAESTUS / **MEDUSA** / PHOENIX) with a comparison rubric.
- `04_recommendation_and_roadmap.md` — MEDUSA full design + Phase 3–8 roadmap.

## Recommended framework: **MEDUSA**
**M**odulus-aware **E**ncrypted **D**ecentralized hospital analytics with edge–cloud split FL and on-chain Shapley.

Headline novelties:
1. **NBA-CKKS Scheduler** — first principled noise-budget controller that resolves the IND-CPAD precision-vs-security conflict surfaced by Lee et al. (2025) p. 11.
2. **Threshold (t,n)-MHE** — eliminates the centralized Trusted Authority that breaks every prior healthcare BC+FL+HE design.
3. **Encrypted Multi-Krum + on-chain HE-Shapley contribution scoring + slashing** — blockchain does real algorithmic work, not just hash storage.
4. **Layer-wise selective HE + CUDA-accelerated CKKS** — communication and compute optimizations that target the bottleneck Firdaus et al. (2025) expose (encryption = 66% of round wall-clock).

## Next step
Begin Phase 3.1 (math + diagrams) per `04_recommendation_and_roadmap.md` §3.

## Reproducibility
Implementation will live under `D:\framework\medusa\` (see roadmap §4.2 for folder layout). Configurations driven by Hydra; runs reproducible via `scripts/reproduce_paper.sh`.
