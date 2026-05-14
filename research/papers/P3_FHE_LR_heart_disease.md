# P3 — Exploring the future of privacy-preserving heart disease prediction: a fully homomorphic encryption-driven logistic regression approach
**Naresh, Reddi — Journal of Big Data (Springer Open) 12:52, 2025**
*Sri Vasavi Engineering College & Raghu Engineering College, India. Received 10 Sept 2024; accepted 11 Feb 2025.*

**Problem.** Heart-disease ML on sensitive records has a privacy/utility trade-off. Anonymization/perturbation degrade utility; DP injects accuracy-killing noise (pp. 1–2, 4). Authors propose **HELR** — an HE-aware logistic regression — so a CSP both trains and infers on encrypted data without decrypting, while claiming resistance to poisoning, evasion, MIA, model inversion, model extraction (pp. 2–3, 14–20).

**ML model.** Binary logistic regression with sigmoid σ(w^T z) (Eq. 1, p. 6; Eq. 6, p. 14). Trained with mini-batch / full-batch GD, lr α=1, BCE + L2-style regularizer: W_j ← W_j − α·(1/P)·Σ(σ(F_i)−Y_i)·F_ij + 0.059·W_j (p. 12). Epochs {5, 10, 20, 50}. **CRITICALLY**: paper does NOT describe a polynomial approximation of sigmoid; Alg. 3 and Eqs. 12, 23–24, 28 write σ(Enc(z^T)·Enc(w)) as if sigmoid were directly homomorphic — a soundness ambiguity. Features: standard 13/14 attributes of UCI Cleveland heart-disease dataset.

**HE setup.** **CKKS** via **TenSEAL + PyTorch on Google Colab** (p. 20, Table 2):
- poly_modulus_degree N ∈ {4096, 8192}
- coeff_mod_bit_sizes = [40, 20, 40] for N=4096; [40, 21, 21, 21, 21, 21, 21, 40] for N=8192
- global scale Δ = 2²⁰ (N=4096), 2²¹ (N=8192)
- Galois keys via `ctx_eval.generate_galois_keys()` for SIMD dot products
- Multiplicative depth ≈ 1 for N=4096 (single mult level between 40-bit primes), ≈ 6 for N=8192
- **No bootstrapping** — depth refreshed by **decrypt-update-re-encrypt** each iter (Alg. 3, p. 16: "Decrypt the gradient... Update... Encrypt the updated weight vector")

**Dataset.** Three Kaggle sets (p. 22, Fig. 8): Heart (johnsmith88, 1025 rows, 14 attr); Statlog (shubamsumbria, 270 samples, 13 features); Framingham (aasheesh200, ~4240, 15 features, 10-yr CHD label). Class balance not reported. No train/test split, normalization, or imputation documented.

**Pipeline.** Training AND inference on encrypted data at CSP (pp. 9–10). Three-party (Fig. 1, p. 9): patient encrypts test record under hospital pubkey; hospital encrypts training set + initial weights, ships to CSP; CSP runs encrypted GD-LR (Alg. 3, p. 13), periodically sends encrypted updated weights back to hospital. Inference: CSP returns Enc(σ(w^T z_test)); hospital decrypts then re-encrypts under patient pubkey. **Inconsistency**: pp. 15–16 indicate gradient *decrypted by the hospital each iter*, then re-encrypted, while Alg. 3 implies fully encrypted loop — actual impl is hybrid to keep depth ≤ 1.

**Results.**
- Accuracy (heart, Fig. 6, p. 22): plain LR 85%; HELR_4096 84%; HELR_8192 84% — 1–3% gap, stable across epochs.
- AUC/ROC (Fig. 7, p. 22): best at threshold 0.8; HELR_4096 > HELR_8192 AUC.
- HESVM comparison (Fig. 8, p. 23): heart HELR 81.7/85 vs HESVM 67/79; statlog HELR 100/100 (overfit/leakage on 270 rows) vs HESVM 69/88; Framingham HELR 62/65 vs HESVM 63/61.
- Enc/compute time (p. 21, Fig. 5): train-set enc HELR_4096 1061/1093/1301/1731 ms (5/10/20/50 epochs); HELR_8192 4550/5242/5542/12225 ms. Test-set enc HELR_4096 ≈ 219–229 ms; HELR_8192 ≈ 1013–1059 ms.
- **No precision, recall, F1, ciphertext-size, key-size reported.** Table 3 only enumerates symbolic op counts.

**Baselines.** Plain LR; HESVM on the same 3 datasets; literature Table 4 (p. 23) cites Zhao et al. 2022 (BFV+DL on COVID X-rays) and Wei et al. (CKKS+LR vertical FL on MNIST). **No comparison with Chen et al. 2018 (BMC Med Genomics) or other CKKS-LR baselines.**

**Stated contributions (p. 3).** CKKS-based HE-driven LR with minimal accuracy loss; formal security analysis vs 5 attacks (Eqs. 6–29, pp. 14–20); empirical evaluation on 3 datasets showing HELR > HESVM.

