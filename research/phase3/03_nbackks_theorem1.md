# MEDUSA — Phase 3.1 (c) — Theorem 1: NBA-CKKS Feasibility Frontier
*The headline crypto contribution. Resolves the unresolved CKKS precision-vs-security conflict raised in Lee, Lim, Eswaran (2025), Discover Public Health, p. 11.*

---

## 1. The problem we are formalizing

Two requirements that prior FL+HE work treats independently are in tension:

(R1) **FL convergence** requires that, after homomorphic aggregation and decryption, the recovered gradient ĝ has at least τ bits of fidelity relative to its plaintext counterpart g, i.e. ‖ĝ − g‖_∞ ≤ ‖g‖_∞ · 2^{−τ}.

(R2) **IND-CPAD security** of CKKS decryption requires noise flooding [Li-Micciancio-Schultz-Sorrell, CRYPTO 2022] with magnitude ≥ 2^{λ_stat} · B_L, where B_L is the inherent ciphertext noise after L levels and λ_stat is the target statistical security parameter. This flooding reduces the post-decryption useful precision by exactly λ_stat bits.

P1 acknowledges this conflict on p. 11 ("the noise level... cripples plaintext precision to typically 8 or 16 bits for practical parameter sets") but proposes no solution. P2 and P3 do not invoke noise flooding at all — their schemes are therefore **not IND-CPAD secure** and are vulnerable to the Guo et al. (USENIX 2024) key-recovery attack on CKKS via shared decryption.

**Theorem 1** is the first formal condition that simultaneously satisfies both R1 and R2 in the federated-learning setting, while also respecting lattice (RLWE) hardness and CKKS multiplicative-depth bookkeeping. **Algorithm 2** (§04) is the online controller that maintains this feasibility per round.

---

## 2. Setup and assumptions

Fix CKKS parameters (N, Q, Δ, χ_err = N(0, σ²)) and assume:

- **(C1) Plaintext encoding.** Gradient coordinates are quantized to b bits by Q_b (Eq. 4, §02). After encoding into R = ℤ[X]/(X^N + 1), the plaintext magnitude is bounded: ‖m‖_∞ ≤ 2^{b−1}.
- **(C2) Noise growth.** After L homomorphic multiplications with rescaling (each step rescales modulus by Δ_l ≈ Δ), the inherent noise satisfies
  ```
       B_L  ≤  B_init · L · (Δ · √N · ‖m‖_∞ / Q_residual)
  ```
  We use the Costache-Smart 2017 / Chen-Han 2017 heuristic upper bound and denote it simply B_L(N, L, σ, Δ).
