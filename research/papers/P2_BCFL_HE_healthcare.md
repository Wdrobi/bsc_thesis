# P2 — Blockchain-based federated learning with homomorphic encryption for privacy-preserving healthcare data sharing
**Firdaus, Larasati, Rhee — Internet of Things (Elsevier) 31:101579, 2025**
*Pukyong National University (Korea), Telkom University (Indonesia), Dong-Eui University (Korea), ITB (Indonesia)*

**Problem.** Cross-silo healthcare FL — HIPAA-style silos; central aggregator = SPOF exposed to MIA, poisoning, gradient leakage. DP hurts accuracy; SecAgg leaks aggregates; MPC sync-heavy. Want decentralized FL with cryptographic privacy + auditability for cross-silo hospitals (pp. 1–2).

**Architecture (pp. 5–7).** Four entity types:
- **Users (hospitals H={h1..hn})** hold local EHR/imaging, train CNN locally, encrypt local weights ψ_h^t with HE under each hospital's pubkey (Eq. 7), upload Enc_HE(ψ_h^t) to cluster's edge server.
- **Clusters C** formed by cosine similarity of "stationary solutions" θ*_i (Eqs. 3–4) — clustered FL à la Sattler.
- **Blockchain-based edge servers E** aggregate via HE-domain weighted averaging ψ_gbl^t = Σ (n_h/N)·Enc_HE(ψ_h^t) (Eq. 9) without decrypting; consortium-blockchain nodes ARE the edge servers.
- **Trusted Authority (TA)** centrally generates and distributes keypairs for both edge servers and hospitals; authenticates hospital identities (p. 6 item viii; p. 7 init).
- **Ethereum smart contracts** store initial global model ψ_in, record encrypted update tx hashes (Eq. 8), verify model quality by prediction accuracy before aggregation (§4.2.2), compute incentives R_h^t = contribution·ψ_gbl^t (Eq. 10, Alg. 1 lines 24–33). Aggregated global redistributed; each hospital decrypts for round t+1.

**FL setup.** FedAvg with weighted averaging by n_h/N over encrypted weights. Cross-silo synchronous clustered. Clients: 2–5 per cluster (C1–C4); 5 clusters total. **10 communication rounds**, local epochs=32, batch=10, lr=0.001 (p. 11). Model: custom CNN — 6 Conv2D layers (filters 32/32/32/64/64/128, 3×3 kernels = 352 filters total), 6 MaxPool 2×2, 2 FC (128, 64), Softmax 2 classes (p. 9, §5.2).

**HE setup.** **FHE via Microsoft SEAL through Pyfhel 2.3.1** (pp. 9–10). Paper says "FHE" but never names BFV/CKKS explicitly — implicitly **CKKS** given real-valued weights. Key management: centralized TA generates all keypairs; each hospital encrypts with its own pk_h. Params: ciphertext modulus q ∈ {128, 192}, **polynomial modulus m ∈ {1024, 2048}** (Table 6, p. 13) — far below 128-bit security floor (CKKS/BFV usually m ≥ 8192). What is encrypted: the entire local model parameter vector after local training, not gradients or activations.

**Blockchain.** Ethereum smart contracts via **Ganache Truffle GUI 2.4.0** in auto-mining RPC mode (p. 10). Described as consortium blockchain (p. 7) but **no consensus algorithm is named** — Ganache auto-mining is effectively PoA. On-chain: tx hashes of encrypted updates, ψ_in, contribution records, rewards, participating hospital list. Off-chain: encrypted payloads at edge servers; only hashes on-chain. Gas price 20 gwei, gas limit 6,721,975, 100 ETH/account — Ganache defaults, not measurements. Throughput linear in epochs: Ep2=149, Ep4=290, Ep6=434, Ep8=578, Ep10=722 tx (p. 15, Fig. 9).

**Datasets (p. 9, §5.1).** (1) COVID-19 Radiography (Rahman et al.) — binary {normal, COVID}; 1000-record sample (800/200). (2) Brain Tumor MRI (Nickparvar, Kaggle) — 7023 scans; binary {no-tumor, meningioma}; 1000-record sample. Partition: manual 3 sub-schemes (100/30, 400/100, 800/200, Table 3). Heterogeneity varied across C1–C5 but **the actual non-IID strategy (Dirichlet α, label/quantity skew) is never specified**. No standard non-IID benchmark.

**Results.**
- Best accuracy: **COVID** prec 0.9735, rec 0.9725, F1 0.9725, acc 0.9725; **Brain MRI** prec 0.8837, rec 0.8625, F1 0.8606, acc 0.8625 (Fig. 5, p. 11).
- Per-cluster (homogeneous, Table 4, p. 13): best COVID at C4 (H=5) acc 0.93 F1 0.9296; brain best at C4 acc 0.8625 F1 0.8606; C1 (H=2) brain 0.7333.
- Compute time (Table 5): C1 (H=2) 1330.6 s; C4 (H=5) 2511.2 s. **Encryption dominates** (1655.7 s for C4) vs aggregation 269.5 s.
- HE sensitivity (Table 6): q=128/m=1024 → 2122.8 s; q=192/m=2048 → 5929.7 s (≈2.8× slowdown).
- Encryption ≫ Decryption (Fig. 7); exec time ~2× from homogeneous C1 to heterogeneous C5 (Fig. 8).
- 722 tx at Ep=10 — **no gas cost, no latency, no TPS reported**.

