# MEDUSA — Phase 3.1 Deliverables
*Formal system design + threat model + mathematical model + Theorem 1 + algorithms + diagrams.*

| File | Contents |
|---|---|
| `01_system_and_threat_model.md` | Entities, cardinality, trust assumptions (A1–A7), five adversary profiles (𝓐₁–𝓐₅), threat-coverage matrix (17 attack classes), five formal security goals (Goals 1–5). |
| `02_mathematical_model.md` | Notation table; CKKS preliminaries; threshold MHE (Mouchet 2021); FedProx update; quantizer Q_b; sensitivity mask m; selective encryption; encrypted Multi-Krum equations (9)–(11); global aggregation & threshold decryption (12)–(14); HE-Shapley (16)–(19); NBA scheduler state. |
| `03_nbackks_theorem1.md` | **Theorem 1 — NBA-CKKS Feasibility Frontier.** Statement, proof sketch, four corollaries including (i) worked numerical example showing Δ = 2^40 is insufficient for τ=12, λ_stat=40; (ii) formal demonstration that P2 (Firdaus 2025) cannot be IND-CPAD secure at its stated parameters; (iii) online-scheduler invariant; (iv) synergy with selective encryption. Empirical validation plan for experiment E7. |
| `04_algorithms.md` | Algorithms 0–5 with numbered lines: orchestration, hospital client round, NBA scheduler, encrypted Multi-Krum, global aggregate + threshold decrypt, HE-Shapley. Cross-references to operators in `02` and Theorem 1 in `03`. |
| `05_diagrams.md` | Mermaid drafts: D1 3-tier architecture, D2 sequence diagram, D3 NBA state machine, D4 threat coverage graph, D5 round Gantt. To be redrawn in TikZ for camera-ready. |

## What this phase establishes
1. **A precise threat model** (𝓐₁–𝓐₅) covering 17 attack classes, of which 4 are not exercised by any of the base papers P1–P4.
2. **A formal mathematical model** with 19 numbered equations operating as the mechanical core of MEDUSA — every operator from local update to on-chain Shapley is defined.
3. **Theorem 1**, a new feasibility theorem reconciling the IND-CPAD precision-vs-security conflict that P1 raises and never solves. The theorem is short, mechanically formalizable, and directly drives Algorithm 2 (the NBA-CKKS scheduler).
4. **Five numbered algorithms** ready to drop into the paper (Alg 0–5), citing the numbered equations of §2 and the inequalities of Theorem 1.
5. **Five diagrams** (Mermaid) defining the architecture, round flow, scheduler state, threat coverage, and round time budget.

## Next step — Phase 3.2 (proposed)
- **Phase 3.2a:** Formalize Theorem 1's noise-growth bound `B_L` using the empirically measured noise budget API in OpenFHE 1.2; refine the worked corollary numbers.
- **Phase 3.2b:** Define the `EncryptedValLoss` operator used in Algorithm 5 line 11 (a small encrypted neural network forward pass for loss evaluation — needs polynomial activations + careful depth budget).
- **Phase 3.2c:** Sketch the Hyperledger Fabric chaincode interface (Go) — methods `submitCommit`, `submitClusterCommit`, `runShapley`, `applySlash`, `rotateKey`.
- **Phase 3.2d:** Draft the Phase 4 module skeleton (`medusa/` Python package) — directory tree, empty modules with type-annotated stubs, pyproject.toml, requirements.txt.

Once Phase 3.2 is complete, we move to Phase 4 implementation milestone M1 (CKKS wrapper + selective encryption + quantization-aware encoder unit-tested).
