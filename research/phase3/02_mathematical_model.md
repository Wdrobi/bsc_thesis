# MEDUSA — Phase 3.1 (b) — Mathematical Model
*Notation, preliminaries, and the formal operators used in every round.*

---

## 0. Notation table

| Symbol | Meaning |
|---|---|
| **n** | number of hospital clients (Tier 1) |
| **k** | number of regional clusters (Tier 2) |
| **n_G, t** | global consortium nodes, decryption threshold |
| **T** | total FL rounds |
| **t ∈ {1..T}** | current round index |
| **H_i, R_j, G_m** | client / cluster aggregator / global node entities |
| **D_i** | local dataset at H_i, |D_i| = N_i |
| **w ∈ ℝ^d** | flattened model parameter vector; d ≈ 10^4–10^7 |
| **w^t** | global model at start of round t |
| **g_i^t** | local update vector at H_i, round t |
| **L_i(·)** | local empirical loss at H_i |
| **η, μ, E** | learning rate, FedProx proximal coefficient, local epochs |
| **b** | gradient quantization width in bits |
| **Q_b(·)** | b-bit symmetric quantizer with clipping |
| **m ∈ {0,1}^d** | per-coordinate selective encryption mask |
| **δ** | sensitivity threshold for selective encryption |
| **ε_LDP** | local DP budget for non-sensitive coordinates |
| **f_H** | maximum Byzantine hospitals tolerated, f_H = ⌊(n-1)/3⌋ |
| **λ_lat, λ_stat** | lattice security / statistical IND-CPAD parameters |
| **N** | CKKS polynomial-ring degree (power of 2) |
| **Q = ∏_l q_l** | CKKS ciphertext modulus, product of L+1 RNS primes |
| **Δ** | CKKS encoding scale |
| **R_Q** | ciphertext ring Z_Q[X]/(X^N + 1) |
| **s ∈ R_Q** | global secret key |
| **s_m** | m-th threshold share s.t. Σ_m s_m = s |
| **pk** | global public key |
| **B_init, B_L** | inherent noise after fresh encryption / after L mults |
| **σ_F** | noise-flooding standard deviation |
| **τ** | target plaintext precision in bits after dequantization |
| **c_i** | ciphertext of H_i's selectively-encrypted gradient |
| **C_j** | cluster aggregate ciphertext from R_j |
| **A^t** | global aggregate ciphertext |
| **φ̂_i** | Monte-Carlo Shapley estimate for H_i |
| **ρ_i** | per-round reward for H_i |
| **B_t** | residual noise-budget margin at round t |

Bold lowercase = vector; uppercase italics = ciphertext / matrix.

---

## 1. CKKS preliminaries (Cheon-Kim-Kim-Song 2017)

Plaintext space: vectors of (up to) **N/2 complex slots**, encoded into R = ℤ[X]/(X^N+1) via the canonical embedding inverse and scaled by Δ.

**Key generation.** Sample s ← χ_key (ternary). Pick a ← R_Q uniform, e ← χ_err (Gaussian, σ_err = 3.2). Set b = −a · s + e (mod Q). Public key pk = (b, a); secret key sk = s.

**Encryption of m ∈ R.** Sample u ← χ_key, e₀, e₁ ← χ_err. Output
```
  c = (c₀, c₁) = (b·u + e₀ + Δ·m,  a·u + e₁)   ∈ R_Q × R_Q
```

**Decryption.** Compute m̃ = c₀ + c₁·s (mod Q); recover plaintext m ≈ m̃ / Δ.

**Inherent noise after fresh encryption:**
```
  B_init = ‖e₀ + e₁·s + Δ·(decoding error)‖_∞  =  O( N · σ_err · ‖s‖_∞ )
        ≈ √(N · 12) · σ_err   (heuristic, Costache-Smart 2017)
```
For N = 8192, σ_err = 3.2 ⇒ B_init ≈ 990 ≈ 2^10.

