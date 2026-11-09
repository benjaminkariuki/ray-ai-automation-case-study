"""AI calls with automatic failover, verdict parsing and message formatting.

Provider order for every call:
  1. OpenRouter (primary model, then OpenRouter's own fallback model)
  2. Cloudflare Workers AI (backup) - used when OpenRouter errors, is rate-limited or returns nothing usable
"""
import json
import os
import re
import time

import requests

REQUIRED_KEYS = ("is_remote", "is_english", "is_relevant", "is_agency", "reason")


def fill(template, values):
    """Replace {{placeholders}} in a prompt template; unknown placeholders are left as-is."""
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(values.get(m.group(1), m.group(0))), template)


def provider_of(model):
    return "Cloudflare" if str(model).startswith("@cf/") else "OpenRouter"


class AIClient:
    def __init__(self, config, openrouter_key=None, cf_account=None, cf_token=None):
        self.config = config
        self.openrouter_key = openrouter_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.cf_account = cf_account or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        self.cf_token = cf_token or os.environ.get("CLOUDFLARE_API_TOKEN", "")
        self.backup_calls = 0
        self._last_openrouter_call = 0.0

    # --- providers -------------------------------------------------------
    def _openrouter(self, models, prompt, temperature, json_mode):
        if not self.openrouter_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        wait = 3.5 - (time.time() - self._last_openrouter_call)  # free tier: max ~20 requests/minute
        if wait > 0:
            time.sleep(wait)
        body = {"models": models, "temperature": temperature, "messages": [{"role": "user", "content": prompt}]}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        self._last_openrouter_call = time.time()
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=120, headers={
            "Authorization": f"Bearer {self.openrouter_key}", "X-Title": "RAY Job Outreach"})
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(str(data["error"])[:200])
        return data["choices"][0]["message"].get("content") or "", data.get("model", models[0])

    def _cloudflare(self, model, prompt, temperature, max_tokens):
        if not (self.cf_account and self.cf_token):
            raise RuntimeError("Cloudflare credentials not set")
        r = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account}/ai/v1/chat/completions",
            json={"model": model, "temperature": temperature, "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": prompt}]},
            headers={"Authorization": f"Bearer {self.cf_token}"}, timeout=180)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"].get("content") or "", data.get("model", model)

    def complete(self, prompt, *, primary, temperature, json_mode, backup_max_tokens, is_usable):
        """Try OpenRouter, then Cloudflare. Returns (text, model) or raises the last error."""
        errors = []
        models = [m for m in (primary, self.config["fallback_model"]) if m]
        for attempt in range(2):
            try:
                text, model = self._openrouter(models, prompt, temperature, json_mode)
                if is_usable(text):
                    return text, model
                errors.append("OpenRouter: unusable reply")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"OpenRouter: {exc}")
                if "429" in str(exc) and attempt == 0:
                    break  # rate-limited/quota: go straight to the backup instead of waiting
        for attempt in range(3):
            try:
                self.backup_calls += 1
                text, model = self._cloudflare(self.config["backup_model"], prompt, temperature, backup_max_tokens)
                if is_usable(text):
                    return text, model
                errors.append("Cloudflare: unusable reply")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Cloudflare: {exc}")
            time.sleep(2)
        raise RuntimeError("; ".join(e[:160] for e in errors))

    # --- the two AI steps --------------------------------------------------
    def validate(self, job):
        prompt = fill(self.config["validation_prompt"], {
            "job_title": job["title"], "company_name": job["company"], "location": job["location"],
            "job_description": job["description"][:6000]})
        text, model = self.complete(prompt, primary=self.config["validation_model"], temperature=0, json_mode=True,
                                    backup_max_tokens=1500, is_usable=lambda t: parse_verdict(t) is not None)
        verdict = parse_verdict(text)
        verdict["model"] = f"{model} ({provider_of(model)})"
        return verdict

    def write_outreach(self, job, verdict):
        prompt = fill(self.config["outreach_prompt_text"], {
            **self.config["sender"], "job_title": job["title"], "company_name": job["company"],
            "location": job["location"], "language_requirements": verdict["languages"],
            "job_description": job["description"][:6000]})
        text, model = self.complete(prompt, primary=self.config["outreach_model"], temperature=0.7, json_mode=False,
                                    backup_max_tokens=2500, is_usable=lambda t: not message_problems(clean_text(t)))
        return format_message(text, self.config["sender"]), f"{model} ({provider_of(model)})"


def _bool(value):
    return value is True or str(value).strip().lower() == "true"


def parse_verdict(text):
    """Parse the validator's JSON. Incomplete answers return None (treated as an error and retried),
    never as a rejection, so a good job is never dropped because a model cut its reply short."""
    if not text:
        return None
    text = strip_reasoning(text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except ValueError:
        return None
    if any(k not in data for k in REQUIRED_KEYS) or not str(data.get("reason", "")).strip():
        return None
    return {"remote": _bool(data["is_remote"]), "english": _bool(data["is_english"]),
            "relevant": _bool(data["is_relevant"]), "agency": _bool(data["is_agency"]),
            "languages": str(data.get("language_requirements") or "English"), "reason": str(data["reason"]).strip()}


def strip_reasoning(text):
    """Remove a model's hidden reasoning if it leaked into the reply.

    Some models (e.g. gpt-oss on Cloudflare) occasionally return their raw "analysis" channel and chat tokens,
    such as "analysis: ...<|end|><|start|>assistantfinal: Subject: ...". Only the final answer is kept."""
    text = re.sub(r"<think>[\s\S]*?</think>", "", str(text or ""))
    final = re.split(r"(?:<\|[a-z_]+\|>)*\s*assistant\s*final\s*:?|<\|channel\|>\s*final\s*(?:<\|message\|>)?", text,
                     flags=re.I)
    if len(final) > 1:
        text = final[-1]
    return re.sub(r"<\|[a-z_]+\|>", "", text).strip()


def message_problems(text):
    """Reasons an outreach draft is not good enough to save (empty list = fine). A draft with problems is
    regenerated (next provider/attempt) instead of being written to the Sheet."""
    problems = []
    words = text.split()
    if not text.lstrip().lower().startswith("subject:"):
        problems.append("no subject line")
    if not 40 <= len(words) <= 320:
        problems.append(f"{len(words)} words")
    if re.search(r"<\||\|>|assistantfinal|^\s*analysis\b", text, flags=re.I | re.M):
        problems.append("leaked model tokens")
    if re.search(r"\b(\w+)(?:\s+\1\b){4,}", text, flags=re.I):
        problems.append("repeated words")
    if re.search(r"\{\{|\[(?:name|company|your name)\]", text, flags=re.I):
        problems.append("unfilled placeholder")
    return problems


def clean_text(text):
    text = strip_reasoning(text)
    text = text.replace("‐", "-").replace("‑", "-").replace(" ", " ").replace(" ", " ")
    text = re.sub(r"^```[a-z]*\n?|```$", "", text, flags=re.M | re.I)
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text).strip()


def format_message(text, sender):
    """Same ending whatever the model wrote: body, blank line, call to action, blank line, signature."""
    message = clean_text(text)
    cta = sender.get("call_to_action", "")
    signature = [s.strip() for s in (sender.get("sender_name", ""), sender.get("sender_company", "")) if s.strip()]
    if cta:
        message = message.replace(cta, "")
    lines = [line.rstrip() for line in message.split("\n") if line.strip() not in signature]
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return "\n\n".join(part for part in (body, cta, "\n".join(signature)) if part)
