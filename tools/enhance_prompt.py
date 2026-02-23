"""Core prompt enhancement logic: LLM profiles + 3 API functions."""

import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# LLM Profiles
# Each profile defines how to structure and frame a prompt for that model,
# based on official documentation from each provider.
# ---------------------------------------------------------------------------

LLM_PROFILES = {
    "Claude": {
        "style_hint": "XML tags · Full structure · Explain WHY · Chain-of-thought",
        "has_role": True,
        "role_framing": "You are [expert].",
        "structure": "xml_tags",
        "components": ["role", "task", "context", "examples", "output", "constraints", "instructions"],
        "cot_phrase": "Think through this carefully before responding.",
        "avoid": ["be thorough", "do not be lazy", "carefully"],
        "special": (
            "Use XML tags for every section. Explain the reasoning BEHIND each constraint "
            "(e.g. 'Avoid jargon because the audience is non-technical'), not just the constraint itself. "
            "Place instructions AFTER any long context blocks. "
            "Be explicit about desired quality — Claude will not infer 'go beyond basics' without being told."
        ),
        "component_labels": {
            "role": "Role (expert persona)",
            "task": "Task (objective)",
            "context": "Context (background + WHY it matters)",
            "examples": "Examples (few-shot demonstrations)",
            "output": "Output (format, length, structure)",
            "constraints": "Constraints (boundaries + reasoning)",
            "instructions": "Instructions (meta-guidance + CoT trigger)",
        },
    },
    "ChatGPT": {
        "style_hint": "Act as · Numbered steps · Few-shot + rules · Think step by step",
        "has_role": True,
        "role_framing": "Act as [expert].",
        "structure": "bold_headers",
        "components": ["persona", "objective", "context", "steps", "examples", "output_format", "chain_of_thought"],
        "cot_phrase": "Think step by step.",
        "avoid": ["vague adjectives", "ambiguous phrasing"],
        "special": (
            "Start with 'Act as [expert persona].' "
            "Use bold **Headers** to separate sections. "
            "Pair EACH example with the explicit rule it demonstrates — examples alone are not enough. "
            "Include 2–5 diverse examples. "
            "End instructions with 'Think step by step.' "
            "GPT-4 follows instructions very literally — be precise, avoid vague language."
        ),
        "component_labels": {
            "persona": "Persona (Act as...)",
            "objective": "Objective (what to accomplish)",
            "context": "Context (background)",
            "steps": "Steps (numbered instructions)",
            "examples": "Examples (with paired rules)",
            "output_format": "Output Format (structure + length)",
            "chain_of_thought": "Chain-of-Thought (reasoning trigger)",
        },
    },
    "Gemini": {
        "style_hint": "## Markdown headers · Instructions LAST · Anchor phrase · Direct commands",
        "has_role": True,
        "role_framing": "You are [expert].",
        "structure": "markdown_headers",
        "components": ["role", "background", "task", "examples", "output_format"],
        "cot_phrase": None,
        "avoid": ["please", "carefully", "I need you to", "could you"],
        "special": (
            "Use ## Markdown headers for each section. "
            "Place the actual directive LAST, after all context — Gemini reasons better this way. "
            "End with the anchor phrase: 'Based on the information above, [directive].' "
            "Gemini 3 gives direct answers by default; explicitly request detail/length if needed. "
            "Avoid filler words like 'please', 'carefully', 'I need you to' — use direct commands. "
            "Use 2–3 examples maximum; too many cause overfitting."
        ),
        "component_labels": {
            "role": "Role",
            "background": "Background (rich context)",
            "task": "Task",
            "examples": "Examples (2–3 only)",
            "output_format": "Output Format",
        },
    },
    "Perplexity": {
        "style_hint": "Single topic · No role · No examples · Cite sources · Time scope",
        "has_role": False,
        "role_framing": None,
        "structure": "research_directive",
        "components": ["research_question", "time_scope", "source_types", "inclusions", "exclusions", "output_format"],
        "cot_phrase": None,
        "avoid": ["few-shot examples", "URL requests", "role personas", "multi-topic queries"],
        "special": (
            "Perplexity is a search-augmented model — NOT a chat model. Rules: "
            "(1) ONE focused topic per query — multi-topic queries confuse the search engine. "
            "(2) NO role persona — irrelevant for a search model. "
            "(3) NO few-shot examples — they trigger searches for your example content, not your actual query. "
            "(4) NEVER request URLs — the model cannot see actual URLs and will hallucinate them. "
            "(5) Always specify a time scope (e.g. 'published after January 2025'). "
            "(6) Specify source types: Academic / Reddit / YouTube / Writing / Wolfram Alpha. "
            "(7) Use evidence-first framing: 'Cite sources for each claim'."
        ),
        "component_labels": {
            "research_question": "Research Question (specific, single-topic)",
            "time_scope": "Time Scope (recency filter)",
            "source_types": "Source Types (Academic / Reddit / etc.)",
            "inclusions": "Required Inclusions (what to cite/show)",
            "exclusions": "Exclusions (what to omit)",
            "output_format": "Output Format",
        },
    },
}

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM = """\
You are a prompt engineering expert. Analyze the user's raw prompt and identify \
which framework components are present (even if implicit or partial).

The component keys depend on the target LLM provided. Return ONLY valid JSON — \
no markdown, no explanation. Each key maps to either a short extracted string \
(what you found) or null (absent/unclear).

Be generous: if a component is implied, extract the implied text."""