**Baselines.** Only two — Wibawa et al. 2022 [16] (HE+FL CNN COVID, acc 0.83) and Rieyan et al. 2024 [35] (FL+PHE for pituitary tumor, acc 0.8331). They beat both. **No comparison to plain FedAvg, DP-FL, SecAgg, BPFL [39], or [40].**

**Stated contributions.** Cross-silo FL minimising central server via consortium BC; HE encrypted aggregation; cosine-similarity hospital clustering; smart-contract incentives; empirical validation on two medical imaging datasets.

**Stated limitations.** Only §6 (p. 15): future work on (a) heterogeneous distribution / personalization / convergence; (b) defenses against FL vulnerabilities.

**Limitations I identify — for novelty hunting.**
1. **HE applied uniformly to ALL CNN weights every round** — no selective layer encryption, no quantization, no sparsification. Encryption alone burns 1655 s for 5 hospitals @ q=192. Massive optimization headroom.
2. **Centralized TA for keygen** contradicts the "remove central authority" claim. No threshold/multi-key HE, no DKG, no key-rotation protocol.
3. **Polynomial-modulus params (m=1024, 2048) below 128-bit security floor** for CKKS/BFV (usually m ≥ 8192). Either insecure or misuses SEAL terminology. **No mention of scale, modulus chain, level budget, or noise budget consumption per FedAvg round.**
4. **Consensus unspecified** — Ganache auto-mining is not real consensus. No PBFT/PoA/PoS evaluation; therefore no real BC throughput / finality / gas numbers. "Consortium BC" while running Ethereum/Ganache is architecturally inconsistent.
5. **No threat model and no attack experiments.** MIA, gradient inversion, label-flipping/poisoning, Sybil, free-rider, collusion are named in motivation but **never tested**. "Verification by prediction accuracy" defense is one line, never benchmarked vs Krum, trimmed-mean, Multi-Krum.
6. **Non-IID handling superficial.** Cosine-similarity clustering but no Dirichlet α; heterogeneity only degrades runtime; no personalization (FedProx, pFedMe, Ditto), no convergence analysis.
7. **Tiny scale**: max 5 hospitals/cluster, 1000 samples/dataset, 10 epochs. No scalability beyond 5 clients.
8. **Encrypted weighted avg multiplies by n_h/N under HE** — consumes multiplicative depth. No level budget or bootstrapping discussion; repeated rounds will exhaust noise budget.
9. **Single global key per hospital, but encrypted updates aggregated together** — impossible under standard CKKS/BFV unless all hospitals share one key, which the paper implies. That defeats per-hospital privacy: any hospital can decrypt another's ciphertext. **Likely a soundness bug.**
10. **Incentive equation R = contribution·ψ_gbl^t** is unitless and ill-defined — contribution measure never formalized (Shapley? data quantity? Krum score?).
11. **No communication-cost analysis** in MB/round. With m=2048 and full-model encryption, ciphertexts are large; not reported.
12. **No comparison to BPFL [39], Yang et al. [40], or other BC+HE+FL baselines** — exactly the gap they should have exploited.

**What I have to beat to publish in Q1.** Their strongest claims: (a) end-to-end working pipeline of cross-silo FL + Ethereum-stored encrypted gradient hashes + HE aggregation on two real medical imaging datasets with GitHub code; (b) accuracy gains over Wibawa (0.83 → 0.9725 COVID) and Rieyan (0.8331 → 0.8625 brain MRI); (c) clustered FL reducing aggregation overhead; (d) incentive tx recorded on-chain. To beat for Q1 I need: (i) credible HE security params (m ≥ 8192, named CKKS or multi-key HE with proven semantic security); (ii) measured attack resilience against MIA + poisoning + free-rider + gradient inversion; (iii) real consensus benchmark with TPS/finality/gas (Hyperledger Fabric PBFT or real PoA testnet, not Ganache); (iv) standardized non-IID (Dirichlet α ∈ {0.1, 0.5}) with >10 clients; (v) communication cost in MB/round and total wall-clock.

**Direct opportunities to extend/improve.**
- Replace TA with **threshold/multi-key HE or DKG** — clear Q1 differentiation.
- Use **selective / layer-wise / gradient-magnitude-based HE encryption** + report exact noise budget per round + bootstrapping strategy.
- Replace Ganache with **Hyperledger Fabric (PBFT) or Polygon/Quorum (IBFT/RAFT)**; publish real gas/TPS/latency.
- Add **Byzantine-robust aggregation (Multi-Krum, trimmed-mean, FLTrust) in the encrypted domain** and benchmark vs concrete poisoning + free-rider attacks.
- Adopt **CKKS with poly_modulus_degree ≥ 8192, 128-bit security**, document scale + level budget — beating m=1024/2048 is correctness + security claim win.
- Use **Dirichlet non-IID partitions over MIMIC-III / eICU / FLamby (FedISIC, FedTCGA-BRCA)** instead of toy 1000-sample subsets.
- Add **personalization layer on clustered FL** (pFedMe/Ditto-style heads) — addresses their stated future work.
- Hybrid **HE + DP or HE + SecAgg + ZK-proof of correct training** — closes their hand-wavy "verification by prediction accuracy" gap.
- Scale to **≥ 20 clients** + report MB/round, wall-clock vs baselines.
