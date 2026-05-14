# Cross-Paper Gap Analysis
*Synthesis across P1 (survey), P2 (BC+FL+HE empirical), P3 (HE-LR single silo), P4 (FHE benchmark)*

## 1. Method of synthesis
Each gap below is **(a) attested by at least two papers**, **(b) phrased so a Q1 reviewer can verify it from the cited evidence**, and **(c) actionable** — i.e., it points to a concrete technical move our framework can make. Gaps are ordered from highest-leverage (Q1-defining) to supporting.

---

## 2. Tier-1 gaps (Q1-defining; the headline contribution must hit ≥ 2 of these)

### G1. Noise-budget / multiplicative-depth blindness in cross-silo FL aggregation
- **Evidence.** P2 multiplies ciphertexts by n_h/N every round under "FHE" (Eq. 9) but never reports noise budget, level chain, or bootstrapping policy; the actual loop would exhaust noise after a few FedAvg rounds [P2 p. 13, Table 6]. P3 admits it sidesteps this with a decrypt-update-re-encrypt loop (Alg. 3, p. 16) — which technically negates end-to-end encryption. P1 §2.1.4 names FLHE as the "right" class but the survey provides no scheduling policy. P4 benchmarks expose ~100 s context setup for CKKS+FHEW scheme-switch (Fig. 5, p. 17) — i.e., naive re-bootstrapping is prohibitively expensive.
- **Why open.** None of P2/P3 has a principled HE-parameter selector tied to FL round count, model size, or required precision; P1 doesn't define one; P4 sweeps batch size only.
- **Move.** A **Noise-Budget-Aware CKKS Scheduler (NBA-CKKS)** that, given (FL rounds R, model dim d, sigmoid-approx depth, gradient-mag range), picks (N, coeff_mod chain, scale, bootstrap interval) to satisfy a target precision–latency frontier.

