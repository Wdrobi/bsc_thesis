# P4 — Homomorphic Encryption in Healthcare Industry: Applications for Protecting Data Privacy
**J. S. Rauthan — G. B. Pant Institute of Engineering and Technology (Pauri Garhwal, India), 2024**

**Type.** Applied feasibility study / experimental case-study (not a pure survey). Benchmarks OpenFHE and TFHE-rs / Concrete-ML on two healthcare use cases (rule-based QC and NN inference), framed by short surveys of privacy-preserving techniques (pp. 6–10) and FHE generations/tools (pp. 11–14).

**Scope.** Concentrates on FHE. Schemes covered: BGV/BFV/CKKS (2nd-gen) + CGGI/TFHE + FHEW (3rd-gen) (pp. 11–13). Healthcare applications: (i) laboratory rule-based QC via Westgard Rules (pp. 17–22); (ii) NN-based medical diagnostics — basic classifier, FC image classifier (X-ray/MRI/CT tumor-detection), 40+-layer PCR test model (pp. 21–22, 29–31). EHR, IoT, wearables, telemedicine, genomics NOT explicitly handled (genetic testing in passing, p. 21).

**Regulatory context.** **GDPR only**, named on p. 3. No HIPAA/HITECH/DPDP. HE framed as remaining-compliant-with-stringent-legislation while using cloud compute; eliminates ops overhead of hash-ID + repeated re-encryption + key-distribution pipelines (pp. 4–5). **Compliance discussion is shallow** — never maps specific GDPR articles (Art. 32, Art. 9 sensitive health data) to HE properties.

**Application case studies.**
- **QC Rule 1 (binary):** decimal vec → 1-bit pass/fail. OpenFHE (CKKS+FHEW scheme-switch) and TFHE-rs (FheInt16/32). TFHE-rs wins per-op latency; OpenFHE wins via batching ≥64 (pp. 14–17).
- **QC Rule 2 (arithmetic + binary, abs):** Naïve manual abs vs optimized manual vs native `if_then_else` vs native `abs` API in TFHE-rs (pp. 18–19). OpenFHE Chebyshev approximation explored vs polynomial degree (p. 19).
- **QC Rule 3 (matrix aggregation):** row/col max/min/SD on encrypted decimal matrix; OpenFHE cannot do per-row max/min in a single batch (pp. 22–25).
- **NN Model 1 trivial:** FHE-converted, no accuracy loss, <1 s inference (p. 30, Fig. 21–22).
- **NN Model 2 FC image classifier:** Concrete-ML, small accuracy drop, ~20–30 s/inference.
- **NN Model 3 production 40+-layer PCR test:** significant accuracy drop after quantization + layer surgery, ~30 s/inference (pp. 29–31).

**HE schemes & tradeoffs.**
- BGV/BFV: lattice-based, exact integer arithmetic, slow bootstrapping (minutes).
- **CKKS:** approximate floats; ideal for ML/statistics; **batching/SIMD = OpenFHE per-result speed advantage at batch 1024 ≈ 400 ms/result, ~2× faster than TFHE-rs** in Rule 2 (p. 20).
- **TFHE/CGGI:** 3rd-gen, fast bootstrapping <0.1 s, native binary, no decimal (workaround: scale to integers up to 512 bits) (pp. 11, 15–16).
- **FHEW:** binary; in OpenFHE used as scheme-switch target from CKKS — **switch costs heavy crypto-context setup** (Fig. 5: ~100 s context setup vs TFHE-rs much lower) (p. 16).

**Performance numbers reported.**
- TFHE-rs single-op QC Rule 1 (FheInt16): ~hundreds ms for enc+compute+dec.
- OpenFHE batch=1024: per-result sub-ms encoding+enc+dec (Figs. 2–3).
- TFHE-rs native `abs`: ~0.8 s end-to-end vs >2.5 s manual branching (Fig. 7, p. 18).
- OpenFHE Rule 2, batch 1024: ~400 ms/result (p. 20).
- Crypto-context setup: OpenFHE CKKS+FHEW ~100,000 ms vs TFHE-rs FheInt16 much lower (Fig. 5, p. 17).
- QC Rule 3 opt vs naïve TFHE-rs: ~6× speedup; CPU 1011%→1476% on 16 threads (p. 21).
- NN inference: trivial <1 s; FC image and PCR ~20–30 s/inference (Fig. 22, p. 31).
- **Key/ciphertext sizes (Table 4, p. 28):** CKKS pubkey 18.9 MB, mult-key 56.6 MB, one batch ciphertext 13.6 MB; client-side memory @ batch 1024 up to ~30 GB (Fig. 20, p. 28).