_QUESTIONS_SYSTEM = """\
You are a prompt engineering expert specializing in {llm}.

The user wants to enhance their prompt for {llm}. Based on the analyzed components \
and {llm}'s specific requirements, identify the {max_q} most impactful missing or \
weak pieces of information.

Important rules for {llm}:
{special}

Avoid asking about components: {present_components}

=== INTENT DETECTION — READ BEFORE GENERATING QUESTIONS ===
First, identify the user's core intent from the raw prompt:

IMAGE GENERATION intent (draw, paint, illustrate, generate an image, create a picture, \
sketch, render, design an image): Ask about VISUAL attributes — art style \
(photorealistic, anime, oil painting, watercolor, 3D render), mood/atmosphere, \
lighting, color palette, composition, subject details, aspect ratio, camera angle. \
The inferred_example must describe visual image parameters. NEVER suggest ASCII art, \
text art, or code as the output format.

TEXT / CHAT intent (write, explain, summarize, analyze, help me with, answer, \
list, compare): Ask about the framework components normally. Output format means \
written structure — paragraphs, bullets, tables, reports.

SEARCH / RESEARCH intent (find, research, what is, look up, sources on): Follow \
Perplexity-style research question conventions regardless of LLM selected.

The inferred_example must reflect the ACTUAL intent — not a generic template.
=== END INTENT DETECTION ===

For each question you generate, also infer the most likely answer from the raw prompt \
context — even if it's not stated explicitly. This inferred answer will be shown to \
the user as a ready-to-use suggestion they can accept with one click.

CRITICAL: The inferred_example MUST be detailed and specific — 5 to 6 lines minimum. \
Write it as if a domain expert is filling out the answer. Do NOT write one-liners or \
vague summaries. A good inferred_example includes:
- Specific details, numbers, names, or qualifiers drawn from the prompt context
- Concrete scenarios or use cases relevant to the user's actual goal
- Nuances that matter specifically for {llm} (e.g. tone calibration, format cues)
- Any audience, constraint, or output preference you can reasonably infer
- Phrasing that is immediately usable as-is — the user should be able to accept it \
with one click and get a meaningfully better prompt result.

Return ONLY valid JSON — no markdown, no explanation. Schema:
[
  {{
    "component": "component_name",
    "question": "The specific question to ask the user",
    "inferred_example": "Your best guess at the answer, inferred from the prompt",
    "placeholder": "Short hint for the text input field"
  }}
]

Return no more than {max_q} questions. Prioritize by impact for {llm}."""


_ENHANCE_SYSTEM = """\
You are a world-class prompt engineer specializing in {llm}.

Transform the raw prompt provided in the user message into an expertly crafted \
prompt optimized specifically for {llm}.

=== STEP 0 — DETECT INTENT BEFORE APPLYING ANY FRAMEWORK ===
Read the raw prompt and determine the user's core intent. This OVERRIDES all framework rules below.

IMAGE GENERATION (keywords: draw, paint, illustrate, generate an image, create a picture, \
sketch, render, design an image):
  - The enhanced prompt must be an IMAGE GENERATION PROMPT — a richly detailed scene \
description specifying subject, style, mood, lighting, colors, composition, and \
any relevant technical parameters (aspect ratio, camera angle, rendering style).
  - Do NOT apply the text-output framework sections (Role, Chain-of-Thought, etc.) as \
wrappers around an image description — they don't apply to image generation.
  - Do NOT convert an image generation request into ASCII art, text art, code, or any \
written representation of the image. The output should describe an image to be rendered.
  - NEVER output ASCII art or text-based drawings in response to an image generation request.

TEXT / CHAT (keywords: write, explain, summarize, analyze, help me with, answer, compare, \
list, describe in words): Apply the full {llm} framework below normally.

SEARCH / RESEARCH (keywords: find, research, what is, look up, sources on): Apply \
research-focused framing regardless of LLM.
=== END STEP 0 ===

=== {llm} STRUCTURE & STYLE REQUIREMENTS (applies to TEXT/CHAT intent only) ===
{special}

=== COMPONENT ORDER FOR {llm} ===
{components}

=== RULES ===
1. Preserve the user's original intent completely — never change what they want.
2. Apply {llm}'s preferred format, structure, and framing exactly (for text intent).
3. Incorporate additional context from user answers naturally.
4. If a component has NO information (not in raw prompt, not in answers), OMIT it entirely — do not hallucinate content.
5. Output ONLY the final enhanced prompt — no explanation, no preamble, no "Here is your enhanced prompt:".
6. The output must be ready to paste directly into {llm}."""

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_client() -> anthropic.Anthropic:
    # Check Streamlit secrets first (Streamlit Cloud deployments),
    # then fall back to environment variable (local .env via python-dotenv).
    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. "
            "Local: add it to your .env file. "
            "Cloud: add it to Streamlit secrets."
        )
    return anthropic.Anthropic(api_key=api_key)


