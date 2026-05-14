# MEDUSA — Phase 3.1 (d) — Diagrams (Mermaid drafts)
*Working drafts for D1 (architecture), D2 (sequence), D3 (NBA state machine), D4 (threat coverage). Camera-ready TikZ versions to be produced in Phase 7.*

> All diagrams render in any Mermaid-aware viewer (GitHub, VS Code Mermaid plugin, `mmdc` CLI). For the paper, redraw in TikZ.

---

## D1 — 3-tier architecture
```mermaid
flowchart TB
  subgraph T1["Tier 1 — Hospital edge (n clients)"]
    H1["H_1\nGPU + CKKS-Enc\nFedProx\nQ_b · m"]
    H2["H_2"]
    H3["H_3 ..."]
    Hn["H_n"]
  end

  subgraph T2["Tier 2 — Regional cluster aggregator (k clusters)"]
    R1["R_1\nEncrypted Multi-Krum"]
    R2["R_2"]
    Rk["R_k"]
  end

  subgraph T3["Tier 3 — Global consortium (n_G nodes, t-of-n_G threshold)"]
    G1["G_1\nkeyshare s_1\nNBA-CKKS\nchaincode"]
    G2["G_2\nkeyshare s_2"]
    G3["G_3\nkeyshare s_3"]
    G4["G_4"]
    G5["G_5"]
  end

  L[("Permissioned chain L\nFabric / Quorum IBFT\nCommits · Shapley · Slash")]

  H1 -- "c_i^t, ldp_i^t (TLS 1.3)" --> R1
  H2 -- "c_i^t" --> R1
  H3 -- "c_i^t" --> R2
  Hn -- "c_i^t" --> Rk
  H1 -- "commit C_i^t" --> L
  H2 -- "commit" --> L
  Hn -- "commit" --> L

  R1 -- "C_j^t (HE-aggregated)" --> G1
  R2 -- "C_j^t" --> G2
  Rk -- "C_j^t" --> G3
  R1 -- "commit C̃_j^t" --> L
  R2 -- "commit" --> L
  Rk -- "commit" --> L

  G1 <--> G2
  G2 <--> G3
  G3 <--> G4
  G4 <--> G5
  G1 -- "BFT consensus" --> L
  G2 -- "BFT" --> L
  G3 -- "BFT" --> L
  G4 -- "BFT" --> L
  G5 -- "BFT" --> L

  L -- "w^{t+1}, ctx^{t+1}, rewards" --> H1
  L -- "broadcast" --> H2
  L -- "broadcast" --> Hn
```

**Notes on D1.**
- Solid arrows = data flow (TLS); double-arrows between G_m = consensus message exchange.
- Off-chain ciphertexts travel H_i → R_j → G_m via TLS; only commits hit L.
- The TSC is **not shown** because it is offline after genesis (epoch 0).

---

## D2 — One-round sequence diagram (R0–R6)
```mermaid
sequenceDiagram
  participant H as Hospital H_i
  participant R as Cluster R_j
  participant G as Global G_m (×n_G)
  participant L as Ledger L

  Note over G,L: Round t begins
  G->>L: R0. publish (w^t, ctx^t)
  L-->>H: broadcast (w^t, ctx^t)

  H->>H: R1. local FedProx (Alg 1, lines 02–07)
  H->>H: quantize · mask · encrypt (Alg 1, lines 08–12)
  H->>L: commit C_i^t + signature
  H->>R: upload c_i^t, ldp_i^t (TLS)

  R->>R: R2. Encrypted Multi-Krum (Alg 3)
  R->>L: commit C̃_j^t + Rej_j^t
  R->>G: upload C_j^t

  G->>G: R3. Σ_j C_j^t → A^t (Alg 4 line 04)
  par threshold partial-decrypt
    G->>G: pd_m = A^t.c₁ · s_m + e_F,m (Alg 4 lines 08–11)
  end
  G->>G: combine ≥ t partials → m̃ → Δŵ^t
  G->>L: w^{t+1} commit

  G->>G: R4. HE-Shapley (Alg 5)
  G->>L: { ρ_i^t, slash_i^t }

  G->>G: R5. NBA-CKKS schedule (Alg 2)
  alt action ≠ KEEP
    G->>L: log action, state^{t+1}
  end

  G->>L: R6. round_commit hash
  Note over G,L: Round t ends — broadcast t+1
```