**Stated limitations.**
- NN inference ~30 s/sample infeasible at millions/day (p. 32).
- Accuracy loss from CKKS approx + quantization + layer surgery (p. 31).
- Ciphertext expansion vs 4K medical images → storage/bandwidth issues (p. 32).
- No native SD/statistical primitives in FHE libraries (p. 32).
- Custom production NN architectures don't translate cleanly to FHE operators (pp. 31–32).
- OpenFHE can't slice batches → matrix-row processing forced into pseudo-parallel, memory explodes (pp. 23–24).

**Limitations I identify — for novelty hunting.**
1. **No FL component at all** — entire architecture single-client / single-server; no multi-hospital collaborative training. Cross-institutional aggregation absent.
2. **No blockchain/DLT** — no immutable audit, no consent management, no on-chain key governance; trust in server assumed via "the server is always set up in trusted zones... extra security against hardware or side-channel attacks doesn't need to be considered" (p. 9). Unrealistic for multi-tenant clouds.
3. **Threat model is HbC server only.** No malicious server, no model-inversion / MIA on FHE outputs, no client collusion, no insider threats.
4. **Key management hand-waved** — "client creates keypairs (periodically refreshed)" (p. 29) — no multi-key FHE, no threshold FHE, no proxy re-encryption beyond mention as an OpenFHE feature (p. 13), no DKG across hospitals.
5. **No scalability discussion for N hospitals.** "Bidirectional" client–server model assumes exactly two parties; does not scale to a federation.
6. **No HE-parameter optimization methodology** — ring dim, modulus chain depth, bootstrapping frequency, level budget never tuned as a function of healthcare workload; only batch and polynomial degree swept.
7. **No GPU/FPGA/ASIC acceleration evaluated** — "industry is showing interest in FHE-specific hardware" (p. 32) but no measurement.
8. **GDPR mapping rhetorical**, not operational — no Article-level mapping, no DPIA framing, no data-subject-rights workflow (right-to-erasure on encrypted data is non-trivial).
9. **No comparison vs hybrid privacy stacks** (HE+SMPC, HE+DP, HE+TEE) even though all four primitives are introduced in §1.2.
10. **No PQ parameter-choice discussion** beyond generic 128-bit floor (p. 12).

**Useful insights for our framework.**
- **Batch-size sweet spot ≈ 64–128** for CKKS in OpenFHE (gains plateau beyond) — sizes our FL client micro-batches.
- **Scheme-switching is expensive** (CKKS↔FHEW): for mixed arithmetic+comparison workloads in FL aggregation, avoid mid-pipeline switches; prefer single-scheme operators.
- **Native APIs ≫ manual implementations** — e.g., `abs` via bit-twiddling beats manual branching by 3×+. Apply to ReLU, max, comparison primitives in encrypted gradient aggregation.
- **128-bit security floor non-negotiable for industry adoption** (p. 12) — fixes our HE parameter baseline.
- **Concrete-ML chosen for scikit-learn / PyTorch-like high-level API** (pp. 13, 25) — keep our optimized-HE layer behind a familiar ML API for hospital adoption.
- **TFHE/CGGI for low-batch / binary-heavy ops** (comparisons, ReLU, decision trees), **CKKS for high-batch numeric aggregation** — informs our hybrid scheme selection per FL stage.
- **Empirically validated key/ciphertext sizes** (CKKS pubkey 18.9 MB, mult-key 56.6 MB, ciphertext 13.6 MB/batch) — concrete numbers for our bandwidth and off-chain storage analysis.
- **Parallelism gains bounded by thread count** (1476% on 16-thread CPU, p. 22) — quantitative justification for GPU/accelerator optimization claims.

**Direct relevance.** Rigorously demonstrates pure FHE is feasible for non-latency-critical healthcare workloads (statistical QC) and marginal for production NN inference (~30 s/sample), benchmarking the exact libraries (OpenFHE, TFHE-rs, Concrete-ML) we will adopt — empirically defensible parameter and tooling choices. Crucially, the paper's two-party HbC client–server scenario, hand-waved key management, "trusted server zone" assumption, and silence on federation, on-chain auditability, and multi-hospital collusion together define the precise novelty gap we fill: *retain Rauthan's HE primitives and library choices; replace single-server trust with blockchain-anchored consent + audit; replace single-client inference with cross-hospital FL; add HE-parameter and hardware-side optimizations Rauthan explicitly flags as open problems on p. 32.* Their runtime/memory numbers (Figs. 5, 6, 12, 20–22; Table 4) are a defensible baseline for quantitative-improvement claims.