**Multiplicative depth budget:** after L homomorphic multiplications with rescaling, ‖e_L‖ grows by a constant factor per level: B_L ≈ B_init · L · (Δ · √N) (loose upper bound). Each rescale drops the modulus by log₂(Δ). After L levels, the residual modulus is log₂(Q_L) = log₂(Q) − L · log₂(Δ).

**Noise-flooding decryption (Li-Micciancio-Schultz-Sorrell CRYPTO 2022)** for IND-CPAD security: at decryption, add fresh Gaussian e_F with σ_F = 2^λ_stat · B_L. Then the statistical distance between ideal and real decryption oracles is bounded by 2^(−λ_stat).

---

## 2. Threshold Multiparty CKKS (Mouchet PETS 2021)

Replaces the single secret key s with additive shares: s = Σ_{m=1}^{n_G} s_m  where each s_m is held by a distinct global node G_m.

**Distributed KeyGen (DKG, run once at genesis by TSC).** Each G_m samples s_m ← χ_key locally; jointly compute pk = (b = −a·Σ_m s_m + e, a) via secret-sharing-aware aggregation. TSC verifies and discards intermediate trapdoors.

**Partial decryption.** Given a ciphertext c = (c₀, c₁) under pk, each G_m computes pd_m = c₁ · s_m + e_F,m where e_F,m is its share of the flooding noise. Public combiner reconstructs:
```
  m̃ = c₀ + Σ_m pd_m  (mod Q)
```
which yields the same plaintext as full-key decryption, plus an aggregate flooding error e_F = Σ_m e_F,m of total magnitude n_G · σ_F.

**Threshold variant (t-of-n_G).** Use Shamir-style polynomial sharing of each s_m so that any t shares suffice to reconstruct via Lagrange interpolation; any t−1 yield no information.

**Security.** Honest-majority semi-honest model; security reduces to RLWE (Mouchet 2021, Thm. 3.1). Under A2 (at most t−1 corrupt G_m), no PPT adversary recovers s.

---

## 3. Local training operator (FedProx)

**FedProx update at H_i, round t** with local dataset D_i and starting point w^t:
```
  w_i^t  =  argmin_w  [ L_i(w) + (μ/2) · ‖w − w^t‖²₂ ]    (1)
```
solved with E local epochs of SGD with learning rate η. The proximal term μ controls client-drift under non-IID; we sweep μ ∈ {0.001, 0.01, 0.1}.

**Local update vector:**
```
  g_i^t = w_i^t − w^t   ∈ ℝ^d                              (2)
```

**Sigmoid replacement (HE-evaluable).** Wherever the model uses σ(·), we substitute a degree-3 Chebyshev polynomial approximation on the bounded interval [−B, B] (B = 6 after BatchNorm):
```
  σ̃(x) = 0.5 + 0.197 · x − 0.004 · x³                     (3)
```
‖σ̃(x) − σ(x)‖_∞ ≤ 2.4 · 10^{−3} on [−6, 6]. We replace the model's last-layer activation and any internal sigmoid; ReLU stays in plaintext (only the encrypted aggregation pipeline needs HE-evaluable ops).

---

## 4. Quantization & selective encryption

**Symmetric b-bit quantizer with clipping range C:**
```
  Q_b(x) = clip(round( x · (2^{b-1} − 1) / C ), −2^{b-1}+1, 2^{b-1}−1)  · C / (2^{b-1}−1)   (4)
```
Default b = 12, C = max over a calibration batch of ‖g_i‖_∞.

**Selective encryption mask m ∈ {0,1}^d.** Layer-l sensitivity s_l is precomputed offline by estimating the mutual information between gradients of layer l and a held-out membership-inference probe (per Geiping et al. 2020 §4):
```
  s_l = Î(g_l ; Z_membership)     (Hutter-Sayre estimator)               (5)
```
Mask: m_l = 1 if s_l > δ else 0; δ chosen so that ‖m‖_0 ≈ 0.2 · d (top-20% sensitive coordinates encrypted; remainder DP-perturbed).

