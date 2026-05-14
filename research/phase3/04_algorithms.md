# MEDUSA — Phase 3.1 (d) — Algorithms (numbered)
*Five algorithms, ready to drop into the paper. Line numbers cited from §2 of `02_mathematical_model.md` and Theorem 1 of `03_nbackks_theorem1.md`.*

---

## Algorithm 1 — `Hospital_Client_Round`
**Inputs:** global model w^t, broadcast context ctx^t = (N, Q, Δ, pk^t), threshold τ_round, local data D_i, local epochs E, learning rate η, FedProx coefficient μ, quantization width b, sensitivity mask m, LDP budget ε_LDP, hospital signing key sk_i.
**Output:** ciphertext c_i^t, LDP slice ldp_i^t, commit C_i^t, signature σ_i^t.

```
01: w_local ← w^t
02: for epoch = 1..E do
03:     for minibatch B ⊂ D_i do
04:         g_step ← ∇L_i(w_local; B) + μ · (w_local − w^t)         // FedProx, Eq. (1)
05:         w_local ← w_local − η · g_step
06:     end for
07: end for
08: g_i ← w_local − w^t                                             // local update, Eq. (2)
09: q_i ← Q_b(g_i)                                                   // Eq. (4)
10: enc_part ← m ⊙ q_i
11: clr_part ← (𝟙 − m) ⊙ q_i + LDP_noise(ε_LDP)                    // Eq. (6)
12: c_i^t   ← CKKS.Enc_{pk^t}(enc_part)                              // Eq. (7)
13: ldp_i^t ← clr_part
14: C_i^t   ← BLAKE3( c_i^t ‖ ldp_i^t ‖ i ‖ t ‖ id(pk^t) )           // Eq. (8)
15: σ_i^t   ← Sign_{sk_i}(C_i^t)
16: post-on-chain( i, t, C_i^t, σ_i^t )
17: upload-off-chain( i, t, c_i^t, ldp_i^t ) → R_{cluster(i)}
18: return (c_i^t, ldp_i^t, C_i^t, σ_i^t)
```

**Notes.**
- Plaintext local training (lines 02–07) runs on the hospital's GPU; only the gradient leaves H_i.
- `Q_b` uses a per-hospital running max ‖g_i‖_∞ as the clipping range C, refreshed every 10 rounds.
- The sensitivity mask m is precomputed once at Phase 4 M1 from a held-out membership-probe dataset (Eq. 5); refreshed if model architecture changes.
- Posting on-chain uses Fabric/Quorum chaincode method `submitCommit(round, hash, sig)`.

---

## Algorithm 2 — `NBA_CKKS_Scheduler`
**Inputs:** state^t = (N^t, Q^t, Δ^t, pk^t, B_residual^t, depth_used^t), targets (τ, λ_stat, λ_lat), projected depth L_next for round t+1, cost model `Cost(action)`.
**Output:** action ∈ {KEEP, MODULUS_SWITCH, BOOTSTRAP, REKEY_THRESHOLD}, next state state^{t+1}.

