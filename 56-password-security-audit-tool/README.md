# Personal Password Security Audit Tool

A local, cybersecurity-focused password analysis engine built in Python to evaluate password resilience, Shannon entropy, predictable sequence patterns, and dictionary vulnerability without persisting or transmitting sensitive user data.

---

## Security Principles & Privacy Guarantee

1. **Zero Storage & Zero Network Transmission**:
   - Analyzed passwords exist strictly in volatile memory during the lifetime of the evaluation function call.
   - Passwords are **never written to SQLite, logs, or disk files**, and no remote HTTP requests or telemetry are executed.
2. **Mathematical Shannon Entropy**:
   - Calculates theoretical keyspace entropy:
     $$E = L \times \log_2(R)$$
     where $L$ is password length and $R$ is the size of the glyph pool (lowercase, uppercase, digits, symbols).
3. **Pattern & Sequence Detection**:
   - Detects common dictionary words (`password`, `admin`, `welcome`), keyboard walks (`qwerty`, `asdfgh`), and numeric sequences (`123456`, `654321`).
4. **Actionable Hardening Guidance**:
   - Provides specific advice (e.g. extending length to $\ge 14$ characters, eliminating consecutive repetitions, increasing symbol variety).
5. **Scoring Limitations**:
   - Heuristics evaluate offline brute-force complexity. They do not protect against keyloggers, session hijacking, or third-party credential stuffing breaches.

---

## Running the Application

```bash
cd 56-password-security-audit-tool
python3 main.py
```

---

## Running Automated Tests

```bash
python3 -m unittest test_auditor.py -v
```
