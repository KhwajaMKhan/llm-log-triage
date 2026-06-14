"""Prompt templates for LLM log triage.

Three versions (v1→v3) for the scorecard "prompt management" axis.
v1 = baseline, v2 = adds severity rubric, v3 = adds adversarial handling.
Used by chain.py via get_prompt(version).
"""

from langchain_core.prompts import ChatPromptTemplate

SEVERITY_RUBRIC = """
Severity rubric (apply strictly):
- SEV1: OOMKilled, pod evicted, vault sealed, total service outage, data loss risk
- SEV2: DB unreachable, connection refused, TLS/cert expired, deadlock, DNS NXDOMAIN,
  external API 503 retries exhausted, SAML clock skew, generic HTTP 500 errors
- SEV3: single-user JWT expired, disk usage warning (~90%), job lag, rate limit exceeded,
  upstream latency degradation (p99 high), SMTP auth failure, buffer high watermark, WARN logs
- SEV4: INFO logs, successful scrape/completion, routine operational messages
- unknown: empty, truncated, nonsense, or repetitive spam with no parseable incident
"""

CATEGORY_RUBRIC = """
Category rubric (pick exactly one):
- connectivity: connection refused, DNS failures, deadlocks, redis READONLY wrong replica,
  network timeouts to peers
- resource: OOM, memory/disk pressure, pod eviction, rate limits, buffer capacity, job lag
- auth: JWT/SAML/SMTP authentication or credential failures
- config: yaml parse errors, certificate expired, vault sealed/unseal required
- dependency: upstream latency, external API 503 (Stripe), origin timeout, LaunchDarkly disconnect
- unknown: generic internal HTTP 500 with no clear subsystem, or insufficient log context
"""

ADVERSARIAL_RULES = """
Adversarial / low-signal input rules:
- Empty log, truncated fragment, keyboard mash, OR repeated identical tokens (e.g. "ERROR ERROR ERROR")
  with no timestamp/service/context → severity=unknown, category=unknown, confidence ≤ 0.3
- Do NOT assign SEV1–SEV4 to spam or unparseable input
"""

LOG_LEVEL_RULES = """
Log level → severity (do NOT treat every ERROR as SEV2):
- FATAL, OOMKilled, pod Evicted, vault sealed → SEV1
- ERROR + connection refused / 503 exhausted / deadlock / cert expired / yaml parse → SEV2
- ERROR + single JWT expired, SMTP auth fail, rate limit → SEV3 (subset impact)
- WARN + latency, disk %, job lag, buffer, stream disconnect → SEV3
- INFO + successful scrape/completion/normal ops → SEV4 (even if category is unknown)
"""

FEW_SHOT = """
Examples:
1. "FATAL ... OOMKilled ... memory limit" → SEV1, resource
2. "WARN ... upstream latency p99=3200ms" → SEV3, dependency
3. "ERROR ... JWT ... token expired for user_id=8821" → SEV3, auth
4. "INFO ... scrape completed duration_ms=45" → SEV4, unknown
"""

PROMPTS: dict[str, ChatPromptTemplate] = {
    "v1": ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an SRE triage assistant. Analyze application logs and return structured JSON.\n"
                "Fields: severity, category, likely_cause, suggested_action, confidence (0-1), evidence_lines.\n"
                + CATEGORY_RUBRIC,
            ),
            (
                "human",
                "Service: {service_name}\n\nLog:\n{log_text}",
            ),
        ]
    ),
    "v2": ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an SRE triage assistant. Analyze application logs and return structured JSON.\n"
                "Fields: severity, category, likely_cause, suggested_action, confidence (0-1), evidence_lines.\n"
                + SEVERITY_RUBRIC
                + "\n"
                + CATEGORY_RUBRIC,
            ),
            (
                "human",
                "Service: {service_name}\n\nLog:\n{log_text}",
            ),
        ]
    ),
    "v3": ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an SRE triage assistant. Analyze application logs and return structured JSON.\n"
                "Fields: severity, category, likely_cause, suggested_action, confidence (0-1), evidence_lines.\n"
                + SEVERITY_RUBRIC
                + "\n"
                + CATEGORY_RUBRIC
                + "\n"
                + LOG_LEVEL_RULES
                + "\n"
                + ADVERSARIAL_RULES
                + "\n"
                + FEW_SHOT,
            ),
            (
                "human",
                "Service: {service_name}\n\nLog:\n{log_text}",
            ),
        ]
    ),
}


def get_prompt(version: str = "v1") -> ChatPromptTemplate:
    if version not in PROMPTS:
        raise ValueError(f"Unknown prompt version: {version}. Choose from {list(PROMPTS)}")
    return PROMPTS[version]
