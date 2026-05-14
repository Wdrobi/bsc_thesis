# P1 — A Comprehensive Survey on Secure Healthcare Data Processing with Homomorphic Encryption: Attacks and Defenses
**Lee, Lim, Eswaran — Discover Public Health (Springer), 2025, vol. 22, art. 137, DOI 10.1186/s12982-025-00505-w**
*Curtin University Malaysia. Received 27 Sept 2024; accepted 17 Mar 2025.*

**Type:** Survey / narrative review (no new experiments; explicitly: "No datasets were generated or analysed", p. 24).

**Scope & taxonomy.** Four HE families — PHE (RSA, Paillier, Benaloh, ElGamal, GM), SHE (BGN, early Gentry'09), FHE (Gentry'09, DGHV, BGV, FV/BFV, GSW, TFHE, CKKS, FHEW, HElib), Fully Leveled HE for ML (pp. 3–5, Tables 1–2). Healthcare domains: EHRs, genomic data, MRI/CT/X-ray, privacy-preserving ML, secure FL, clinical trials, telehealth (§3.1–3.7, pp. 6–7).

**Threat model & attacks.** Three perspectives (pp. 7–8): historical/implementation — timing (Kocher; Cheng cache-timing on SEAL Barrett mult, p. 8), power (SPA/DPA/CPA, SEAL v3.2 Gaussian sampler, AES-128 CPA 10k traces, p. 9), EM (Fox-IT AES-256 break, 5 min @ 1m, p. 9); scheme-based — lattice attacks (LWE, LLL, BKZ, hybrid; pp. 19–21, Tables 5–7); algorithm-based — fault injection (CLKSCREW, Plundervolt, instr skip, pp. 17–18, Table 4) and key recovery (Guo's CKKS attack on OpenFHE via shared decryption, NTRU-based adaptive key recovery, IND-CPAD, p. 11). Also CCA1/CCA2, KPA, CPA/CPA2 (pp. 12–17).

**Defenses.** Constant-time programming (Almeida et al.; Spectre-era foundations, p. 9); noise injection & DPA-resistant ECC coprocessor (p. 10); shielding/isolation & tamper-resistant HW; noise flooding (Li-Micciancio-Schultz-Sorrell, p. 11); key escrow / split keys / homomorphic secret sharing; HSMs (FIPS 140-2); PQC (lattice, code-based); CCA-secure HE via constrained HE, randomisation, hybrid (HE+ZKP, HE+digital signatures), functional encryption; ciphertext randomisation; homomorphic signatures / MACs / authenticated HE (p. 13); dynamic keys, rotation, anonymisation, secure SDLC (p. 15); fault-resistant impl with redundancy & sensors (p. 18); larger lattice dim, NIST PQC params (pp. 21–22).

**Key insights for FL+BC+HE design.**
- **FLHE** is the right HE class for FL: layered NN structure matches leveled HE; avoids full bootstrapping (p. 5; §3.5, p. 7).
- "Nearly every SHE scheme proposed thus far has been susceptible" to adaptive key recovery; SHE is **not** CCA1-secure (p. 11) — hybrid designs must not depend on SHE-only safety under collusion.
- **IND-CPAD security for CKKS** requires noise flooding, which cripples precision to "typically 8 or 16 bits for practical parameter sets" (p. 11) — direct constraint on FL gradient aggregation precision.
- **Guo et al. CKKS attack** recovers OpenFHE secret key from "just one shared decryption output" (p. 11) — critical for multi-key / threshold-decrypted FL aggregation.
- **Hybrid cryptography (HE + SMPC + DP + ZKP)** explicitly endorsed (pp. 13, 22) — supports combining HE with blockchain attestations / zk-proofs of correct aggregation.
- **Side-channel leakage documented inside real HE libraries** (SEAL Barrett mult, SEAL v3.2 Gaussian sampler, TFHE) (pp. 8–9): blind library choice is not a defense.
- Ref [58] **Kumar et al. 2022** (Comput Med Imaging Graph) already pairs blockchain+HE for medical-image model aggregation (p. 25) — confirms hybrid is publishable but novelty must come from optimisation or threat coverage.

**Authors' admitted limitations** (Sec. 5, pp. 22–23): HE compute overhead/latency; PQ security still open; hybrid (HE+SMPC+DP) needed; scalability for large data; poor usability for non-cryptographers.

**Gaps I identify (for novelty hunting).**
1. **No quantitative comparison whatsoever** — no ciphertext sizes, no ms/operation, no FL round-time benchmarks. Purely descriptive.
2. **FL treated in a single short subsection** — gradient inversion, MIA, model inversion, backdoor/poisoning, Byzantine clients never mentioned, even though they dominate FL threat models.
3. **Blockchain integration absent from the body** despite citing prior art ([58], [70]) — no discussion of on-chain key management, smart-contract aggregation, or consensus-layer attacks vs. HE.
4. **No threat model for multi-key/threshold/multi-party HE** in cross-silo healthcare FL, despite citing Mouchet's MHE ([31, 33]).
5. **No HE accelerator / GPU / FPGA side-channel coverage**, although hardware acceleration is named as the efficiency path (p. 22).
6. **Regulatory/compliance angle missing** (HIPAA, GDPR, IND-CPAD vs. "pseudonymisation").
7. **Composability of defenses unanalysed**: e.g., noise flooding directly conflicts with the precision CKKS needs for FL gradient aggregation — survey lists both but never reconciles them.
8. **"Optimised HE" named as a goal** (p. 22) but no concrete optimisation taxonomy (SIMD/batching/CRT/RNS/modulus-switching/bootstrapping-cost).

**Performance numbers reported.** Almost none. Only second-hand: AES-256 EM break 5 min @ 1m (p. 9); CPA AES-128 FPGA 10k traces (p. 9); DPA-resistant ECC coprocessor 50% FPGA / 36% ASIC gain (p. 10); IND-CPAD noise flooding limits CKKS precision to 8–16 bits (p. 11). No HE throughput/latency/key-size measured.

**Datasets mentioned.** None used. Domains: EHRs, genomic/GWAS, MRI/CT/X-ray, wearables, clinical trials (pp. 6–7). COVID-19 detection cited via Wibawa [65].

**Citations to follow up.**
- Froelicher et al., *Nat Commun* 2021 [14] — multiparty HE for federated precision medicine.
- Kumar et al., *Comput Med Imaging Graph* 2022 [58] — blockchain + HE for medical-image FL.
- Zhang et al., *IEEE TNSE* 2022 [59] — HE-based privacy-preserving FL for IoT healthcare.
- Hijazi et al., *IEEE IoT J* 2023 [63] and Xie et al., *IEEE IoT J* 2024 [64] — efficiency optimisation in HE-FL (Xie is a survey on this).
- Ma et al., *Int J Intell Sys* 2022 [52] — multi-key HE for privacy-preserving FL.
- Guo, Nabokov, Suvanto, Johansson, *USENIX Sec* 2024 [98] — key-recovery on CKKS w/ non-worst-case noise flooding.
- Li & Micciancio, *EUROCRYPT* 2021 [128] and Li-Micciancio-Schultz-Sorrell, *CRYPTO* 2022 [101] — IND-CPAD / DP-secured CKKS.
- Mouchet et al., *PETS* 2021 [33] and EPFL thesis [31] — multiparty HE from Ring-LWE.
- Reddi et al., *IEEE TII* 2024 [34] — FHE + IOTA + masked authenticated messaging for EMR.
- Steffen et al., *IEEE S&P* 2022 [113] (Zeestar) — HE + ZKP for private smart contracts.
- Cheon, Son, Yhee 2022 [158] — practical FHE parameters against lattice attacks.
- Bergamaschi et al. *ePrint* 2024/424 [157] — revisiting noise-flooding security.

**Direct relevance to our hybrid framework.** Use as the **canonical threat-landscape backbone**. Cite as the 2025 attack-and-defense taxonomy and as evidence that no current survey integrates FL + blockchain + optimised HE — *our framework is the missing synthesis.* Position our contribution as: (i) an HE-parameter optimisation procedure that resolves the noise-flooding-vs-precision conflict this survey flags but never solves (p. 11); (ii) blockchain-anchored attestation closing the CCA1/verifiability gap noted on p. 13; (iii) a unified threat model covering both crypto-layer attacks from this survey *and* the ML-layer attacks it ignores.