**Selective gradient with LDP fallback:**
```
  ĝ_i^t  =  m ⊙ Q_b(g_i^t)  +  (𝟙 − m) ⊙ ( Q_b(g_i^t) + n_LDP )           (6)
```
where n_LDP is per-coordinate Laplace noise with scale b · Δ_sens / ε_LDP (ε_LDP = 8, weak local-DP for non-sensitive coordinates only, used as a backstop).

**Ciphertext payload of H_i:**
```
  c_i^t  =  CKKS.Enc_{pk^t}(  m ⊙ Q_b(g_i^t)  )                            (7)
```
plus clear-text ldp_i^t = (𝟙 − m) ⊙ (Q_b(g_i^t) + n_LDP) sent alongside.

**Commit** (posted on chain):
```
  C_i^t = H( c_i^t  ∥  ldp_i^t  ∥  i  ∥  t  ∥  pk^t_id )                   (8)
```
H = BLAKE3.

---

## 5. Encrypted Multi-Krum at R_j (Algorithm 3 in §04)

Let {c_i}_{i ∈ C_j} be the ciphertexts in cluster j, |C_j| = n_j. With Byzantine bound f_j ≤ ⌊(n_j − 1)/3⌋:

**Step 1 — encrypted pairwise squared distance.** For every i ≠ i′ in C_j:
```
  d_{i,i′}  =  Σ_l (c_{i,l} − c_{i′,l})²                                    (9)
```
Computed slot-wise in CKKS (one homomorphic subtract + one homomorphic square per slot, batched across slots via SIMD).

**Step 2 — partial-decrypt distances only.** Threshold-decrypt the d_{i,i′} (small integers, low precision needed) — *not* the c_i themselves. Yields scalar s_{i,i′} per pair.

**Step 3 — Krum score for client i:**
```
  KR(i) = Σ_{i′ ∈ KNN_{n_j − f_j − 2}(i)} s_{i,i′}                          (10)
```
where KNN_k(i) is the set of k closest neighbours of i (smallest s_{i,i′}).

**Step 4 — cluster aggregate.** Choose the n_j − f_j hospitals with smallest KR(·); average their ciphertexts with their data-size weights:
```
  C_j^t  =  Σ_{i ∈ Selected_j}  (N_i / Σ_{i′∈Selected_j} N_{i′}) · c_i^t     (11)
```
This consumes **one multiplicative level** (the scalar multiplication N_i/N_sum) — included in the depth budget L of Theorem 1.

**Rejected hospitals** are recorded on-chain; repeated rejection over a sliding window triggers Shapley slash.

---

## 6. Global aggregation & threshold decryption

```
  A^t  =  Σ_{j=1}^{k}  C_j^t                                                (12)
```
Pure homomorphic addition; no level consumed.

**Threshold partial decryption** (each G_m, in parallel):
```
  pd_m^t  =  (A^t).c₁ · s_m  +  e_F,m                                       (13)
```

**Public combine (chaincode):**
```
  Δw^t  ≈  (A^t).c₀ + Σ_m pd_m^t   /   Δ                                    (14)
```
where the division by Δ is the standard CKKS rescale to recover the plaintext gradient. After dequantization (inverse of (4)) we obtain the global update Δŵ^t.

**Global model step:**
```
  w^{t+1}  =  w^t + Δŵ^t                                                    (15)
```

---

## 7. On-chain HE-Shapley contribution scoring

We use Monte-Carlo data Shapley (Ghorbani-Zou ICML 2019) with M sub-coalition samples per scored hospital. For hospital H_i in round t:

**Sampling.** Draw M random sub-coalitions S_l ⊂ {H} \ {H_i}, |S_l| = κ (κ = ⌈n/4⌉ default).

**Encrypted utility function.** Let `score(S, t)` denote 1 − (encrypted FedProx validation loss on a shared validation ciphertext after aggregating the gradients of S):
```
  score(S, t) = 1 − L̂_val( Σ_{i ∈ S} (N_i / N_S) · c_i^t )                  (16)
```
where L̂_val is evaluated under partial threshold decryption of *only the loss scalar*, not the gradient.

