# MEDUSA — Recommended Framework & Full Research Roadmap (Phases 3–8)

> *Modulus-aware Encrypted Decentralized Hospital Analytics with Edge–Cloud Split FL and On-Chain Shapley*

This document is the canonical roadmap. It assumes:
- Recommended framework: **MEDUSA** (see `03_framework_proposals.md`).
- Headline novelties locked: **NBA-CKKS scheduler**, **threshold-MHE keys at Tier-3**, **encrypted Multi-Krum**, **on-chain HE-Shapley + slashing**, **layer-wise selective HE**, **CUDA-accelerated CKKS**.
- Target submission: a Q1 SCIE-indexed journal at the FL + privacy + healthcare intersection.

---

## Phase 3 — System Design (Months 1–2)

### 3.1 Entities and trust model
| Entity | Cardinality | Role | Trust |
|---|---|---|---|
| Hospital edge clients **H_i** | 20+ simulated; 3 real GPU nodes in lab | Local training; encrypts updates | Honest-but-curious; up to 30% Byzantine |
| Regional cluster aggregator **R_j** | 4–5 | Encrypted Multi-Krum within cluster | HbC; verifiable via on-chain commits |
| Tier-3 consortium nodes **G_k** | 5 (t = 3 threshold) | Threshold key share; global aggregation; smart-contract execution; NBA-CKKS scheduler | t-of-n malicious-tolerant |
| Trusted Setup Coordinator | 1, one-time | Orchestrates DKG; deletes secrets after | Trust required at setup only |
| External patients / clinicians | n/a in v1 (out of scope; ablation only) | Query inference | n/a |

### 3.2 Mathematical model

**Local update (client i, round t):**
- Plaintext step: w_i^{t+1/2} = w^t − η · ( ∇L_i(w^t) + μ(w^t − w_global^t) )   [FedProx]
- Quantize gradients to b bits: q_i^{t+1/2} = Q_b(w_i^{t+1/2} − w^t)
- Selective encryption mask m: m_l = 1 if layer-l sensitivity s_l > δ else 0
- Encrypted update: c_i^t = CKKS.Enc_pk(m ⊙ q_i^{t+1/2}) ; LDP-perturbed clear part for ¬m

**Cluster aggregation (R_j):**
- Robust Multi-Krum in CKKS: select k closest ciphertexts by pairwise encrypted ‖·‖₂² distances (use SIMD batching).
- Cluster ciphertext: C_j^t = Σ_{i∈Krum(C_j)} (n_i/N_j) · c_i^t

**Global aggregation (G_k, threshold-decrypted only after on-chain commit):**
- Aggregate: A^t = Σ_j C_j^t
- Threshold partial decryption: pd_k = A^t · s_k where s_k is k-th secret share; combined by Lagrange to recover w^t+1 update for re-encryption next round.

**NBA-CKKS scheduler decision** at round t:
- Inputs: residual noise budget B_t, model dim d, layer mask m, target precision τ, target sec level λ ≥ 128.
- Outputs (a) bootstrap_trigger ∈ {0,1}, (b) modulus-switch chain step, (c) re-encrypt-under-fresh-keyshare ∈ {0,1}, (d) coeff_mod chain pick for next round.
- Decision rule: minimize wall-clock subject to B_t ≥ Bootstrap_threshold OR precision_after_noise_flood ≥ τ.

**HE-Shapley contribution (on-chain SC):**
- Sample m sub-coalitions S_l ⊂ H \ {h_i} of size k.
- Compute φ̂_i = (1/m) · Σ_l [ score(S_l ∪ {h_i}) − score(S_l) ] where score = encrypted FedProx validation loss on shared validation ciphertext.
- Reward ρ_i ∝ φ̂_i; slash if φ̂_i < threshold or if encrypted Krum vote rejected h_i.

### 3.3 Threat model (formal)
- **Crypto layer:** CPA, CCA1, IND-CPAD adversary; ≤ t−1 corrupted Tier-3 nodes; passive side-channel (timing) but not active fault injection (deferred).
- **ML layer:**
  - **Membership inference** (Yeom 2018; ML-Doctor) — shadow models with same architecture.
  - **Gradient inversion** (DLG, iDLG, GradInversion) — full-batch reconstruction attempt on intercepted ciphertext (must remain encrypted → upper-bounded by IND-CPAD).
  - **Poisoning** — label flip, sign flip, additive backdoor (BadNets-style trigger).
  - **Sybil** — single adversary registers ν fake hospitals.
  - **Free-rider** — null-gradient submitter.
  - **Collusion** — up to t−1 Tier-3 nodes + 30% Tier-1 hospitals.