```
01: // Compute current feasibility margins per Theorem 1
02: prec_margin  ← log₂(Δ^t) − (τ + λ_stat + log₂(B_L(N^t, depth_used^t, σ_err, Δ^t)) + 1)
03: lat_margin   ← N^t − N_lattice(λ_lat, log₂(Q^t))
04: depth_margin ← log₂(Q^t) − (L_next · log₂(Δ^t) + log₂(Δ_init) + log₂(B_init))
05:
06: // Trigger logic
07: violations ← []
08: if prec_margin  < ε_prec  then violations.append("F1")
09: if lat_margin   < 0        then violations.append("F2")
10: if depth_margin < ε_depth  then violations.append("F3")
11:
12: if violations = []:
13:     return (KEEP, state^t)
14:
15: // Choose cheapest restoring action that resolves ALL violations
16: candidates ← {MODULUS_SWITCH, BOOTSTRAP, REKEY_THRESHOLD}
17: action_costs ← []
18: for action in candidates do
19:     proposed ← simulate_transition(state^t, action)
20:     if NBA_feasible(proposed, τ, λ_stat, λ_lat, L_next):
21:         action_costs.append( (Cost(action), action, proposed) )
22: end for
23: assert action_costs ≠ ∅                                          // else escalate alarm
24: sort action_costs by cost ascending
25: (_, action*, state^{t+1}) ← action_costs[0]
26:
27: // Side-effects of restoring action
28: switch action* do
29:     case MODULUS_SWITCH:
30:         drop one residual prime from Q chain; depth_used^{t+1} ← 0
31:     case BOOTSTRAP:
32:         run CKKS bootstrap (Cheon-Han-Kim-Kim-Song 2019); cost ~ minutes
33:         B_residual^{t+1} ← B_init
34:     case REKEY_THRESHOLD:
35:         G_m collectively run a fresh threshold DKG (Mouchet 2021 §4)
36:         pk^{t+1} ← new public key; old ciphertexts dropped after threshold partial-decrypt of A^t
37:         all hospitals re-encrypt next round under pk^{t+1}
38: end switch
39:
40: post-on-chain( t, action*, state^{t+1}_id )
41: return (action*, state^{t+1})
```

**Cost model defaults** (instantiated from E9 measurements):
- `Cost(KEEP) = 0`
- `Cost(MODULUS_SWITCH) = 10 ms` (cheap; just drops a prime)
- `Cost(BOOTSTRAP) = 30–60 s` per ciphertext (varies with N)
- `Cost(REKEY_THRESHOLD) = 5–20 s` (DKG + key broadcast)

`ε_prec`, `ε_depth` are margin thresholds (defaults 2 bits and 1 level respectively) to fire the scheduler *before* the next round would violate feasibility.

---

## Algorithm 3 — `Encrypted_Multi_Krum` (at R_j)
**Inputs:** ciphertext set {c_i}_{i ∈ C_j} with cluster size n_j, Byzantine bound f_j = ⌊(n_j − 1)/3⌋, data sizes {N_i}.
**Output:** cluster aggregate ciphertext C_j^t, rejected hospital set Rej_j^t.

```
01: // Phase 1 — encrypted pairwise squared distances (Eq. 9)
02: for each pair (i, i′), i < i′ do
03:     d_pair  ← CKKS.Sub( c_i, c_{i′} )
04:     d_sq    ← CKKS.Square( d_pair )                             // one mult level, batched
05:     d_acc   ← CKKS.SlotSum( d_sq )                              // SIMD reduce across slots
06:     dist_cipher[i,i′] ← d_acc
07: end for
08:
09: // Phase 2 — threshold partial-decrypt ONLY the n_j(n_j−1)/2 scalar distances
10: for each pair (i, i′) do
11:     dist_scalar[i,i′] ← ThresholdPartialDecrypt( dist_cipher[i,i′] )   // Eq. (13)–(14)
12: end for
13:
14: // Phase 3 — Krum score (Eq. 10)
15: for i in C_j do
16:     KNN_i ← argmin_{S, |S|=n_j − f_j − 2} Σ_{i′ ∈ S} dist_scalar[i,i′]
17:     KR(i) ← Σ_{i′ ∈ KNN_i} dist_scalar[i,i′]
18: end for
19:
20: // Phase 4 — Selection and weighted average (Eq. 11)
21: Selected ← argmin_{S ⊆ C_j, |S| = n_j − f_j} Σ_{i ∈ S} KR(i)
22: Rej_j^t ← C_j \ Selected
23: N_sum ← Σ_{i ∈ Selected} N_i
24: C_j^t  ← Σ_{i ∈ Selected}  CKKS.ScalarMult( c_i, N_i / N_sum )  // one mult level
25:
26: // Phase 5 — on-chain commit + rejection log
27: commit_j ← BLAKE3( C_j^t ‖ j ‖ t ‖ Selected ‖ Rej_j^t )
28: post-on-chain( j, t, commit_j, Rej_j^t )
29: upload-off-chain( C_j^t ) → G_m
30: return (C_j^t, Rej_j^t)
```

