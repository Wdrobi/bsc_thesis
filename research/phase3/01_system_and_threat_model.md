# MEDUSA — Phase 3.1 (a) — System Model & Threat Model
*Formal specification of entities, trust assumptions, and adversary capabilities.*

---

## 1. System entities

| Symbol | Entity | Cardinality (target) | Function | Trust class |
|---|---|---|---|---|
| **H_i** | Hospital edge client | n ∈ {5..100}; default n=20 simulated, 3 lab GPU nodes | Local training; quantize; selectively encrypt; sign and post commit; upload ciphertext to its cluster aggregator | Honest-but-curious by default; up to f_H = ⌊(n−1)/3⌋ Byzantine |
| **R_j** | Regional cluster aggregator | k ∈ {2..8}; default k=4 | Run encrypted Multi-Krum within its cluster; emit cluster ciphertext + commit | HbC; verifiable via on-chain commits |
| **G_m** | Tier-3 consortium / global node | t-of-n threshold; default n_G=5, t=3 | Hold threshold MHE keyshare; verify commits; sum cluster ciphertexts; partial-decrypt; run NBA-CKKS scheduler; execute chaincode (HE-Shapley, slashing) | At most t−1 = 2 Byzantine (Byzantine-tolerant threshold) |
| **TSC** | Trusted Setup Coordinator | 1, one-time at federation genesis | Orchestrate distributed key generation (DKG); destroy all secrets after epoch 0; act as bootstrap CA for hospital identities | Trust required at setup epoch only; not online thereafter |
| **L** | Permissioned chain ledger | 1 logical, n_G physical orderers | Stores commits, Shapley scores, key-rotation events, slash events, model-version metadata | Liveness ≥ ⌊2n_G/3⌋ honest; safety as per BFT consensus |
| **P** | External patient/clinician | Out of scope for v1 (deferred to Phase 4 inference pipeline) | — | — |

### 1.1 Identity & key material
- Each H_i holds: long-term signing key (Ed25519) certified by TSC at genesis; ephemeral per-round encryption nonce; local CKKS evaluation key.
- Each G_m holds: threshold MHE keyshare s_m s.t. Σ_m s_m = s_global; signing key; chaincode admin cert.
- Each R_j holds: signing key; CKKS evaluation key; no secret share.

### 1.2 Communication
- **H_i ↔ R_j:** TLS 1.3, mutual-auth via X.509 certs anchored in TSC-signed root.
- **R_j ↔ G_m:** TLS 1.3 + gRPC over Fabric channel.
- **All commits / scores / events** appended to ledger L; off-chain blob store (IPFS or S3) for ciphertexts indexed by content hash committed on L.

### 1.3 Round structure (one synchronous FL round)
Phase R0 — broadcast: G_m signs and publishes (w^t, ctx^t = (N, Q, Δ)^t from NBA-CKKS).
Phase R1 — local: each H_i computes Algorithm 1 (Client_Round); posts commit C_i^t; uploads (c_i^t, ldp_i^t).
Phase R2 — cluster: each R_j runs Algorithm 3 (Encrypted_Multi_Krum); posts commit C̃_j^t; uploads C_j^t.
Phase R3 — global: G_m verify, sum into A^t; threshold partial-decrypt; chaincode executes HE-Shapley + slash/reward.
Phase R4 — schedule: NBA-CKKS scheduler (Algorithm 2) decides ctx^{t+1} and key-rotation; G_m broadcast for round t+1.

---

## 2. Trust model — formal

### 2.1 Assumptions
**A1 (Setup integrity).** At genesis epoch 0, TSC honestly runs the DKG protocol [Mouchet 2021] and securely deletes all transient secrets. No secrets persist on TSC after epoch 0.

**A2 (Threshold soundness).** At most t−1 of the n_G global nodes are corrupted simultaneously at any time. Honest majority among Tier-3 ⇒ no individual G_m can decrypt ciphertexts; ⇒ ledger safety per BFT consensus.

**A3 (Authenticated channels).** All point-to-point channels are TLS 1.3 with forward secrecy; certificates rooted at the TSC genesis CA; revocation via on-chain CRL.

**A4 (Lattice hardness).** Ring-LWE with parameters (N, Q, χ_err) is λ_lat-hard against the best known classical attacks per Albrecht's LWE estimator; default λ_lat = 128.

