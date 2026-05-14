# Literature Review Matrix — 4 Base Papers
*Project: Hybrid Federated Learning + Blockchain + Optimized Homomorphic Encryption for Privacy-Preserving Healthcare Analytics*

---

## 1. Side-by-side comparison matrix

| Dimension | **P1 — Lee, Lim, Eswaran (2025)** *Discover Public Health / Springer* | **P2 — Firdaus, Larasati, Rhee (2025)** *Internet of Things, Elsevier 31:101579* | **P3 — Naresh, Reddi (2025)** *J. Big Data 12:52, Springer Open* | **P4 — Rauthan (2024)** *G.B. Pant IET, applied study* |
|---|---|---|---|---|
| **Type** | Survey of HE attacks/defenses | Empirical framework (FL+BC+HE) | Empirical framework (HE-LR single silo) | Empirical FHE benchmarking |
| **HE scheme** | All families (PHE/SHE/FHE/FLHE) reviewed | "FHE" via SEAL/Pyfhel (likely CKKS, unnamed) | CKKS (TenSEAL) | CKKS, TFHE/CGGI, FHEW, BGV/BFV (OpenFHE, TFHE-rs, Concrete-ML) |
| **HE parameters** | n/a | poly_modulus_degree m ∈ {1024, 2048}, q ∈ {128,192} — **insecure / toy params** | N ∈ {4096, 8192}, coeff_mod=[40,20,40]/[40,21×6,40], scale=2²⁰/2²¹ | Various; CKKS pubkey 18.9 MB, mult-key 56.6 MB, ciphertext 13.6 MB / batch |
| **Federated learning** | Mentioned in §3.5 only | FedAvg, cross-silo, clustered (cosine sim) | None (single hospital → cloud) | None (single client–server) |
| **# clients** | n/a | 2–5 per cluster, 5 clusters max | 1 | 1 |
| **Blockchain** | Absent | Ethereum / Ganache (auto-mining ≈ PoA); consortium claim | Absent | Absent |
| **Smart contracts** | n/a | Store enc hashes, verify accuracy, distribute rewards | None | None |
| **Key management** | Threshold/multi-key reviewed but no design | Centralized Trusted Authority — single PoF | Hospital + patient pubkeys, hospital decrypts and re-encrypts each round | Client-side, periodically refreshed; HbC server "trusted zone" |
| **Threat model** | 7 attack classes (crypto + side-channel + scheme + impl) | Implicit HbC server; no FL-attack experiments | 5 attack classes (poisoning, evasion, MIA, model inv, model extraction) — informal | HbC server only |
| **Model** | n/a | Custom CNN (6 Conv + 2 FC) for binary classification | Logistic regression | Trivial NN, FC image NN, 40+ layer PCR NN |
| **Datasets** | Listed only as domains | COVID-19 Radiography (1000 sample), Brain Tumor MRI (1000 sample) | Heart (Kaggle 1025), Statlog (270), Framingham (~4240) | Synthetic QC vectors / matrices, NN models |
| **Best accuracy** | n/a | COVID 97.25%, Brain MRI 86.25% | Heart LR 84% (HE) vs 85% (plain); Statlog 100% (overfit); Framingham 65% | n/a (not classification benchmarks) |
| **Latency** | n/a | C4 (5 hospitals) total 2511 s; enc dominates (1655 s) | Train enc 1–12 s; no per-inference latency | NN inference ~20–30 s/sample; 1 s for trivial NN |
| **Communication cost** | Not measured | Not reported in MB | Not reported | Not reported |
| **Blockchain throughput** | n/a | 722 tx at 10 epochs (linear); no TPS, no gas | n/a | n/a |
| **Bootstrapping** | Reviewed | Not discussed | Avoided via decrypt-re-encrypt loop | Discussed for CGGI |
| **Sigmoid / non-linear** | Reviewed (polynomial approx) | ReLU (cleartext local training) | **Undocumented / mathematically ambiguous** | Polynomial / Chebyshev shown |
| **Stated novelty** | First unified attack-defense taxonomy | Clustered cross-silo FL + HE + BC + incentives | HE-LR + 5-attack analysis on 3 datasets | OpenFHE vs TFHE-rs vs Concrete-ML for healthcare |
| **Honest limitations admitted** | Overhead, PQ open, hybrid needed | Non-IID handling, attack defense | HE overhead, small data, binary only | NN inference too slow, accuracy loss |
| **Reproducibility** | n/a (survey) | GitHub linked, Ganache + Pyfhel | TenSEAL + Colab, no public repo | OpenFHE / TFHE-rs / Concrete-ML, no public repo |

---

## 2. Per-paper deep analyses (verbatim research notes)

The full per-paper structured analyses (≥700 words each) are kept in:
- `papers/P1_HE_survey_attacks_defenses.md`
- `papers/P2_BCFL_HE_healthcare.md`
- `papers/P3_FHE_LR_heart_disease.md`
- `papers/P4_HE_healthcare_industry.md`

These should be cited as the canonical record of what each paper does and where it falls short.