**Stated limitations (pp. 1, 23, 26).** HE compute overhead; scalability to large data unproven; binary only.

**Limitations I identify.**
1. **Single-institution, single-model, no federation.** All data assumed at one hospital → one CSP. No horizontal/vertical FL, no FedAvg. Intro acknowledges FL as future work (p. 2) but does not implement.
2. **No blockchain / audit / defense against malicious CSP.** Implicit semi-honest threat model: encryption protects confidentiality but no integrity check, no verifiable computation, no consensus on updates, no defense against gradient-dropping/biasing CSP. Decrypt-step-re-encrypt loop also enables hospital-side server poisoning.
3. **Sigmoid approximation undocumented / mathematically unsound.** CKKS supports only add/mult; Alg. 3 and Eqs. 12, 23, 24, 28 write σ(·) on ciphertexts directly (pp. 13, 16, 18–19). Polynomial degree never specified (CKKS-LR typically uses degree-3 / degree-7 approx on bounded interval). Accuracy claims hard to reproduce; likely on a decrypt-eval-σ-re-encrypt loop that leaks intermediate gradients.
4. **No deep models, no non-linear ML.** Only LR (and weak HESVM baseline). Cannot extend to CNN/Transformer healthcare models without bootstrapping or much larger N.
5. **Tiny / leaky datasets.** Heart (≈1025), Statlog (270). "100% accuracy" on Statlog under both N=4096 and N=8192 (Fig. 8, p. 22) is a strong indicator of evaluation flaw (no held-out test, or trivial separation). No cross-validation, no CIs, no class-imbalance metrics on Framingham.
6. **Incomplete cryptographic reporting.** No ciphertext byte-size, key-size, security level in bits (TenSEAL defaults imply 128-bit but unstated), memory footprint. Multiplicative depth = 1 for [40,20,40] is insufficient for any non-trivial encrypted gradient step → confirms loop is not fully encrypted.
7. **Single learning rate (α=1) implausibly large** for logistic loss; 0.059 regularizer is a magic number (p. 12). Suggests insufficient HP tuning.
8. **Security "proofs" informal.** Attack-defense in §4 (pp. 14–20) restates "encryption hides w and z" but never formalizes game-based reductions or quantifies leakage from gradient/prediction queries. MIA defense (Eqs. 23–24) ignores that the decrypted prediction *is* the standard MIA oracle.
9. **No inference latency, no end-to-end throughput** — only dataset encryption times reported, not per-prediction latency (the clinician-facing metric).

**Practical insights I can reuse.**
- **Concrete CKKS starting params** for TenSEAL on tabular healthcare data: N=8192, coeff_mod=[40,21,21,21,21,21,21,40], scale=2²¹ → mult depth ≈ 6 — enough for one degree-3 sigmoid approx per gradient step. N=4096 with [40,20,40] is essentially encrypt-only.
- **Galois-key SIMD packing** via `ctx.generate_galois_keys()` — free dot-product batching across the feature axis.
- **Decrypt-step-re-encrypt** (p. 16) is a pragmatic shortcut — to be **replaced** with a bootstrapping-free, fixed-depth polynomial gradient (e.g., degree-3 sigmoid on normalized input) at each FL client, with HE used only for the aggregation tree at the server.
- **Empirical accuracy budget**: CKKS-LR on heart data costs ~1% vs plaintext at modest N — sanity ceiling for our framework's HE-induced loss.
- **Encryption-time scaling**: ~4× slower train enc N=4096 → N=8192 (1061 → 4550 ms @ 5 epochs).
- **Three-dataset test suite (Cleveland, Statlog, Framingham)** — reuse with proper stratified CV + AUPRC for imbalanced Framingham.
- **Clean attack taxonomy** (§4) — poisoning, evasion, MIA, model inversion, model extraction — lift into our security section and *extend* with a sixth axis (Byzantine FL clients) and a seventh (collusion CSP + hospital fraction) that blockchain commits defend against.

**Direct relevance to our framework.** Near-perfect "single-silo, no-FL, no-blockchain" baseline. Establishes (i) CKKS-LR viability on heart-disease tabular data with ≤3% accuracy hit; (ii) usable TenSEAL parameters; (iii) 5-attack threat model — all inherited. Weaknesses define our gap: no federation (we add FedAvg/FedProx over CKKS-encrypted updates), no defense against malicious/colluding CSP (we add permissioned BC ledger with hash-commitments of encrypted gradients), no bootstrapping or depth-aware sigmoid approx (we add explicit degree-3 polynomial sigmoid + RNS-CKKS leveled scheme with fixed depth → fully encrypted FL round without their decrypt-re-encrypt leak), no scalability story (we quantify ciphertext size, key size, per-round latency). Citation use: *"prior CKKS-LR work [Naresh & Reddi, 2025] secures a single hospital–cloud channel; we generalize to multi-hospital federated training with on-chain auditability and a depth-optimized HE pipeline, recovering their accuracy while eliminating the trusted-CSP and trusted-hospital assumptions."*