def _call(system: str, user: str, max_tokens: int = 1024) -> str:
    """Single API call to claude-haiku-4-5. Returns the text response."""
    client = _get_client()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def _parse_json(raw: str, fallback):
    """Strip markdown fences and parse JSON. Returns fallback on failure."""
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return fallback

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_prompt_components(raw_prompt: str, target_llm: str) -> dict:
    """
    Detect which framework components are present in the raw prompt.
    Returns a dict keyed by that LLM's component names, each value: str | None.
    """
    profile = LLM_PROFILES[target_llm]
    components = profile["components"]
    labels = profile["component_labels"]

    component_descriptions = "\n".join(
        f'  "{c}": {labels[c]}' for c in components
    )

    user_msg = (
        f"Target LLM: {target_llm}\n\n"
        f"Component keys to detect:\n{component_descriptions}\n\n"
        f"Raw prompt to analyze:\n{raw_prompt}"
    )

    raw = _call(_ANALYSIS_SYSTEM, user_msg, max_tokens=512)
    fallback = {c: None for c in components}
    result = _parse_json(raw, fallback)

    # Ensure all expected keys are present
    for c in components:
        if c not in result:
            result[c] = None
    return result


def generate_clarifying_questions(
    raw_prompt: str,
    target_llm: str,
    components: dict,
    max_questions: int = 4,
) -> list:
    """
    Generate up to max_questions targeted clarifying questions for missing/weak
    components. Each question includes an AI-inferred example answer.

    Returns list of dicts: {component, question, inferred_example, placeholder}
    """
    profile = LLM_PROFILES[target_llm]
    present = [k for k, v in components.items() if v]
    missing = [k for k, v in components.items() if not v]

    if not missing:
        return []

    system = _QUESTIONS_SYSTEM.format(
        llm=target_llm,
        max_q=max_questions,
        special=profile["special"],
        present_components=", ".join(present) if present else "none",
    )

    user_msg = (
        f"Raw prompt: {raw_prompt}\n\n"
        f"Missing/weak components: {', '.join(missing)}\n\n"
        f"Already present: {', '.join(present) if present else 'none'}"
    )

    raw = _call(system, user_msg, max_tokens=1024)
    result = _parse_json(raw, [])

    # Validate structure
    validated = []
    for item in result:
        if isinstance(item, dict) and "question" in item:
            validated.append({
                "component": item.get("component", ""),
                "question": item.get("question", ""),
                "inferred_example": item.get("inferred_example", ""),
                "placeholder": item.get("placeholder", "Type your answer here..."),
            })
    return validated[:max_questions]


def build_enhanced_prompt(
    raw_prompt: str,
    target_llm: str,
    components: dict,
    user_answers: dict,
) -> str:
    """
    Build the final enhanced prompt optimized for target_llm.
    Merges raw prompt analysis + user answers into the LLM-specific format.
    Returns only the final prompt string.

    Security note: user-controlled content (raw_prompt, user_answers) is placed
    ONLY in the user message — never in the system prompt — to prevent format
    string injection and system prompt contamination.
    """
    profile = LLM_PROFILES[target_llm]

    # System prompt contains ONLY static/internal data — no user input.
    system = _ENHANCE_SYSTEM.format(
        llm=target_llm,
        special=profile["special"],
        components=" → ".join(profile["components"]),
    )

    # All user-controlled content goes here — in the user turn only.
    components_json = json.dumps(components, indent=2)
    answers_json = json.dumps(user_answers, indent=2) if user_answers else "{}"
    user_msg = (
        f"Enhance this prompt for {target_llm}.\n\n"
        f"RAW PROMPT:\n{raw_prompt}\n\n"
        f"ANALYZED COMPONENTS (what was found in the original):\n{components_json}\n\n"
        f"ADDITIONAL CONTEXT FROM USER ANSWERS:\n{answers_json}"
    )
    return _call(system, user_msg, max_tokens=2048)