---

## D3 — NBA-CKKS scheduler state machine
```mermaid
stateDiagram-v2
  [*] --> KEEP : init at genesis

  KEEP --> KEEP : margins healthy (F1, F2, F3 all OK)
  KEEP --> EVAL : end of round (Alg 2)

  EVAL --> KEEP : all margins ≥ ε
  EVAL --> SWITCH : (F3) depth_margin < ε_depth\n& (F1,F2) OK
  EVAL --> BOOTSTRAP : (F1) prec_margin < ε_prec\n→ noise budget exhausted
  EVAL --> REKEY : (F1)+(F2) jointly tight\n→ frontier crossing imminent

  SWITCH --> KEEP : drop one prime; depth_used ← 0
  BOOTSTRAP --> KEEP : refresh noise; B_residual ← B_init\n(~30–60 s cost)
  REKEY --> KEEP : DKG round; pk' ← new pk\n(~5–20 s cost)

  KEEP --> ESCALATE : no action restores feasibility
  ESCALATE --> [*] : alarm; human in the loop
```

---

## D4 — Threat-model coverage matrix (visual)
```mermaid
flowchart LR
  subgraph A["Attack classes"]
    A1["IND-CPA"]
    A2["IND-CPAD\n(LMSS'22)"]
    A3["Lattice / LWE"]
    A4["Key recovery\n(Guo USENIX'24)"]
    A5["Membership\ninference"]
    A6["Gradient inversion\n(DLG/iDLG)"]
    A7["Label-flip"]
    A8["Sign-flip"]
    A9["Backdoor"]
    A10["Sybil"]
    A11["Free-rider"]
    A12["Collusion ≤ (t-1, f_H, k/2)"]
    A13["DoS on consensus"]
  end

  subgraph D["MEDUSA defenses"]
    D1["CKKS encryption\n+ end-to-end pipeline"]
    D2["NBA-CKKS\nflooding (Thm 1)"]
    D3["N ≥ N_lattice(128, Q)"]
    D4["Threshold MHE\n(Mouchet 2021)"]
    D5["Encrypted Multi-Krum"]
    D6["On-chain commits\n+ HE-Shapley"]
    D7["BFT (Fabric/IBFT)"]
  end

  A1 --> D1
  A2 --> D2
  A3 --> D3
  A4 --> D4
  A5 --> D1
  A5 --> D2
  A6 --> D1
  A6 --> D2
  A7 --> D5
  A7 --> D6
  A8 --> D5
  A9 --> D5
  A10 --> D6
  A11 --> D6
  A12 --> D4
  A12 --> D5
  A12 --> D6
  A13 --> D7
```

---

## D5 — Round time budget (Gantt-style; planned, not measured yet)
```mermaid
gantt
    title One MEDUSA FL round (target wall-clock)
    dateFormat  X
    axisFormat  %s
    section R0 broadcast
    Publish ctx^t           :done, 0, 1
    section R1 hospitals
    Local FedProx           :h1, 1, 60
    Quantize · mask         :h2, after h1, 2
    CKKS encrypt (GPU)      :h3, after h2, 15
    Commit + upload         :h4, after h3, 3
    section R2 clusters
    Pairwise sq distances   :r1, after h4, 25
    Threshold dec distances :r2, after r1, 5
    Krum select + average   :r3, after r2, 5
    section R3 global
    Sum Σ C_j^t              :g1, after r3, 1
    Threshold partial decrypt:g2, after g1, 5
    Decode + dequantize     :g3, after g2, 1
    section R4 chaincode
    HE-Shapley sample       :s1, after g3, 50
    Mint reward / slash     :s2, after s1, 3
    section R5
    NBA-CKKS scheduler      :n1, after s2, 1
    section R6
    Round commit            :c1, after n1, 1
```

Target round wall-clock: **~3 minutes** (CPU baseline); **~45 s** with GPU CKKS (E9 ablation goal).

---

## Notes for camera-ready
- For Q1 publication, D1–D2 should be **redrawn in TikZ** with custom node shapes (chip icon for hospitals, hexagon for chain).
- D3 stays a finite-state diagram — TikZ `automata` library.
- D4 can be promoted to a **matrix table** (attack × defense × measured experiment) rather than a graph.
- D5 belongs in the Evaluation section, not the system-design section; redraw with measured numbers.