**Shapley estimate:**
```
  φ̂_i^t  =  (1/M) · Σ_{l=1}^{M}  [ score(S_l ∪ {H_i}, t) − score(S_l, t) ]   (17)
```

**Reward / slash rule:**
```
  ρ_i^t  =  α · max(0, φ̂_i^t)                                               (18)
  slash_i^t = 1   if  φ̂_i^t < φ_min  or  H_i was Krum-rejected             (19)
```

α is a per-round emission constant set by chaincode policy; φ_min = 0.

To bound on-chain cost, the chaincode rotates scoring: in round t, only hospitals with id ≡ t (mod n / S) are scored, where S is the per-round Shapley budget (default S = 4 hospitals/round).

---

## 8. NBA-CKKS scheduler state

Carried forward across rounds:
```
  state^t  =  (  Q^t,  Δ^t,  N^t,  pk^t,  B_residual^t,
                 depth_used^t,  bootstrap_count^t,  rekey_count^t  )
```

State transitions are governed by **Algorithm 2** (§04). The selection invariant is:

**Definition (NBA-feasibility).** The state^t is NBA-feasible iff (Theorem 1, §03):
- (F1) **Precision–security:** log₂(Δ^t) ≥ τ + λ_stat + log₂(B_L) + 1
- (F2) **Lattice security:** N^t ≥ N_lattice(λ_lat, log₂(Q^t))
- (F3) **Depth budget:** log₂(Q^t) − depth_used^t · log₂(Δ^t) ≥ log₂(Δ^t) + log₂(B_init) (room for one more level)

If any of (F1)–(F3) is violated at round t, Algorithm 2 fires the cheapest restoring action: modulus-switch, bootstrap, or threshold re-key.

---

## 9. Communication & computation complexity (per round)

Let d be the model dimension, n the client count, k the cluster count, n_G the threshold-node count.

| Component | Bytes / round | Time / round |
|---|---|---|
| H_i → R_j ciphertext c_i | 2 · ⌈d/(N/2)⌉ · 2N · log₂(Q) / 8 | O(d / (N/2) · L_mult_enc · T_NTT) |
| H_i → chain commit C_i | 32 | O(d) hash |
| R_j → G_m cluster ciphertext C_j | same as c_i | O(n_j² · d / (N/2)) for encrypted Krum |
| G_m partial decrypt | small | O(d / (N/2) · L_ntt) per G_m |
| Chaincode Shapley | O(M · κ · d) | O(M · κ · L_score) |
| Total bytes on-chain / round | n · 32 + k · 32 + O(S · log₂ d) | — |

For N = 8192, log₂(Q) ≈ 200, d = 10^6 ⇒ ciphertext ≈ ⌈10^6/4096⌉ · 16384 · 25 ≈ 100 MB / hospital / round. With Top-20% selective encryption: ≈ 20 MB. With Top-K sparsification ablation (k=1%): ≈ 1 MB.

This complexity is dominated by *encryption + Multi-Krum pairwise squared distances*. The GPU CKKS path (E9) measures the actual constants.

---

## 10. Summary of operators

| Symbol | Eq. | Operator |
|---|---|---|
| (1) | FedProx local optimization |
| (2) | Local update vector |
| (3) | Chebyshev sigmoid replacement |
| (4) | Symmetric b-bit quantizer |
| (5) | Layer sensitivity (MI estimator) |
| (6) | Selective gradient with LDP fallback |
| (7) | Hospital ciphertext payload |
| (8) | Commit hash |
| (9)–(11) | Encrypted Multi-Krum at R_j |
| (12) | Global ciphertext aggregate |
| (13)–(14) | Threshold partial / combined decryption |
| (15) | Global model step |
| (16) | Encrypted Shapley utility |
| (17) | Monte-Carlo Shapley estimate |
| (18)–(19) | Reward / slash rule |

These operators are the **mechanical core of MEDUSA**. Theorem 1 (§03) ties (1)–(15) to the lattice-security and IND-CPAD constraints they must satisfy.
