# Disclaimer

**llm-log-triage** — structured log triage via LLM (severity, category, cause, action).

Read this before using any triage output, eval scores, or automation built from this code — **including in production**.

---

## What this project is

An **open-source learning lab** for LLMOps: frozen LangChain apps, golden-set evals, and a fair comparison of observability tools. It demonstrates engineering patterns (tracing, offline eval, CI gates, prompt/model experiments) — it is **not** a certified monitoring, alerting, or safety-critical product.

---

## No warranty

This software is provided **“AS IS”**, without warranty of any kind, express or implied. See the [MIT License](LICENSE) for full legal terms.

The authors and contributors **do not warrant** that:

- Triage output will be correct, complete, or timely
- Severity or category labels will match your organization’s standards
- Critical, severe, or security-related issues will be detected
- Golden-set or LangSmith experiment scores will hold in your environment
- The software is fit for on-call, incident response, compliance, or life-safety use

---

## Your responsibility

You may use this software for **personal, educational, commercial, and production** purposes under the MIT License — **at your own risk**.

If you deploy triage or alerting based on this code:

- Validate behavior on **your** logs, models, and prompts
- Maintain human review and established incident processes
- Do not rely on this software as the **sole** basis for severity decisions or paging
- Treat eval pass rates as **development signals**, not production guarantees

---

## Limitation of liability

To the maximum extent permitted by applicable law, the authors and copyright holders shall **not be liable** for any claim, damages, or other liability arising from use of this software — including missed, misclassified, or delayed detection of severe, critical, or security incidents — whether in contract, tort, or otherwise.

Some jurisdictions do not allow certain liability exclusions; in those cases, liability is limited to the extent permitted by law.

---

## No endorsement

Use of this software does not imply endorsement by the authors. Derivative products should not suggest official certification or support without explicit written permission.

---

## Questions

For licensing and attribution: see [LICENSE](LICENSE).

For security issues in this repo: open a GitHub issue (do not rely on this document as a security SLA).

---

*This disclaimer supplements the MIT License; it does not replace it.*