**A5 (Statistical IND-CPAD).** CKKS decryption follows Li-Micciancio-Schultz-Sorrell (CRYPTO 2022) noise-flooding regime with parameter λ_stat ≥ 40, achieving statistical distance ≤ 2^(-λ_stat) between ideal and real decryption transcripts.

**A6 (Bounded Byzantine fraction).** At most f_H = ⌊(n−1)/3⌋ hospitals exhibit Byzantine behavior per round (consistent with Multi-Krum's f-Byzantine tolerance [Blanchard et al. NeurIPS 2017]).

**A7 (Synchronous communication within a round).** Round timeout τ_round = 30 minutes; messages later than τ_round are dropped (treated as free-rider behaviour by Shapley contract).

### 2.2 Out of scope (v1)
- Active fault-injection inside HE library (CLKSCREW / Plundervolt-style attacks on the lattice arithmetic).
- Quantum adversaries against the LWE base (we use 128-bit *classical* lattice security; not claiming PQ-safety).
- Front-running on the public mempool of the chain (we use a permissioned consortium chain; no public mempool).
- Adversarial control of the TSC at genesis (A1 must hold).

---

## 3. Adversary models

We instantiate **five adversary profiles** that the framework must defend against. Each profile is defined by (a) corrupted entities, (b) capabilities, (c) attack goals, (d) information accessible.

### 3.1 𝓐₁ — Crypto-passive adversary (IND-CPAD)
- **Corrupts:** ≤ t−1 Tier-3 nodes; passive read of all on-chain commits and off-chain ciphertexts.
- **Capabilities:** Adaptive chosen plaintext queries; observation of decryption transcripts.
- **Goal:** Recover hospital h's plaintext gradient from any single round; or recover any keyshare s_m.
- **Defense:** Lattice-LWE λ_lat = 128; noise flooding λ_stat = 40 (Theorem 1, §3.1c); threshold MHE (A2).
- **Bound:** Distinguishing advantage ≤ 2^(-λ_stat) + negl(λ_lat).

### 3.2 𝓐₂ — Byzantine hospital adversary
- **Corrupts:** ≤ f_H = ⌊(n−1)/3⌋ hospitals; controls their local data, training, and submitted ciphertexts.
- **Capabilities:** Submit arbitrary ciphertexts (label-flip, sign-flip, additive backdoor with BadNets trigger).
- **Goal:** Degrade global model accuracy OR insert a targeted backdoor.
- **Defense:** Encrypted Multi-Krum at R_j (§3.1b, Algorithm 3); on-chain Shapley downgrade; slashing.
- **Metric:** Δaccuracy under attack ≤ ε_robust (target ε_robust ≤ 2% under 30% byzantine).

### 3.3 𝓐₃ — Membership-inference / gradient-inversion adversary
- **Corrupts:** External observer of on-chain commits + ciphertexts (no hospital, no G_m corrupted).
- **Capabilities:** Shadow-model training; DLG / iDLG / GradInversion reconstruction attempts on intercepted ciphertexts.
- **Goal:** Determine whether a specific record was in a hospital's training set (MIA) or reconstruct a training example.
- **Defense:** End-to-end CKKS encryption with IND-CPAD ⇒ ciphertexts reveal no plaintext information; reconstruction reduces to breaking 𝓐₁.
- **Metric:** MIA AUC ≤ 0.55; DLG PSNR < 14 dB.

### 3.4 𝓐₄ — Free-rider / Sybil adversary
- **Corrupts:** Spawns ν fake hospitals submitting null or copied gradients; or a single hospital submits w^{t-1} unchanged.
- **Capabilities:** Mint identities via Sybil; submit valid-format ciphertexts with low information content.
- **Goal:** Receive reward without contributing useful training signal.
- **Defense:** Identity binding via TSC genesis CA (limits Sybil); on-chain HE-Shapley scoring; below-threshold φ̂_i triggers slash.
- **Metric:** Shapley AUC for separating free-rider vs honest ≥ 0.90.

### 3.5 𝓐₅ — Collusion adversary
- **Corrupts:** Up to t−1 G_m AND up to f_H hospitals AND up to ⌊k/2⌋ R_j simultaneously, coordinated.
- **Capabilities:** Combine 𝓐₁..𝓐₄ capabilities; share intermediate signals.
- **Goal:** Recover plaintext OR steer model OR steal Shapley reward.
- **Defense:** Threshold MHE (A2 forces ≥ t honest G_m to decrypt — secrets remain hidden); on-chain commits make R_j malice publicly auditable; encrypted Multi-Krum bounds H corruption to f_H.
- **Caveat:** If t G_m AND > f_H hospitals are simultaneously colluding, the framework breaks. We claim defense up to (t-1, f_H, k/2) simultaneously.

---

## 4. Threat-model coverage matrix

| Attack class | Prior work coverage | MEDUSA defense mechanism | Measured in experiment |
|---|---|---|---|
| **CPA / IND-CPA** | P3 informal | CKKS + threshold MHE | E7 (crypto sensitivity) |
| **IND-CPAD** (Li-Micciancio'22) | P1 surveys, **none implements** | Calibrated noise flooding via Theorem 1 | E7 |
| **Lattice attack (LWE)** | P1 surveys | N ≥ N_lattice(128); Albrecht estimator | E7 |
| **Key recovery via shared decryption** (Guo USENIX'24) | P1 surveys | Threshold MHE: no single party reconstructs s | E7 |
| **Timing / cache side-channel** (Cheng SEAL Barrett) | P1 surveys | OpenFHE 1.2 constant-time arithmetic; documented, not measured in v1 | discussion |
| **Power / EM side-channel** | P1 surveys | Out of scope (no HW deployment in v1) | — |
| **Membership inference** (Yeom CSF'18) | P3 informal claim | IND-CPAD encryption → reduces to 𝓐₁ | E6 |
| **Gradient inversion** (DLG, iDLG, GradInversion) | P2 motivation | Same as MIA; no plaintext gradient ever leaves H_i | E6 |
| **Model inversion** | P3 informal claim | Threshold decryption only ever yields aggregate model | E6 |
| **Label-flipping poisoning** | None of P1–P4 tests | Encrypted Multi-Krum + Shapley slash | E6 |
| **Sign-flipping poisoning** | None of P1–P4 tests | Encrypted Multi-Krum + Shapley slash | E6 |
| **Backdoor (BadNets trigger)** | None of P1–P4 tests | Encrypted Multi-Krum; trimmed-mean fallback | E6 |
| **Sybil** | None | TSC-signed identity at genesis; per-round signing key | E6 |
| **Free-rider** | P2 incentive eq. but ill-defined | On-chain HE-Shapley contribution scoring | E6 |
| **Collusion** (≤ t−1, f_H, k/2) | None | Threshold MHE + Multi-Krum + auditable commits | E6 |
| **Denial of service on consensus** | P2 silent (Ganache) | Fabric/Quorum BFT liveness ⌊2n_G/3⌋ honest | E8 |
| **Front-running / MEV** | n/a | Permissioned chain; no public mempool | architectural |

Coverage: **17 of 17** attack classes have either a deployed defense or a documented out-of-scope justification. **9 of 17** are exercised in measured experiments (E6–E8). **4 of these 9 are not exercised by any of P1–P4.**

---

## 5. Security goals (formal)

**Goal 1 (Confidentiality):** No PPT adversary 𝓐 with capabilities ≤ 𝓐₁ ∨ 𝓐₃ recovers any plaintext gradient component or any record-level training datum, except with advantage ≤ 2^(-λ_stat) + negl(λ_lat).

**Goal 2 (Robustness):** With ≤ f_H Byzantine hospitals (𝓐₂), the global model accuracy degradation Δaccuracy ≤ ε_robust per round.

**Goal 3 (Auditability):** Every (i) hospital update, (ii) cluster aggregate, (iii) global aggregate, (iv) reward / slash event is publicly verifiable from L given (TSC genesis CA, ctx^t).

**Goal 4 (Incentive compatibility):** A rational hospital maximizes expected reward by submitting truthful gradients of its full local dataset; free-riding (𝓐₄) yields expected payoff < truthful payoff.

**Goal 5 (Liveness):** Under A6 + A7, every round completes within 2·τ_round.

These five goals map to evaluation experiments E6 (Goals 1, 2), E7 (Goal 1), and E8 (Goals 3, 5); Goal 4 is verified by the Shapley discrimination AUC in E6.