- **Out of scope (v1):** active fault injection inside HE library; quantum adversary (we use 128-bit lattice security but don't claim PQ-safety beyond CKKS' LWE base).

### 3.4 Workflow (one FL round)
1. G nodes broadcast w^t and (N, coeff_mod, scale)^t from NBA-CKKS scheduler.
2. Each H_i trains locally for E epochs (FedProx); quantizes; selectively encrypts; signs and posts ciphertext-commit (hash) on-chain; uploads ciphertext off-chain to its R_j.
3. R_j runs encrypted Multi-Krum; emits cluster ciphertext C_j^t + commit on-chain.
4. G nodes verify commits, sum to A^t, partial-decrypt with t shares.
5. Smart contract triggers HE-Shapley sampling job; computes φ̂_i; emits reward/slash events.
6. Global w^{t+1} re-encrypted under new threshold pubkey (if NBA-CKKS scheduler triggers re-key) and broadcast for round t+1.

### 3.5 Algorithms / pseudocode (high level)

```
Algorithm 1 — Hospital_Client_Round(w^t, ctx^t)
  q_i ← Quantize_b( LocalFedProx(w^t, D_i, E, μ) − w^t )
  m  ← SensitivityMask(model, threshold=δ)            # offline precomputed
  c_i ← CKKS.Enc(ctx^t, m ⊙ q_i)
  ldp_i ← LDP(¬m ⊙ q_i, ε)                            # for non-sensitive layers
  commit ← H(c_i ∥ ldp_i ∥ round=t)
  Tx.post_commit(H_i, commit)                         # to chain
  Upload(c_i, ldp_i) → R_j
```

```
Algorithm 2 — NBA_CKKS_Scheduler(state_t)
  B_t   ← MeasureNoiseBudget(A^{t-1})
  prec_t ← BitsAfterFlood(scale_t, λ=128)
  if B_t < B_min or prec_t < τ:
      if cost(bootstrap) < cost(rekey):
          action ← BOOTSTRAP
      else:
          action ← REKEY_THRESHOLD
  else:
      action ← MODULUS_SWITCH if depth_used_t > depth_max/2 else KEEP
  return (action, next_params)
```

```
Algorithm 3 — Encrypted_Multi_Krum( {c_1..c_n} )
  d_ij ← Σ slot-wise (c_i - c_j)^2          # encrypted L2 (one mult, batched)
  s_i  ← partial_decrypt_only_distances(d_ij)   # decrypt distances, NOT updates
  K    ← argmin_{|K|=n-f-2} Σ_{j∈K_i} s_ij
  C_j  ← Σ_{i∈K} (n_i / Σ n_i) · c_i
  return C_j
```

```
Smart-Contract HE-Shapley (Quorum/Solidity 0.8.x)
  function sampleAndScore(hospital_id, round) external onlyAggregator {
      for l in 1..m:
          S ← randomCoalition(H \ {h}, k);
          base ← scoreOf(S, round);
          plus ← scoreOf(S ∪ {h}, round);
          phi_l ← plus - base;
      phi_hat[h] ← mean(phi_l);
      if phi_hat[h] < slash_threshold: slash(h);
      else: reward(h, phi_hat[h]);
  }
```

### 3.6 Diagrams to produce
- D1. 3-tier architecture (icons: hospital ↔ regional ↔ global ↔ chain).
- D2. Sequence diagram of one round (Mermaid → final TikZ).
- D3. NBA-CKKS state machine.
- D4. Threat-model coverage matrix (crypto × ML × collusion axes).

---

## Phase 4 — Implementation (Months 2–5)