**Privacy property.** Only the *scalar distances* dist_scalar[i,i′] are decrypted, not the ciphertexts c_i themselves. The distance scalars leak a quantity related to gradient similarity but no per-coordinate information — analogous to the gradient norm leakage in cleartext Multi-Krum.

**Depth consumption.** This algorithm consumes 2 multiplicative levels per round (square + scalar mult). Theorem 1's depth budget (F3) accounts for L = 2 in the per-round projection.

---

## Algorithm 4 — `Global_Aggregate_and_Decrypt` (collective at G_1..G_{n_G})
**Inputs:** cluster ciphertexts {C_j^t}_{j=1..k}, threshold MHE secret shares {s_m}_{m=1..n_G}, threshold t.
**Output:** plaintext global update Δŵ^t.

```
01: // Phase 1 — homomorphic sum across clusters (Eq. 12)
02: A^t ← C_1^t
03: for j = 2..k do
04:     A^t ← CKKS.Add( A^t, C_j^t )                                // no level consumed
05: end for
06:
07: // Phase 2 — threshold partial decryption (Eq. 13)
08: in parallel for each G_m do
09:     e_F,m ← sample N(0, σ_F²) where σ_F = 2^{λ_stat} · B_L
10:     pd_m  ← A^t.c₁ · s_m + e_F,m   (mod Q)                       // partial decrypt
11:     sign( pd_m ); broadcast to combiner
12: end for
13:
14: // Phase 3 — public combiner (chaincode; needs ≥ t partials)
15: collect_partials({pd_m : m ∈ T}), where |T| ≥ t
16: if Shamir-threshold:
17:     m̃ ← A^t.c₀ + Σ_{m ∈ T} λ_m · pd_m  (mod Q)                  // Lagrange combine
18: else:
19:     m̃ ← A^t.c₀ + Σ_m pd_m                                       // additive combine
20:
21: // Phase 4 — decode, rescale, dequantize
22: m_decoded ← CKKS.Decode( m̃ / Δ )                                // Eq. (14)
23: Δŵ^t      ← Q_b⁻¹( m_decoded )                                   // inverse of Eq. (4)
24: return Δŵ^t
```

**Theorem 1 invariant.** Steps 09–10 add flooding noise σ_F = 2^{λ_stat} · B_L. By (F1), the post-decryption precision exceeds τ. By (F2), no adversary corrupting < t G_m can recover s. By Mouchet 2021 Thm 3.1, the protocol is semi-honest secure under RLWE.

---

## Algorithm 5 — `HE_Shapley_Round` (chaincode, executed by G_1..G_{n_G})
**Inputs:** ciphertexts {c_i}, validation ciphertext c_val (shared encrypted holdout), Monte-Carlo budget M, sub-coalition size κ, reward emission α, slash threshold φ_min, per-round budget S (number of hospitals scored this round).
**Output:** per-hospital reward ρ_i^t, slash flags slash_i^t.