### G2. Conflict between IND-CPAD noise-flooding security and FL gradient precision
- **Evidence.** P1 p. 11 explicitly states noise flooding (the standard CKKS defense against passive secret-key recovery, per Li-Micciancio-Schultz-Sorrell CRYPTO'22) "typically [reduces precision] to 8 or 16 bits for practical parameter sets," and cites Guo et al. USENIX'24 [98] showing key recovery on OpenFHE from a single shared decryption. P2 and P3 do not invoke noise flooding at all → they are vulnerable. The survey itself flags this conflict and does not resolve it.
- **Why open.** No prior FL paper has explicitly engineered an FL-compatible noise-flooding regime (calibrated to gradient quantization).
- **Move.** Combine **quantization-aware gradient encoding** + **calibrated noise flooding** so that the post-flooding precision still meets the FL convergence bound (e.g., 8-bit gradient quantization + 32-bit noise flood headroom in CKKS [40, 21×k, 40]).

### G3. Centralized Trusted Authority for key generation — a single point of failure that breaks the decentralization claim
- **Evidence.** P2 uses a centralized TA generating all keypairs (p. 6 item viii, p. 7 init) despite advertising a "minimized central server" architecture — internal inconsistency. P3 has hospital + patient pubkeys, but only one hospital "decrypts" and re-encrypts the gradient (pp. 9–10). P4 hand-waves with "client creates keypairs (periodically refreshed)" (p. 29). P1 reviews multi-key/threshold/multi-party HE (Mouchet PETS'21 [33], Ma 2022 [52]) but no integration is proposed.
- **Why open.** No prior healthcare BC+FL+HE paper deploys threshold or multi-key HE end-to-end and benchmarks it.
- **Move.** Replace TA with a **(t,n)-threshold CKKS via Mouchet-MHE** (or distributed key generation à la Joint-Feldman) executed by the consortium blockchain nodes — keys are never reconstructed; decryption requires t-of-n signatures.

### G4. ML-layer attacks on FL never tested under the HE+BC framework
- **Evidence.** P2's motivation names MIA, gradient inversion, poisoning, Sybil, free-rider, collusion (§1, p. 1) but the entire experiments section is clean-only. P3 has informal "analyses" of poisoning/evasion/MIA/model-inversion/extraction (pp. 14–20) without an attack experiment. P1's survey treats only crypto-layer attacks (§3.x). P4 is single-tenant, so the attack surface is not even relevant.
- **Why open.** No published BC+FL+HE healthcare paper benchmarks accuracy under MIA/poisoning with HE in place; reviewers in Q1 venues (IEEE TIFS, Elsevier IoT/COMNET, Springer JBHI) consistently demand this.
- **Move.** Implement **encrypted Byzantine-robust aggregation** (Multi-Krum / trimmed-mean / FLTrust in the CKKS domain), benchmark vs label-flipping + sign-flipping + Sybil + gradient-inversion (DLG/iDLG) + MIA (ML-Doctor / Yeom 2018) attacks.

### G5. Blockchain is a glorified log; consensus, gas, TPS not measured
- **Evidence.** P2 runs on **Ganache auto-mining**, calls it a consortium chain, and never names a consensus algorithm (p. 10). No TPS, no real gas costs (only Ganache defaults), no finality latency. P1, P3, P4 have no blockchain at all.
- **Why open.** Reviewers expect realistic consensus (PBFT/IBFT/PoA) with measured throughput and gas. None of the four papers provide it.
- **Move.** Deploy on **Hyperledger Fabric (PBFT-style ordering) or Quorum (IBFT 2.0)**, publish TPS / finality / per-tx gas; make the smart contract do **algorithmic work** (Shapley-style contribution scoring, slashing, key-rotation triggers) — not just hash storage.

---

## 3. Tier-2 gaps (strong supporting differentiation)

### G6. Uniform whole-model HE encryption — no selective / layer-wise / sparsified scheme
- P2 encrypts every weight every round → encryption dominates 1655 s of 2511 s wall-clock (Table 5, p. 13). P3 encrypts the full weight vector each iter. P4 encrypts whole intermediate activations. Sparsification (Top-K), quantization-aware HE, and layer-wise sensitivity-driven encryption are absent across the corpus.
- **Move.** **Gradient-sensitivity-driven selective HE** — encrypt only layers whose gradient mutual-information leakage exceeds a per-layer threshold computed offline; transmit other layers in clear (or after DP perturbation). Combine with **Top-K sparsification before encryption** to slash MB/round.

### G7. Unrealistic non-IID modelling
- P2 partitions samples manually across 2–5 hospitals (Table 3) without Dirichlet α, label skew, or quantity skew. P3 is single-silo. P1/P4 don't run FL.
- **Move.** Use **Dirichlet(α ∈ {0.1, 0.5, 1.0}) label-skew partitioning** and **FLamby-style realistic medical splits** (FedISIC, FedTCGA-BRCA, FedHeart). Report convergence as a function of α.

### G8. No personalization / cluster-specific heads
- P2 future-works personalization (§6). Others not applicable.
- **Move.** Apply **pFedMe / Ditto / FedRep** personalization on top of cluster-level encrypted aggregation; report per-hospital accuracy gain.

### G9. Small client count, small data, short rounds
- P2: max 5 hospitals × 1000 samples × 10 rounds. P3: single silo. None tests > 20 clients.
- **Move.** Scale to **20+ simulated hospitals**, full MIMIC-III / eICU cohorts, 50–100 rounds, with wall-clock + MB/round tables.

### G10. No GPU / FPGA / accelerator path
- P1 names HW acceleration as the efficiency path (p. 22) but reviews nothing concrete. P4 admits hardware interest (p. 32) but doesn't measure. P2/P3 are CPU-only.
- **Move.** Provide a **CUDA-accelerated CKKS path** (via OpenFHE-CUDA or Microsoft EVA / SEAL-GPU forks) and benchmark encryption + aggregation latency on a single V100/A100 vs 16-core CPU.

### G11. Verifiable computation absent
- P1 cites Steffen et al. *S&P* 2022 (Zeestar — HE+ZKP for private smart contracts, p. 25) but no integration. P2/P3/P4 lack proof of correct training/aggregation.
- **Move.** Attach **succinct ZK-proofs of correct ciphertext aggregation** (zk-SNARK over the linear combination + commitment hashes, e.g., Halo2 / Plonk circuit) for *aggregation-correctness only* (not full training) — keeps proof time tractable while giving on-chain verifiable aggregation.

### G12. Communication cost untracked
- None of P2/P3/P4 reports MB/round. With CKKS pubkey 18.9 MB and mult-key 56.6 MB (P4 Table 4), this is the dominant cost in practice.
- **Move.** Always report **per-round payload in MB**, **total wall-clock**, and **per-tx on-chain bytes**.

---

## 4. Tier-3 gaps (polish / compliance / dataset realism)

### G13. Regulatory mapping is rhetorical
- P1 silent. P4 names GDPR generically (p. 3). HIPAA, HITECH, EU AI Act, Indian DPDP Act 2023 absent.
- **Move.** Map each architectural primitive to specific clauses: HIPAA §164.514 (de-identification), GDPR Art. 9 (sensitive health data), Art. 32 (security of processing), Art. 17 (right to erasure → on-chain consent revocation + re-keying).

### G14. Sigmoid / non-linear activation under HE is silently broken
- P3 applies σ on ciphertexts as if it were homomorphic (Eqs. 12, 23–24, 28) without polynomial approximation — a soundness defect.
- **Move.** Use a documented **degree-3 Chebyshev sigmoid on a bounded interval** (e.g., [-6, 6] after batch-norm) — provably HE-evaluable, with measured accuracy delta vs plaintext.

### G15. Datasets are toy
- P2 uses 1000-sample sub-samples. P3 uses 270-sample Statlog and gets 100% accuracy (overfit/leak).
- **Move.** Use **MIMIC-III/IV ICU mortality**, **eICU sepsis prediction**, **FedISIC2019 (dermatology)**, **FedTCGA-BRCA (cancer)** — large, established federated medical benchmarks.

### G16. Side-channel / implementation-attack defense never deployed
- P1 reviews extensively (§§3.1–3.3) but no prior empirical paper adopts constant-time arithmetic, DPA-resistant samplers, fault-tolerant impls, or HSM-backed key storage.
- **Move.** Use a CKKS library with **constant-time arithmetic + Gaussian sampling** (verified in OpenFHE 1.1+) and **HSM-backed (FIPS 140-2) threshold-key share storage** at edge nodes. Mention even if not measured.

### G17. Free-rider / contribution-fairness untreated
- P2 has an incentive equation (Eq. 10) but `contribution` is undefined.
- **Move.** Use **on-chain Shapley-value contribution scoring** (sampled / approximated) over encrypted updates — provides slashing/reward fairness with formal underpinnings (Ghorbani-Zou 2019 data Shapley).

---

## 5. Unique conflict the survey raises but never resolves
P1 page 11 raises a contradiction nobody has solved:
> *"For CKKS, achieving IND-CPAD security requires noise flooding, which reduces useful plaintext precision to ~8–16 bits in practical settings."*

Yet FL gradients in healthcare CNNs typically need ≥ 16–24-bit precision to converge without instability. **No prior paper reconciles these two requirements.**

Resolving this conflict (G2) with a **calibrated quantization + flooding co-design** is, on its own, sufficient for a strong Q1 contribution.

---

## 6. Cumulative gap leverage — what to attack
**Highest-leverage 5-tuple** (we should hit all five in the framework):
1. **G1 (NBA-CKKS scheduler)** + **G2 (precision/security co-design)** — the technical "we solved an open problem" angle.
2. **G3 (threshold MHE)** — kills the TA SPOF.
3. **G4 (encrypted Byzantine-robust aggregation + attack benchmarks)** — answers Q1 reviewer demands.
4. **G5 (real consensus + non-trivial smart-contract work)** — beats P2's Ganache-as-log critique.
5. **G6+G10 (selective HE + GPU path)** — communication + compute efficiency story.

Tier-2/3 gaps (G7–G17) become **ablations**, **compliance discussion**, and **deployment-realism sections** in the paper — strengthening but not headlining.
