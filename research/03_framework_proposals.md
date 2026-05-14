# Three Candidate Novel Frameworks
*Each proposal addresses ≥ 4 Tier-1 gaps from `02_gap_analysis.md`. After full description, §4 recommends one.*

---

## Proposal A — **HEPHAESTUS**
### Hierarchical Encrypted Federated Healthcare AI with Threshold-Decrypted SNARK-Audited Stack
**Tagline:** *FL + threshold HE + ZK-attested aggregation on a permissioned chain.*

### Core idea
Replace the centralized TA with **(t,n)-threshold CKKS via Mouchet-style multiparty HE** (DKG executed by the consortium nodes themselves). Aggregation correctness is proven on-chain with a **zk-SNARK over the encrypted-domain linear combination**, so a hospital can verify the aggregator did not drop / bias its update without decrypting anyone's ciphertext.

### Architecture (4 layers)
1. **Hospital clients (edge):** local plaintext training → degree-3 Chebyshev sigmoid → 8-bit quantization → CKKS encryption under the shared threshold pubkey.
2. **Aggregator nodes (consortium BC peers, e.g., 5 nodes):** Hyperledger Fabric ordering service; each peer performs partial aggregation; final aggregate published on-chain alongside a Halo2/Plonk SNARK attesting `aggregate = Σ w_i · Enc(grad_i)` for the published weights w_i.
3. **Threshold-decryption committee:** any t-of-n peers collaboratively partial-decrypt the aggregate; reconstructed by the next-round broadcaster only.
4. **Audit chain:** Fabric channel storing tx{round, hospital_id, ciphertext_commit, SNARK_proof, contribution_score}.

### Gaps addressed
- G3 (TA killed), G4 (SNARK + encrypted Multi-Krum), G5 (Fabric + non-trivial SC work), G11 (verifiable computation), G16 (HSM-backed shares).

### Strengths
- **Cryptographically strongest** of the three.
- Clean Q1 story: "first FL + threshold HE + zk-SNARK aggregator for healthcare."
- Threshold HE neutralizes the Guo et al. CKKS key-recovery attack P1 cites.

### Weaknesses / risks
- **SNARK over CKKS aggregation is heavy** — Halo2 prover time for a 10⁶-parameter model could be minutes/round. Mitigation: prove only the linear combination, not bootstrapping or training; use Plonk with custom gates for SIMD.
- Heavy plumbing — threshold DKG + SNARK circuit + Fabric chaincode all in one paper risks reviewer fatigue.
- Less direct attack on the noise-budget / precision conflict P1 raises (G1, G2 are *enabled* but not *headlined*).

---

## Proposal B — **MEDUSA**  ⭐ recommended (see §4)
### Modulus-aware Encrypted Decentralized Hospital Analytics with Edge–Cloud Split FL and On-Chain Shapley
**Tagline:** *The first FL framework with a noise-budget scheduler that solves CKKS's precision/security conflict in cross-silo healthcare.*

### Core idea
Make HE *scheduling itself* the headline novelty. Introduce **NBA-CKKS** (Noise-Budget-Aware CKKS), an online controller that:
- Tracks the residual noise budget per ciphertext.
- Decides per round whether to (a) keep the current level, (b) modulus-switch, (c) bootstrap, or (d) re-encrypt under a fresh key-share at the threshold committee.
- Co-calibrates **quantization width × noise-flooding magnitude** to keep precision ≥ τ bits *and* IND-CPAD security ≥ 128 bits (resolves the P1 p. 11 conflict).

The framework also introduces **On-chain HE-Shapley contribution scoring** — an approximate Shapley value over each hospital's encrypted update is computed by sampling sub-coalitions of size k, aggregating in the HE domain, and recording each evaluation as an on-chain commitment. Free-riders are slashed; honest contributors rewarded.

### Architecture (3 tiers)
1. **Tier 1 — Hospital edge (n hospitals):** GPU-accelerated CKKS encryption (OpenFHE-CUDA); local FedProx (μ proximal term to bound client drift under non-IID); selective layer-wise encryption (gradient-sensitivity > δ → CKKS, else DP-LDP-perturbed cleartext).
2. **Tier 2 — Regional cluster aggregator (k clusters formed by FLamby-style demographic similarity):** runs **encrypted Multi-Krum + trimmed-mean**; emits cluster aggregate ciphertext.
3. **Tier 3 — Global coordinator (consortium BC, 5–7 nodes, Hyperledger Fabric or Quorum IBFT 2.0):** runs NBA-CKKS scheduler, threshold-decrypts the cross-cluster aggregate, signs the global model commit; smart contracts perform HE-Shapley scoring + slashing + key-rotation triggers.

### Gaps addressed (Tier-1: 5/5, Tier-2: 6/6)
- **G1** ✅ NBA-CKKS scheduler is the headline.
- **G2** ✅ Quantization × flooding co-calibration explicitly resolves P1 p. 11.
- **G3** ✅ Threshold CKKS keyshares at Tier 3 nodes; no TA.
- **G4** ✅ Encrypted Multi-Krum + benchmarked against MIA / DLG / label-flip / Sybil / free-rider.
- **G5** ✅ Quorum IBFT 2.0 (or Fabric) with HE-Shapley smart contract = real BC work.
- **G6** ✅ Layer-wise selective encryption.
- **G7** ✅ Dirichlet non-IID + FLamby benchmarks.
- **G8** ✅ Optional pFedMe heads per hospital.
- **G9** ✅ Scale to 20+ hospitals.
- **G10** ✅ CUDA-accelerated CKKS path benchmarked.
- **G11** ⚪ Optional — can attach Pedersen-commitment proofs without full SNARK.
- **G12** ✅ MB/round + on-chain bytes always reported.

