# Disclaimer

**llm-log-triage** — open-source (MIT) structured log triage via LLM: raw log text in → JSON out (severity, category, cause, action).

Read this before using any triage output, eval scores, or automation built from this code — **including in production**. Setup and scope: [README.md](README.md).

---

## What this project is

A **teaching and reference implementation** of **Evaluation-Driven Development (EDD)** for LLM apps — built around a small, frozen LangChain log-triage pipeline.

It demonstrates:

- A **golden set** of labeled cases and a **code reviewer** (`eval_checks.py`) that scores triage output
- **CI merge gates** — L0 schema checks (`test (free)`) and L1 golden-set eval (`eval (golden-set)`, ≥90% pass rate)
- An optional **LLM judge** (L2) for coherence and actionability — manual / notebook only, not a merge gate
- CLI, Streamlit, and notebook interfaces; you supply your own provider API keys (OpenAI, Anthropic, etc.)

Optional observability hooks (e.g. LangSmith tracing) may be present — they are **not** required to run the app or pass CI.

This is **not** a certified monitoring, alerting, or safety-critical product.

---

## No warranty

This software is provided **“AS IS”**, without warranty of any kind, express or implied. See the [MIT License](LICENSE) for full legal terms.

The authors and contributors **do not warrant** that:

- Triage output will be correct, complete, or timely
- Severity or category labels will match your organization’s standards
- Critical, severe, or security-related issues will be detected
- Golden-set pass rates, CI green checks, or a **“main is green” badge** will hold in your environment or on your logs
- Optional L2 judge scores reflect production readiness
- The software is fit for on-call, incident response, compliance, or life-safety use

---

## Your responsibility

You may use this software for **personal, educational, commercial, and production** purposes under the MIT License — **at your own risk**.

If you deploy triage or alerting based on this code:

- Validate behavior on **your** logs, models, and prompts — not only the bundled golden set
- Maintain human review and established incident processes
- Do not rely on this software as the **sole** basis for severity decisions or paging
- Treat **EDD eval pass rates and CI status as development signals**, not production guarantees — a green merge gate means the frozen golden set passed under CI conditions, not that your live traffic is safe

Branch protection and golden-set evals are **recommended engineering practice** in this repo; they do not transfer liability or certify fitness for your use case.

---

## Limitation of liability

To the maximum extent permitted by applicable law, the authors and copyright holders shall **not be liable** for any claim, damages, or other liability arising from use of this software — including missed, misclassified, or delayed detection of severe, critical, or security incidents — whether in contract, tort, or otherwise.

Some jurisdictions do not allow certain liability exclusions; in those cases, liability is limited to the extent permitted by law.

---

## No endorsement

Use of this software does not imply endorsement by the authors. Derivative products should not suggest official certification or support without explicit written permission.

---

## Questions

- Setup, EDD overview, and CI workflows: [README.md](README.md)
- Architecture and eval layers: [docs/architecture.md](docs/architecture.md)
- Licensing and attribution: [LICENSE](LICENSE)

For security issues in this repo: open a GitHub issue (do not rely on this document as a security SLA).

---

*This disclaimer supplements the MIT License; it does not replace it.*