```
01: // Round-robin scoring schedule
02: scored ← { H_i : (i mod (n / S)) = (t mod (n / S)) }             // S hospitals/round
03:
04: for each h ∈ scored do
05:     phi_samples ← []
06:     for l = 1..M do
07:         S_l ← uniform random subset of (H \ {h}) of size κ
08:         // Eq. (16): encrypted utility — sum sub-coalition, evaluate val loss in HE
09:         agg_S      ← Σ_{i ∈ S_l}     CKKS.ScalarMult( c_i, N_i / N_{S_l} )
10:         agg_S_plus ← Σ_{i ∈ S_l∪{h}} CKKS.ScalarMult( c_i, N_i / N_{S_l ∪ {h}} )
11:         loss_S      ← EncryptedValLoss( agg_S,      c_val )
12:         loss_S_plus ← EncryptedValLoss( agg_S_plus, c_val )
13:         score_S      ← 1 − ThresholdPartialDecrypt( loss_S )
14:         score_S_plus ← 1 − ThresholdPartialDecrypt( loss_S_plus )
15:         phi_l ← score_S_plus − score_S
16:         phi_samples.append(phi_l)
17:     end for
18:     phi_hat ← mean(phi_samples)                                   // Eq. (17)
19:     phi_var ← var(phi_samples)
20:     post-on-chain( "shapley", h, t, phi_hat, phi_var )
21:
22:     // Reward / slash (Eq. 18, 19)
23:     if h ∈ Rej_j^t for any j  OR  phi_hat < φ_min:
24:         slash_i^t ← 1
25:         apply-slash( h, amount = β · stake(h) )
26:     else:
27:         slash_i^t ← 0
28:         ρ_i^t ← α · max(0, phi_hat)
29:         mint-reward( h, ρ_i^t )
30:     end if
31: end for
32: return { (ρ_i^t, slash_i^t) : i ∈ scored }
```

**Cost / privacy notes.**
- M = 50 samples is typical; per-round Shapley cost ~ M · κ · (depth-1 HE ops) ≈ 50 · 5 · 200 ms ≈ 50 s/hospital scored. At S = 4 hospitals/round and 20 rounds, every hospital scored on average 4 times during training — sufficient for statistical free-rider discrimination.
- Only the **validation-loss scalar** is partially decrypted, not the gradient. The leakage is bounded to one scalar per Shapley sample.
- The reward / slash policy is settable per-channel via Fabric chaincode parameters.

---

## Algorithm 0 — `MEDUSA_Master_Round` (orchestration)
**Inputs:** round number t, hospitals H, clusters C, global state^t.
**Output:** new global model w^{t+1}, state^{t+1}.

```
01: // R0 — broadcast
02: G_m broadcast (w^t, ctx^t) signed by ≥ t G_m
03:
04: // R1 — hospital local round (parallel)
05: in parallel for each H_i do
06:     (c_i^t, ldp_i^t, C_i^t, σ_i^t) ← Hospital_Client_Round(w^t, ctx^t, ...)   // Algorithm 1
07: end for
08:
09: // R2 — cluster aggregation (parallel)
10: in parallel for each R_j do
11:     (C_j^t, Rej_j^t) ← Encrypted_Multi_Krum( {c_i : i ∈ C_j} )                // Algorithm 3
12: end for
13:
14: // R3 — global aggregation + threshold decrypt
15: Δŵ^t ← Global_Aggregate_and_Decrypt( {C_j^t}, {s_m} )                          // Algorithm 4
16: w^{t+1} ← w^t + Δŵ^t                                                           // Eq. (15)
17:
18: // R4 — HE-Shapley
19: ({ρ_i^t, slash_i^t}) ← HE_Shapley_Round( ... )                                  // Algorithm 5
20:
21: // R5 — NBA-CKKS schedule
22: (action^t, state^{t+1}) ← NBA_CKKS_Scheduler(state^t, ...)                      // Algorithm 2
23:
24: // R6 — commit round to chain
25: round_commit ← BLAKE3( w^{t+1} ‖ {ρ_i^t, slash_i^t} ‖ action^t )
26: post-on-chain( round_commit )
27: return (w^{t+1}, state^{t+1})
```

A round wall-clock is dominated by R1 (encryption) and R2 (Multi-Krum). All algorithms run on the GPU CKKS path in E9.

---

## Cross-references
- Algorithm 1 uses operators from `02_mathematical_model.md` Eqs. (1)–(8).
- Algorithm 2 enforces Theorem 1 (F1)–(F3) from `03_nbackks_theorem1.md`.
- Algorithm 3 uses operators (9)–(11).
- Algorithm 4 uses (12)–(15).
- Algorithm 5 uses (16)–(19).

All five algorithms together cover the **R0–R6 round structure** specified in `01_system_and_threat_model.md` §1.3.