### 4.1 Stack
- **Language:** Python 3.11 (Flower-compatible), Solidity 0.8.x for chaincode.
- **FL framework:** [Flower 1.10+](https://flower.dev/) (chosen over PySyft for hospital-realistic deployment).
- **HE:** **OpenFHE 1.2 (CPU)** primary; **TenSEAL** for cross-validation of CKKS; optional **OpenFHE-CUDA fork** for GPU path.
- **Threshold MHE:** Mouchet's `lattigo`-style protocol — we wrap **Lattigo v5 (Go) → gRPC bridge** to Python clients, *or* use OpenFHE 1.2's experimental multi-party module.
- **Blockchain:** **Hyperledger Fabric 2.5** (PBFT-style ordering with Raft) for v1; ablation comparison vs **Quorum (IBFT 2.0)**.
- **ML:** PyTorch 2.4; Opacus for DP-LDP ablation.
- **Attack simulators:** [FedSwarm](https://github.com/), Adversarial Robustness Toolbox 1.18, `dlg`/`iDLG` reference implementations.
- **Diagrams:** Mermaid (draft) → TikZ + Asymptote (camera-ready).
- **Runtime / orchestration:** Docker Compose for 20 simulated hospitals + 5 G-nodes + 5 R-nodes; Kubernetes optional.
- **Hardware:** Lab — 1 × A100 80 GB, 2 × RTX 4090, 64-core EPYC for CPU baseline. Optional cloud burst (AWS p4d.24xlarge) for scale runs.

### 4.2 Folder layout
```
medusa/
├── README.md
├── pyproject.toml
├── requirements.txt
├── configs/                  # YAML configs: experiments, attacks, FL
│   ├── base.yaml
│   ├── nbackks.yaml          # noise-budget scheduler params
│   ├── attacks/{mia,dlg,labelflip,signflip,sybil,freerider,collusion}.yaml
│   └── datasets/{mimic,eicu,fedisic,fedtcga,fedheart}.yaml
├── medusa/
│   ├── client/               # Flower clients per hospital
│   ├── server/               # Flower server + cluster aggregator + G-node
│   ├── crypto/
│   │   ├── ckks_ops.py
│   │   ├── threshold_mhe.py
│   │   ├── nbackks_scheduler.py
│   │   └── selective_encryption.py
│   ├── fl/
│   │   ├── fedprox.py
│   │   ├── multi_krum_he.py
│   │   └── personalization.py
│   ├── chain/
│   │   ├── chaincode/        # Solidity / Go chaincode
│   │   ├── deployer.py
│   │   └── shapley_oracle.py
│   ├── attacks/              # MIA, DLG, label/sign flip, free-rider, sybil
│   ├── data/                 # Loaders, Dirichlet partitioner, FLamby wrappers
│   ├── eval/                 # metrics, latency, communication, gas trackers
│   └── utils/                # logging, seed, hydra glue
├── notebooks/                # exploratory / figure generation
├── scripts/
│   ├── run_experiment.sh
│   ├── run_attack_suite.sh
│   ├── start_fabric_net.sh
│   └── reproduce_paper.sh
├── tests/                    # pytest + property tests on CKKS ops
└── docker/
    ├── client.Dockerfile
    ├── aggregator.Dockerfile
    └── docker-compose.yaml
```

### 4.3 Module-by-module milestones
1. **M1 (Wk 1–3):** CKKS wrapper + selective encryption + quantization-aware encoder unit-tested.
2. **M2 (Wk 3–5):** Flower client/server with FedProx + non-IID Dirichlet partitioner; baseline plaintext FedAvg/FedProx on MIMIC-III mortality + FedISIC.
3. **M3 (Wk 5–7):** Threshold MHE prototype (DKG, partial decryption) — Lattigo bridge or OpenFHE-MP.
4. **M4 (Wk 7–9):** Encrypted Multi-Krum + NBA-CKKS scheduler.
5. **M5 (Wk 9–11):** Fabric 2.5 network + chaincode (commit + Shapley + slash) + gas/TPS instrumentation.
6. **M6 (Wk 11–13):** Attack suite (MIA, DLG, labelflip, signflip, sybil, free-rider, collusion).
7. **M7 (Wk 13–15):** GPU CKKS path; ablations.
8. **M8 (Wk 15–17):** Final scale runs, figure freeze.

### 4.4 Reproducibility
- Hydra configs; deterministic seeds across NumPy / PyTorch / Flower.
- `reproduce_paper.sh` executes the entire table+figure pipeline in ≤ 8 GPU-days.
- Public repo at submission + Zenodo DOI for the snapshot.

---

## Phase 5 — Datasets & Experiments (Month 5)

### 5.1 Dataset selection (rank-ordered by reviewer credibility)
| # | Dataset | Modality | Size | FL realism | Notes |
|---|---|---|---|---|---|
| 1 | **MIMIC-III v1.4** (or MIMIC-IV 3.0) | Tabular EHR (ICU) | 60k patients | High — hospital-split in original studies | Primary for in-hospital mortality + sepsis prediction |
| 2 | **eICU-CRD v2.0** | Tabular EHR (multi-ICU) | 200k+ ICU stays | Native multi-hospital partition (208 hospitals) | Gold-standard non-IID FL benchmark for healthcare |
| 3 | **FedISIC2019 (FLamby)** | Dermoscopy images | 23k images, 6 sources | Native non-IID FL split | CNN backbone, well-publishable |
| 4 | **FedTCGA-BRCA (FLamby)** | Genomic + clinical | 1k+ patients, 5 sites | Native FL split | Survival analysis (cox-style head) |
| 5 | **FedHeart (synthetic federated heart)** | Tabular | UCI Cleveland + Statlog + Hungarian + Switzerland + VA | 4 sites | Direct head-to-head vs P3 (Naresh & Reddi) |
| 6 | **MedMNIST v2** (PneumoniaMNIST, RetinaMNIST) | 28×28 imaging | 100k+ | Synthetic Dirichlet split | Ablation-only |

### 5.2 Partitioning
- **Natural splits** (eICU hospital_id, FedISIC source, FedTCGA-BRCA site) → realism.
- **Dirichlet(α)** with α ∈ {0.1, 0.5, 1.0} → controlled non-IID for sensitivity analysis.

### 5.3 Preprocessing
- MIMIC-III: extract benchmark feature set from Harutyunyan 2019 — 17 time-series + 5 statics; in-hospital mortality ≤ 24h horizon.
- FedISIC: standard ISIC2019 train transforms; ResNet-50 imagenet-pretrained backbone, head retrained federated.
- Sigmoid / softmax outputs replaced with **degree-3 Chebyshev** polynomial approximations on [−6, 6] post-batchnorm.

### 5.4 Experiment matrix (per dataset)
| Experiment | Variants | Output |
|---|---|---|
| **E1 Baselines** | Plaintext FedAvg, FedProx, Wibawa[16], Rieyan[35], Firdaus[P2], Naresh[P3] | Acc / F1 / AUC table |
| **E2 MEDUSA full** | NBA-CKKS + threshold + Krum + Shapley | Acc / F1 / AUC + latency + MB/round + gas |
| **E3 Ablations** | −NBA-CKKS, −threshold, −Krum, −selective HE, −GPU | One curve per ablation |
| **E4 Non-IID sensitivity** | α ∈ {0.1, 0.5, 1.0}; cluster count k ∈ {1, 4, 8} | Convergence curves |
| **E5 Scalability** | n_clients ∈ {5, 10, 20, 50, 100} | Wall-clock + MB scaling |
| **E6 Attacks** | MIA / DLG / labelflip / signflip / sybil / free-rider / collusion | Attack-success rate, accuracy under attack, Shapley discrimination |
| **E7 Crypto sensitivity** | poly_mod ∈ {8192, 16384, 32768}; scale 2^21..2^40; flood σ sweep | Precision-latency-security frontier |
| **E8 Blockchain sensitivity** | Fabric vs Quorum; n_orderers ∈ {3, 5, 7}; load 10–1000 tx/round | TPS / finality / gas |
| **E9 GPU vs CPU** | OpenFHE-CUDA vs OpenFHE CPU | Speedup curve |

---

## Phase 6 — Evaluation

### 6.1 Metrics
- **ML utility:** Accuracy, Precision, Recall, F1, ROC-AUC, AUPRC (for imbalanced eICU sepsis / Framingham).
- **Privacy:** MIA AUC (lower = stronger privacy); DLG reconstruction PSNR / SSIM (lower = better); ε used for DP-LDP ablation arm.
- **Crypto:** Bits-of-precision-after-flood; effective IND-CPAD security level; noise-budget headroom histograms.
- **Latency:** Per-round wall-clock; encryption time; aggregation time; threshold-decrypt time; end-to-end round.
- **Communication:** MB/round/client; MB/round on chain; total federation MB; CKKS pubkey/ciphertext sizes.
- **Blockchain:** TPS, p50/p99 finality, gas/tx, total federation gas/round.
- **Robustness:** Accuracy under {labelflip 10/20/30%, signflip, sybil 10/30%, free-rider 20%}; Shapley discrimination AUC (free-rider vs honest).
- **Energy (optional):** kJ/round via `pyJoules` or NVML on the A100 path.

### 6.2 Statistical rigor
- 5 seeds per cell; report mean ± 95% CI.
- Paired Wilcoxon signed-rank for MEDUSA vs each baseline.
- Holm-Bonferroni correction for multiple comparisons.

### 6.3 Tables & figures to deliver
- T1. Literature comparison (already drafted in `01_literature_matrix.md`).
- T2. Headline accuracy + latency + MB + gas across datasets vs P2/P3 and DP/SecAgg baselines.
- T3. Threat-model coverage matrix.
- T4. NBA-CKKS scheduler decision table.
- F1. 3-tier architecture.
- F2. Convergence (acc vs round) for α ∈ {0.1, 0.5, 1.0}.
- F3. Precision-latency-security frontier (3D scatter).
- F4. Scalability (wall-clock + MB vs n_clients).
- F5. Attack robustness bar chart.
- F6. Shapley contribution histogram (free-rider separation).
- F7. Fabric vs Quorum TPS / latency.
- F8. GPU vs CPU speedup curves.

### 6.4 Acceptance gates (internal)
- Must beat P2 (Firdaus 2025) on COVID accuracy AND latency AND MB/round under matched setup.
- Must beat P3 (Naresh 2025) on Heart-disease accuracy under cross-silo (≥ 4 hospitals) setting.
- MIA AUC ≤ 0.55 (near-random); DLG PSNR < 14 dB (unintelligible reconstruction).
- IND-CPAD security ≥ 128 bits while gradient precision ≥ τ = 12 bits.
- Smart-contract gas/round ≤ 6 M (median Quorum / Fabric).

---

## Phase 7 — Paper Writing (Months 6–7)

### 7.1 Section plan (~12–14 pages 2-column IEEE-Trans style, ~7–8k words ex-refs)
1. **Abstract** (250 words, includes 1 sentence per: problem, novelty, method, results, impact).
2. **Introduction** (1.5 pp) — motivation, P1's unresolved conflict (G1+G2), 4 contributions, paper roadmap.
3. **Related Work** (1.5 pp) — taxonomy: BC+FL+HE healthcare (P2 + Wibawa + Rieyan + Yang + BPFL); CKKS-FL (P3 + Chen + Wei); HE benchmarking (P4 + OpenFHE/TenSEAL); FL attacks. Use Table 1 from `01_literature_matrix.md`.
4. **Threat Model & Preliminaries** (1 pp) — CKKS, IND-CPAD, threshold MHE, FedProx, Multi-Krum.
5. **MEDUSA Framework** (2 pp) — architecture (Fig. 1), notation, end-to-end round.
6. **NBA-CKKS Scheduler** (1.5 pp) — formal noise-budget tracking, precision-security co-design (Theorem 1: parameter set P satisfies τ-precision AND λ-security iff …), Algorithm 2.
7. **Encrypted Robust Aggregation** (1 pp) — encrypted Multi-Krum, encrypted Shapley.
8. **Implementation** (0.75 pp) — stack, code/Zenodo links.
9. **Evaluation** (3 pp) — E1–E9 results, Tables T2–T4, Figures F2–F8.
10. **Security Analysis** (0.75 pp) — proof sketches, attack-experiment summary.
11. **Discussion & Limitations** (0.5 pp) — PQ, malicious-side-channel, real-hospital deployment.
12. **Conclusion & Future Work** (0.25 pp).
13. **References** (70–90 entries, IEEE style).

### 7.2 Writing style guidelines
- Active voice, declarative claims; no "we believe" or hedging on results.
- Equation-anchored novelty (Theorem 1, Algorithm 2) so the contribution is mechanical, not narrative.
- Reference every claim, especially attack-experiment outcomes.
- Avoid "AI-style" generic transitions; use venue-style prose (e.g., IEEE TIFS authors).

### 7.3 Bibliography seed (must-cite)
- P1–P4 (this matrix).
- McMahan et al. 2017 (FedAvg); Li et al. 2020 (FedProx); Blanchard 2017 (Multi-Krum); Cao et al. 2021 (FLTrust).
- Cheon et al. 2017 (CKKS); Mouchet et al. PETS'21 (Multiparty HE); Li-Micciancio CRYPTO'22 (IND-CPAD); Guo et al. USENIX'24 (CKKS key recovery).
- Ghorbani-Zou 2019 (data Shapley); Wang et al. 2020 (FL contribution evaluation).
- Yeom et al. CSF'18 (MIA); Zhu et al. NeurIPS'19 (DLG); Geiping et al. NeurIPS'20 (GradInversion).
- Androulaki et al. EuroSys'18 (Hyperledger Fabric); De Angelis 2018 (IBFT 2.0 Quorum).
- HIPAA §164.514; GDPR Art. 9, 17, 32; EU AI Act 2024.

---

## Phase 8 — Publication Support

### 8.1 Recommended Q1 venue ranking
| Tier | Venue | IF (latest) | Indexing | Fit | Reviewer expectation |
|---|---|---|---|---|---|
| **A1 (top pick)** | **IEEE Transactions on Information Forensics and Security (TIFS)** | ~7.2 | SCIE Q1, CCF-A | Privacy + cryptography + FL | Heavy crypto rigor; need formal proofs; attack experiments mandatory |
| **A1** | **IEEE Transactions on Dependable and Secure Computing (TDSC)** | ~7.0 | SCIE Q1 | Same as TIFS, slightly more systems | Same expectations |
| **A2** | **IEEE Journal of Biomedical and Health Informatics (J-BHI)** | ~7.7 | SCIE Q1 | Healthcare-focused; FL accepted | Clinical relevance must be explicit |
| **A2** | **Elsevier *Future Generation Computer Systems* (FGCS)** | ~7.5 | SCIE Q1 | FL + BC + cloud | Wants systems & evaluation depth, BC story matters |
| **A2** | **Elsevier *Information Sciences*** | ~8.1 | SCIE Q1 | Broad; novelty + math | Strong math required |
| **A3** | **Elsevier *Internet of Things*** (where P2 published) | ~6.0 | SCIE Q1 | Direct fit; head-to-head w/ P2 | Lower bar than TIFS; faster cycle |
| **A3** | **IEEE Internet of Things Journal** | ~10.6 | SCIE Q1 | Edge + cloud + FL | Strong fit; longer review |
| **A3** | **Springer *Journal of Big Data*** (where P3 published) | ~8.6 | SCIE Q1 | Open access; healthcare-friendly | Pay APC; faster cycle |
| **A4 (backup)** | **MDPI *Sensors*** (Q1 since 2024) | ~3.8 | SCIE Q1 | Permissive; sensor/health FL | APC; fast turnaround |

**My recommendation:** Submit first to **IEEE TIFS** (A1). If rejected, **FGCS** or **IoT-J** (A3). Backup **Elsevier Internet of Things** (head-to-head P2 venue).

### 8.2 Acceptance probability heuristic
- TIFS: ~12–18% (depends on crypto-novelty proof quality of NBA-CKKS).
- IoT-J / FGCS: ~25–30%.
- *Internet of Things* (Elsevier): ~30–35% — direct head-to-head with P2 *helps* if we clearly beat them.

### 8.3 Reviewer pre-empt checklist
- "Did you compare against [P2 Firdaus 2025, P3 Naresh 2025, Yang BPFL]?" → yes, Table T2.
- "Is your HE actually 128-bit secure?" → yes, Theorem 1 + param table.
- "How does it scale?" → 20→100 clients in E5.
- "MB/round?" → reported.
- "Real consensus, not Ganache?" → Fabric + Quorum benchmark in E8.
- "Attack resilience?" → MIA, DLG, labelflip, signflip, sybil, free-rider in E6.
- "Reproducibility?" → repo + Zenodo + Docker.

### 8.4 Suggested timeline (12 months total)
| Month | Phase |
|---|---|
| 1–2 | Phase 3 — System design + threat model + math + diagrams D1–D4 |
| 2–5 | Phase 4 — Implementation milestones M1–M8 |
| 5 | Phase 5 — Dataset prep, baseline reproduction |
| 5–6 | Phase 6 — Full evaluation runs (E1–E9) |
| 6–7 | Phase 7 — Paper drafting (12-page version) |
| 7 | Internal review + revision |
| 8 | Submit to TIFS |
| 8–11 | Wait for reviews; prepare extension for backup venue |
| 11–12 | Revisions / camera-ready |

---

## Appendix A — Open risks
- **NBA-CKKS theoretical proof** (Theorem 1) may end up empirical. Mitigation: frame as algorithmic contribution with measured precision-security frontier (E7).
- **HE-Shapley cost.** Mitigation: Monte-Carlo with m ≤ 50 sub-coalitions; lazy on-chain evaluation (1 hospital per round, round-robin).
- **OpenFHE multiparty module maturity.** Mitigation: fall back to Lattigo-Go bridge if OpenFHE-MP unstable at v1.2.
- **MIMIC-III access timing.** Mitigation: start credentialed application immediately at Phase 3 start (PhysioNet review = 1–2 weeks).