### Strengths
- **Solves an explicitly open conflict P1 raises** → clean Q1 framing.
- Blockchain does **real algorithmic work** (HE-Shapley + slashing) — most BC+FL papers fail this test.
- 3-tier matches **actual hospital IT** (edge GPU at hospital → regional aggregator → cloud coordinator), so deployable and reviewable.
- Each headline contribution has a **separable ablation** (NBA-CKKS, Multi-Krum, HE-Shapley, layer-wise encryption, GPU path), giving the paper 5+ ablation experiments — strong evaluation surface.
- Absorbs the strongest pieces of A (threshold HE) and C (selective encryption) without their fragility.

### Weaknesses / risks
- HE-Shapley is expensive; the paper needs a tight approximation budget (Monte-Carlo with m=50 sub-coalitions per hospital).
- 3-tier means more moving parts; mitigated by clean module boundaries.

---

## Proposal C — **PHOENIX**
### Privacy-preserving Hybrid On-chain Encrypted Networked Inference & eXchange for Healthcare
**Tagline:** *Two-phase framework — communication-efficient encrypted FL training + patient-consent-NFT-gated encrypted inference.*

### Core idea
Cut **communication** rather than computation. Phase 1: encrypted FL training with **Top-K sparsified gradients packed into a single CKKS ciphertext** (SIMD slot packing reduces MB/round by >10×). Phase 2: **inference-as-a-service** via **proxy re-encryption (PRE)** so a patient's encrypted record can be evaluated against the federated model without revealing either to the hospital or to the cloud; consent is anchored as **on-chain NFTs** (one NFT per patient × purpose × time-window), and right-to-erasure triggers re-keying.

### Architecture
- Hospital clients run local training, sparsify gradients (keep top 1–5% by magnitude), pack into a single ciphertext via Galois rotations, push to BC-mediated aggregator.
- Aggregator merges sparsified ciphertexts.
- Inference: patient encrypts record under their pubkey → PRE re-encrypts under model pubkey at the aggregator → encrypted prediction sent back to patient pubkey for decryption.
- Consent NFTs (ERC-721 variants on Quorum) gate every PRE delegation; revocation triggers BC-mediated re-encryption of the federated model under a fresh key.

### Gaps addressed
- G6 (sparsification), G12 (MB/round headline), G13 (operational GDPR mapping via NFTs), G3 (PRE replaces TA), partial G2.

### Strengths
- **Patient-centric narrative** plays well in healthcare informatics journals (JBHI, JMIR).
- Operational GDPR Art. 17 story.
- Sparsified encrypted FL is genuinely under-explored.

### Weaknesses / risks
- **Two phases dilute focus** — papers covering both training + inference + consent often get hit with "split into two papers" reviewer comments.
- PRE in CKKS is non-trivial (no standard library has it production-grade); we'd lean on Polyakov's PALISADE PRE primitives which are not robustly supported in current OpenFHE.
- Doesn't directly address NBA-CKKS / G1 / G2.

---

## 4. Recommendation — adopt Proposal **B (MEDUSA)** with one absorption from A
### Reasoning
| Criterion | A (HEPHAESTUS) | **B (MEDUSA)** | C (PHOENIX) |
|---|---|---|---|
| Solves an explicitly open problem P1 raised | partial | **full (G1+G2)** | partial |
| Blockchain does real algorithmic work | yes (SNARK verification) | **yes (HE-Shapley + slashing)** | partial (NFT gating) |
| Q1 reviewer appetite (TIFS / IoT-J / FGCS / JBHI) | high but heavy plumbing | **high, multi-axis evaluation** | medium, narrative risk |
| Implementation risk in 6–9 months | high (SNARK circuit) | **moderate** | high (PRE-CKKS) |
| Ablation surface | 3 | **5+** | 3 |
| Beats P2 head-to-head | yes | **yes, on more axes** | partially |
| Patient-facing GDPR story | weak | adequate | strong |

**MEDUSA is recommended** because:
1. The **NBA-CKKS scheduler** is a clean, mechanically formalizable contribution that *directly answers a problem P1 raises and never solves* — Q1 reviewers love this framing.
2. **HE-Shapley + slashing** turns blockchain into a load-bearing component instead of a glorified log — eliminates the most common BC+FL reviewer complaint.
3. **3-tier edge–regional–global** matches real hospital topologies (deployment story) and gives **5+ ablation knobs** for evaluation.
4. The framework absorbs the best of A (**threshold CKKS at Tier-3 nodes**) and C (**optional Top-K sparsification as an ablation lever**) without their technical fragility.
5. Implementation risk is the most contained: TenSEAL/OpenFHE for HE, FedProx in Flower, Hyperledger Fabric or Quorum for BC, optional CUDA path via OpenFHE-CUDA. All open-source, none speculative.

### One absorption from A
Take A's **(t,n)-threshold MHE via Mouchet's protocol** and use it at MEDUSA Tier-3 nodes (DKG run once at federation setup; partial decryption only by t-of-n quorum). This kills G3 cleanly without committing us to a full SNARK circuit (which can be left as a "future work / orthogonal extension" paragraph in the discussion).