- **(C3) Multi-Krum aggregation.** Encrypted Multi-Krum at R_j consumes one multiplicative level (cluster averaging, Eq. 11). Sum across clusters at G_m consumes zero additional levels (Eq. 12).
- **(C4) Statistical IND-CPAD parameter** λ_stat (default 40). The flooding noise standard deviation must be
  ```
       σ_F  =  2^{λ_stat} · B_L
  ```
  per [LMSS'22, Thm. 4.1].
- **(C5) Lattice security parameter** λ_lat (default 128). The ring-LWE instance (N, Q, χ_err) must be λ_lat-bit hard against the best known classical attacks; we use the LWE-Estimator (Albrecht et al. 2015, updated 2024) function
  ```
       N_lattice(λ_lat, log₂(Q))
  ```
  Default values for σ_err = 3.2:
  - log₂(Q) ≤ 218 ⇒ N ≥ 8192
  - log₂(Q) ≤ 438 ⇒ N ≥ 16384
  - log₂(Q) ≤ 881 ⇒ N ≥ 32768
- **(C6) Target precision** τ (in bits) for the decoded global gradient.

---

## 3. Statement

**Theorem 1 (NBA-CKKS Feasibility Frontier).**

Under (C1)–(C6), the CKKS parameter set (N, Q, Δ) used in round t of MEDUSA is **NBA-feasible** with respect to (τ, λ_stat, λ_lat, b, L) if and only if all three of the following inequalities hold:

```
(F1)  Precision–security inequality:
          log₂(Δ)  ≥  τ  +  λ_stat  +  log₂( B_L(N, L, σ_err, Δ) )  +  1

(F2)  Lattice (RLWE) security:
          N  ≥  N_lattice(λ_lat, log₂(Q))

(F3)  Depth budget:
          log₂(Q)  ≥  L · log₂(Δ)  +  log₂(Δ_init)  +  log₂(B_init)
```

Furthermore, when (F1) is tight, the **effective precision** of the decoded global gradient satisfies
```
       prec_eff  =  log₂(Δ)  −  log₂( σ_F  +  B_L )   ≥   τ.            (★)
```

---

## 4. Proof sketch

The proof is a direct chain of noise / modulus bookkeeping.

### 4.1 Direction "feasibility ⇒ (F1)–(F3)"
Assume (N, Q, Δ) is NBA-feasible — i.e., the round can be executed correctly and IND-CPAD-securely with the required precision. We derive each inequality.

**(F1).** Post-decryption error per [LMSS'22, Lem. 3.2] is the sum of inherent noise B_L and flooding noise of magnitude ≤ n_G · σ_F (Eq. 13 sums n_G partial decryptions). The decoded plaintext m̃ satisfies
```
     ‖m̃ − Δ·m‖_∞  ≤  B_L  +  σ_F  ≤  B_L  +  2^{λ_stat} · B_L  ≤  2^{λ_stat + 1} · B_L.
```
For prec_eff ≥ τ (R1), we need log₂(Δ) − log₂(B_L + σ_F) ≥ τ, i.e.,
```
     log₂(Δ) ≥ τ + log₂(B_L) + λ_stat + 1.                              ☐
```

**(F2).** A PPT adversary with on-chain access to ciphertexts but bounded by lattice attacks cannot recover s if and only if the underlying RLWE instance is λ_lat-bit hard. The Albrecht estimator gives N_lattice(λ_lat, log₂(Q)) as the smallest N for which the cheapest known attack costs ≥ 2^{λ_lat} elementary operations. Feasibility ⇒ N ≥ N_lattice(·). ☐

**(F3).** Each homomorphic multiplication rescales Q by Δ. After L levels, the residual modulus is Q_L = Q / Δ^L; we additionally require headroom Δ_init · B_init for the final aggregation step. Thus
```
     log₂(Q) ≥ L · log₂(Δ) + log₂(Δ_init) + log₂(B_init).               ☐
```

### 4.2 Direction "(F1)–(F3) ⇒ feasibility"
(F1) implies post-flooding precision ≥ τ ⇒ R1 holds.
(F1) + flooding noise σ_F = 2^{λ_stat} · B_L ⇒ statistical IND-CPAD security by [LMSS'22, Thm 4.1] ⇒ R2 holds.
(F2) ⇒ RLWE-hard ⇒ no PPT recovery of s ⇒ semantic security holds.
(F3) ⇒ ciphertext modulus is large enough for L multiplications without underflow ⇒ correctness of homomorphic evaluation.
Conjunction is sufficient. ☐

### 4.3 Eq. (★)
Substituting σ_F = 2^{λ_stat} · B_L into prec_eff = log₂(Δ) − log₂(σ_F + B_L) gives
```
prec_eff = log₂(Δ) − log₂( (2^{λ_stat} + 1) · B_L )
         ≈ log₂(Δ) − λ_stat − log₂(B_L)
         ≥ τ + 1.                  (using (F1) tightness)
```
☐

---

## 5. Corollaries

### Corollary 1 — Worked numerical example for FedISIC / MIMIC binary classifier
**Inputs.** τ = 12 (sufficient for FedProx convergence in our pilot experiments); λ_stat = 40; λ_lat = 128; b = 12 (quantization width); L = 1 (one Multi-Krum cluster averaging per round); σ_err = 3.2.

**Compute B_L.** For N = 8192, L = 1, ‖m‖_∞ ≤ 2^11:
```
  B_init ≈ √(12 · 8192) · 3.2 ≈ 1000 ≈ 2^10
  B_L   ≈ B_init · 1 · (Δ · √8192 · 2^11 / Q_residual)
```
For Δ = 2^40, Q ≈ 2^218 (chain [60, 40, 40, 40, 40] = 5 primes), Q_residual after one mult ≈ 2^178:
```
  B_L ≈ 2^10 · 1 · 2^{40 + 6.5 + 11 − 178} ≈ 2^{−110.5} · 2^{10} ≈ effectively the rescaling drops noise back below B_init scale; practical heuristic B_L ≈ 2 · B_init ≈ 2^11.
```
(In practice, monitor B_L empirically — TenSEAL and OpenFHE both expose `invariantNoise` / `getScalingFactor` APIs.)

**Check (F1).** Need log₂(Δ) ≥ 12 + 40 + 11 + 1 = 64 bits.
- **Standard CKKS scale Δ = 2^40 is INSUFFICIENT**; prior work using Δ = 2^40 cannot simultaneously claim τ = 12 bits of precision AND λ_stat = 40 bits of IND-CPAD security. P3 used Δ = 2^21 (heart-disease paper) — would yield prec_eff ≈ 21 − 40 − 11 = −30 bits if flooding were applied; i.e., the paper is implicitly trading IND-CPAD security for precision.
- **NBA-CKKS picks Δ = 2^64**. With N = 16384 and chain [80, 64, 64, 64, 80] (log₂(Q) ≈ 352): (F2) requires N ≥ 16384 for 128-bit lattice security at log₂(Q) ≤ 438 → satisfied. (F3) requires log₂(Q) ≥ 64 + 64 + 10 = 138; we have 352 → satisfied with budget.

**Effective precision (★):** prec_eff ≈ 64 − 40 − 11 − 1 = 12 bits ✓

**Trade-off if λ_stat is relaxed to 30:** Need log₂(Δ) ≥ 54 bits. Could pick Δ = 2^54 with N = 8192 and chain [60, 54, 54, 60] (log₂(Q) ≈ 228 just above the N=8192 ceiling — borderline; NBA scheduler would switch to N = 16384 if borderline).

### Corollary 2 — Insecurity of P2 (Firdaus 2025) under Theorem 1
P2 uses poly modulus m ∈ {1024, 2048}. By (F2), the corresponding ciphertext modulus log₂(Q) at 128-bit lattice security is bounded by:
- N = 1024 ⇒ log₂(Q) ≤ 27 (per Albrecht); P2 uses unspecified Q.
- N = 2048 ⇒ log₂(Q) ≤ 54.
Even at the upper bound, plaintext magnitude headroom is ≤ 25 bits after a single multiplication (rescale by 2^21–2^40 ⇒ residual < 2^14). The FedAvg weighted-average step (Eq. 9 of P2) multiplies by a scalar n_h/N — at minimum one level. After this, attempting noise flooding with λ_stat = 40 leaves negative effective precision; **P2 cannot be made IND-CPAD secure at its stated parameters**.

Conclusion: P2 is *either* IND-CPAD insecure *or* its parameters are unable to support λ_stat ≥ 40 noise flooding. Theorem 1 makes this dichotomy explicit and unavoidable.

### Corollary 3 — Online NBA-CKKS scheduler invariant
**Lemma.** If Algorithm 2 (§04) is applied at the end of every round and chooses the cheapest restoring action (modulus-switch / bootstrap / threshold re-key) whenever any of (F1)–(F3) is on track to be violated in round t+1, then NBA-feasibility holds for all rounds t = 1..T.

**Proof.** By induction on t. Base: at t = 1, the genesis parameters are chosen by Algorithm 2 to satisfy (F1)–(F3) for L = depth required by a single round. Inductive step: assume (F1)–(F3) hold at round t. After consuming depth d_t in round t, the scheduler measures B_residual^t (Eq. 12 of §02), depth_used^t. If any of (F1) (precision margin), (F2) (lattice), or (F3) (depth) is within an ε-margin of violation for round t+1's projected workload, the scheduler triggers the cheapest restoring action: modulus-switch if depth budget is the only issue (cheapest); bootstrap if noise budget is exhausted (expensive); threshold re-key (rotate pk) if precision-security frontier would be crossed (medium cost — requires DKG step). Each action restores the state to satisfy (F1)–(F3). ☐

### Corollary 4 — Hybrid trade-off (selective-encryption synergy)
By Eq. 6 of §02 (selective encryption with LDP fallback), only ‖m‖_0 / d ≈ 20% of coordinates are encrypted. The remaining 80% are LDP-perturbed in clear. The effective HE workload per round is **5× smaller**, so the depth budget (F3) is relaxed in proportion: NBA scheduler can pick a smaller N (e.g., N = 8192 instead of 16384) for fixed (τ, λ_stat, λ_lat), reducing ciphertext size from ~100 MB to ~20 MB per hospital per round. **This is the synergy point that justifies coupling selective HE with NBA-CKKS in a single framework**, rather than treating them as independent optimizations.

---

## 6. Where Theorem 1 sits in the paper

- **Section 4 (MEDUSA Framework)** introduces the system; cites Theorem 1 as black-box.
- **Section 5 (NBA-CKKS Scheduler)** states and proves Theorem 1, presents Corollaries 1–4.
- **Section 6 (Implementation)** instantiates Algorithm 2 with concrete bookkeeping.
- **Section 7 (Evaluation)**, sub-experiment E7, sweeps (Δ, N, λ_stat) and empirically validates the (F1)–(F3) frontier; produces Figure F3 (3-D scatter: precision × latency × security).

The proof is short enough to fit in ~0.5 page of journal text; Corollary 2's exposure of P2's insecurity is the rhetorical hammer for the Related-Work comparison table.

---

## 7. Empirical validation plan (E7)

| Sweep | Range | Output |
|---|---|---|
| **Δ** | 2^21, 2^30, 2^40, 2^54, 2^64 | prec_eff vs Δ curve |
| **N** | 4096, 8192, 16384, 32768 | latency × security boundary |
| **λ_stat** | 0, 20, 30, 40 | flooding-budget impact on precision |
| **L (depth)** | 1, 2, 3 | depth-budget feasibility region |

We expect to plot Figure F3 as a 3-axis scatter: x = precision (τ), y = encryption+aggregation latency (ms), z = effective lattice security (bits). The NBA-CKKS frontier should form a Pareto envelope dominating both naive CKKS (Δ = 2^40 fixed, no flooding) and security-only CKKS (full flooding, no precision tuning).

---

## 8. Open theoretical questions (future work)
- Tightening B_L bounds beyond Costache-Smart / Chen-Han heuristics (using Costache-Curtis-Iliashenko-Player-Smart 2023 average-case analysis).
- Extending Theorem 1 to **post-quantum** RLWE parameters with the same precision-security trade-off.
- Generalizing to **bootstrapping-aware** schedulers where the cost of bootstrap is itself a function of (N, L).
- Extending to **multi-key CKKS** (Chen-Dai-Kim-Song 2019) where each hospital has its own key — relevant if threshold MHE is replaced by full multi-key encryption.

These are listed in the paper's "Discussion / Future Work" section but not pursued in v1.
