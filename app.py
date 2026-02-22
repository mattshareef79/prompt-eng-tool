"""Prompt Enhancement Tool — Streamlit app."""

import time

import streamlit as st

from tools.enhance_prompt import (
    LLM_PROFILES,
    analyze_prompt_components,
    build_enhanced_prompt,
    generate_clarifying_questions,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Prompt Enhancement Tool",
    page_icon="✦",
    layout="centered",
)

st.markdown("""
<style>
/* ── Base ──────────────────────────────── */
.stApp { background: #f5f6ff; }
.block-container { max-width: 820px; padding-top: 0.5rem; padding-bottom: 3rem; }

/* ── Hero banner ───────────────────────── */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(102,126,234,0.28);
}
.hero h1 {
    color: white; font-size: 1.9rem; font-weight: 800;
    margin: 0 0 0.4rem 0; letter-spacing: -0.02em;
}
.hero p { color: rgba(255,255,255,0.88); font-size: 0.97rem; margin: 0; line-height: 1.55; }
.hero .step-badge {
    display: inline-block;
    background: rgba(255,255,255,0.22);
    border-radius: 20px; padding: 0.18rem 0.75rem;
    font-size: 0.78rem; color: rgba(255,255,255,0.95);
    margin-bottom: 0.7rem; font-weight: 600; letter-spacing: 0.02em;
}

/* ── Primary buttons ────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important; border-radius: 10px !important;
    color: white !important; font-weight: 600 !important;
    font-size: 0.95rem !important; padding: 0.6rem 1.8rem !important;
    box-shadow: 0 4px 14px rgba(102,126,234,0.38) !important;
    transition: all 0.18s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102,126,234,0.5) !important;
}
.stButton > button[kind="primary"]:active { transform: translateY(0) !important; }

/* ── Secondary buttons ──────────────────── */
.stButton > button:not([kind="primary"]) {
    background: white !important; border: 2px solid #667eea !important;
    border-radius: 10px !important; color: #667eea !important;
    font-weight: 500 !important; transition: all 0.18s ease !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: rgba(102,126,234,0.06) !important;
    border-color: #764ba2 !important; color: #764ba2 !important;
}

/* ── Progress bar ──────────────────────── */
div[data-testid="stProgress"] > div {
    background: rgba(102,126,234,0.15); border-radius: 10px; height: 8px !important;
}
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #667eea, #764ba2) !important; border-radius: 10px;
}

/* ── Info / suggestion box ───────────────── */
div[data-testid="stInfo"] {
    background: linear-gradient(135deg, rgba(102,126,234,0.07), rgba(118,75,162,0.04)) !important;
    border: 1px solid rgba(102,126,234,0.22) !important;
    border-left: 4px solid #667eea !important;
    border-radius: 10px !important;
}

/* ── Text areas ─────────────────────────── */
.stTextArea textarea {
    border-radius: 10px !important; border: 2px solid #e8eaf6 !important;
    font-size: 0.95rem !important; line-height: 1.55 !important;
    transition: all 0.18s !important; color: #1a1a2e !important;
}
.stTextArea textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.12) !important;
}

/* ── LLM selector — official logos as button background images ── */
/* Base padding for all four LLM buttons */
button[aria-label="Claude"],
button[aria-label="ChatGPT"],
button[aria-label="Gemini"],
button[aria-label="Perplexity"] {
    padding-left: 40px !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 20px 20px, auto !important;
}
/* Unselected: brand-colored logo on white */
button:not([kind="primary"])[aria-label="Claude"] {
    background-image: url('https://cdn.simpleicons.org/anthropic/CC785C') !important;
}
button:not([kind="primary"])[aria-label="ChatGPT"] {
    background-image: url('https://cdn.simpleicons.org/openai/10A37F') !important;
}
button:not([kind="primary"])[aria-label="Gemini"] {
    background-image: url('https://cdn.simpleicons.org/googlegemini/8E75B2') !important;
}
button:not([kind="primary"])[aria-label="Perplexity"] {
    background-image: url('https://cdn.simpleicons.org/perplexity/5436DA') !important;
}
/* Selected (primary): white logo layered over gradient */
button[kind="primary"][aria-label="Claude"] {
    background: url('https://cdn.simpleicons.org/anthropic/ffffff') no-repeat 12px center / 20px 20px,
                linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}
button[kind="primary"][aria-label="ChatGPT"] {
    background: url('https://cdn.simpleicons.org/openai/ffffff') no-repeat 12px center / 20px 20px,
                linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}
button[kind="primary"][aria-label="Gemini"] {
    background: url('https://cdn.simpleicons.org/googlegemini/ffffff') no-repeat 12px center / 20px 20px,
                linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}
button[kind="primary"][aria-label="Perplexity"] {
    background: url('https://cdn.simpleicons.org/perplexity/ffffff') no-repeat 12px center / 20px 20px,
                linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* ── Code block (result) ─────────────────── */
[data-testid="stCodeBlock"] {
    border-radius: 14px !important;
    border: 2px solid rgba(102,126,234,0.18) !important;
    box-shadow: 0 4px 20px rgba(102,126,234,0.09) !important;
}

/* ── Expanders ──────────────────────────── */
details {
    border-radius: 10px !important;
    border: 1px solid rgba(102,126,234,0.15) !important;
    background: white !important; margin-top: 0.5rem !important;
}
summary { color: #667eea !important; font-weight: 500 !important; }

/* ── Dividers ───────────────────────────── */
hr {
    border: none !important; height: 1px !important;
    background: linear-gradient(90deg, rgba(102,126,234,0.3), rgba(118,75,162,0.08), transparent) !important;
    margin: 1.5rem 0 !important;
}

/* ── Caption ────────────────────────────── */
.stCaption { color: #6b7280 !important; }

/* ── Scrollbar ──────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 3px; }
::-webkit-scrollbar-thumb { background: #667eea; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "stage": "input",
    "raw_prompt": "",
    "target_llm": "Claude",
    "components": {},
    "questions": [],
    "answers": {},
    "current_q": 0,
    "enhanced_prompt": "",
    "draft": "",              # holds the text area value for the current question
    "use_suggestion": False,
    "last_request_time": 0,   # unix timestamp of last API call (rate limiting)
    "request_count": 0,       # total API calls this session
    "output_format": "(No preference)",
    "output_format_details": "",
}

_OUTPUT_FORMAT_OPTIONS = [
    "(No preference)",
    "Prose / Essay",
    "Bullet List",
    "Table / Spreadsheet",
    "Report with sections (PDF-style)",
    "Code snippet",
    "Step-by-step Guide",
    "Email / Document",
    "Chart / Visual description",
]

# Input limits — prevent runaway token costs from oversized inputs
_MAX_PROMPT_CHARS = 6000   # ~1,500 tokens
_MAX_ANSWER_CHARS = 1000   # per clarifying question answer

# Rate limiting — per session (not per IP; use a reverse proxy for IP-level limiting)
_MIN_SECONDS_BETWEEN_REQUESTS = 10  # seconds between full enhancement runs
_MAX_REQUESTS_PER_SESSION = 20      # hard cap per browser session


def _check_rate_limit() -> str | None:
    """Return an error message string if rate limited, else None."""
    now = time.time()
    elapsed = now - st.session_state.last_request_time
    if elapsed < _MIN_SECONDS_BETWEEN_REQUESTS:
        wait = int(_MIN_SECONDS_BETWEEN_REQUESTS - elapsed) + 1
        return f"Please wait {wait} seconds before submitting again."
    if st.session_state.request_count >= _MAX_REQUESTS_PER_SESSION:
        return "Session limit reached. Please refresh the page to start a new session."
    return None


def _record_request():
    st.session_state.last_request_time = time.time()
    st.session_state.request_count += 1


def _safe_api_error(e: Exception) -> str:
    """Return a user-safe error message that doesn't expose internal details."""
    msg = str(e)
    if "api_key" in msg.lower() or "ANTHROPIC_API_KEY" in msg:
        return "API key not configured. Contact the administrator."
    if "rate_limit" in msg.lower() or "429" in msg:
        return "The AI service is busy. Please try again in a few seconds."
    if "overloaded" in msg.lower() or "529" in msg:
        return "The AI service is temporarily overloaded. Please try again shortly."
    # Generic fallback — never show raw exception to public users
    return "Something went wrong while processing your request. Please try again."


def _init_state():
    for key, val in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _reset():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _init_state()


def _get_answers_with_format() -> dict:
    """Merge user Q&A answers with the chosen output format."""
    answers = dict(st.session_state.answers)
    fmt = st.session_state.output_format
    details = st.session_state.get("output_format_details", "").strip()
    if fmt and fmt != "(No preference)":
        answers["desired_output_format"] = fmt + (f" — {details}" if details else "")
    return answers


_init_state()


def _hero(title: str, subtitle: str, badge: str = ""):
    """Render a gradient hero banner replacing st.title()."""
    badge_html = f'<div class="step-badge">{badge}</div>' if badge else ""
    st.markdown(
        f'<div class="hero">{badge_html}<h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Stage 1 — Input
# ---------------------------------------------------------------------------


def render_input():
    _hero(
        "✦ Prompt Enhancement Tool",
        "Enter your rough prompt, choose your target LLM, and we'll restructure "
        "it using that model's proven prompt engineering framework.",
        badge="Step 1 of 4 · Enter Prompt",
    )

    st.markdown("**Select your target LLM**")
    cols = st.columns(len(LLM_PROFILES))
    for col, llm in zip(cols, LLM_PROFILES.keys()):
        with col:
            is_sel = st.session_state.target_llm == llm
            # Labels are plain LLM names so aria-label matches the CSS logo selectors
            st.button(
                llm,
                key=f"llm_btn_{llm}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
                on_click=_set_llm,
                args=(llm,),
            )
    st.caption(f"**Style:** {LLM_PROFILES[st.session_state.target_llm]['style_hint']}")

    st.divider()

    st.markdown("**Desired output format**")
    st.caption("What should the final output look like? This shapes how the prompt is structured.")
    output_fmt = st.selectbox(
        "Output format",
        options=_OUTPUT_FORMAT_OPTIONS,
        index=_OUTPUT_FORMAT_OPTIONS.index(st.session_state.output_format)
        if st.session_state.output_format in _OUTPUT_FORMAT_OPTIONS else 0,
        label_visibility="collapsed",
    )
    st.session_state.output_format = output_fmt
    if output_fmt != "(No preference)":
        st.text_input(
            "Format details (optional)",
            placeholder="e.g., 10 pages with executive summary · 5 columns: Name, Date, Status, Owner, Notes · bar chart by region",
            label_visibility="collapsed",
            key="output_format_details",
        )

    st.divider()

    raw_prompt = st.text_area(
        "Your raw prompt",
        height=200,
        placeholder=(
            "Paste your rough prompt here — it can be a single sentence or a messy draft. "
            "We'll analyze it and ask the right questions."
        ),
        value=st.session_state.raw_prompt,
        max_chars=_MAX_PROMPT_CHARS,
    )
    if raw_prompt:
        remaining = _MAX_PROMPT_CHARS - len(raw_prompt)
        st.caption(f"{len(raw_prompt):,} / {_MAX_PROMPT_CHARS:,} characters")

    if st.button("Analyze & Enhance →", type="primary", use_container_width=True):
        if not raw_prompt.strip():
            st.error("Please enter a prompt before continuing.")
        else:
            err = _check_rate_limit()
            if err:
                st.error(err)
            else:
                st.session_state.raw_prompt = raw_prompt.strip()
                st.session_state.stage = "analysis"
                st.session_state.components = {}   # clear any previous run
                st.rerun()


# ---------------------------------------------------------------------------
# LLM brand assets + selector callback
# ---------------------------------------------------------------------------

# SimpleIcons CDN base URLs (append /<hex-color> for colored SVGs)
_LLM_LOGO_BASE = {
    "Claude":     "https://cdn.simpleicons.org/anthropic",
    "ChatGPT":    "https://cdn.simpleicons.org/openai",
    "Gemini":     "https://cdn.simpleicons.org/googlegemini",
    "Perplexity": "https://cdn.simpleicons.org/perplexity",
}
_LLM_BRAND_COLOR = {
    "Claude": "CC785C", "ChatGPT": "10A37F",
    "Gemini": "8E75B2", "Perplexity": "5436DA",
}


def _llm_logo_url(llm: str, color: str | None = None) -> str:
    """Return a SimpleIcons CDN URL for the given LLM logo."""
    base = _LLM_LOGO_BASE[llm]
    c = color or _LLM_BRAND_COLOR[llm]
    return f"{base}/{c}"


def _set_llm(llm: str):
    st.session_state.target_llm = llm


# ---------------------------------------------------------------------------
# Stage 2 — Analysis
# ---------------------------------------------------------------------------

_COMPONENT_ICONS = {
    # generic fallbacks
    "role": "👤", "task": "🎯", "context": "🗂️", "examples": "📋",
    "output": "📄", "constraints": "🚧", "instructions": "📌",
    "persona": "👤", "objective": "🎯", "steps": "🔢", "output_format": "📄",
    "chain_of_thought": "🧠", "background": "🗂️",
    "research_question": "🔍", "time_scope": "📅", "source_types": "📚",
    "inclusions": "✅", "exclusions": "❌",
}


def render_analysis():
    _hero(
        "Prompt Analysis",
        "We've scanned your prompt against the framework for your chosen LLM. "
        "Review what's present and decide how to proceed.",
        badge="Step 2 of 4 · Analysis",
    )

    # Run analysis once and cache in session state
    if not st.session_state.components:
        with st.spinner("Analyzing your prompt..."):
            try:
                _record_request()
                components = analyze_prompt_components(
                    st.session_state.raw_prompt,
                    st.session_state.target_llm,
                )
                st.session_state.components = components
            except Exception as e:
                st.error(_safe_api_error(e))
                st.stop()

    components = st.session_state.components
    profile = LLM_PROFILES[st.session_state.target_llm]
    labels = profile["component_labels"]

    present = {k: v for k, v in components.items() if v}
    missing = {k: v for k, v in components.items() if not v}
    coverage = int(len(present) / max(len(components), 1) * 100)

    # Styled LLM badge with official logo
    llm = st.session_state.target_llm
    st.markdown(
        f'<div style="display:inline-flex;align-items:center;gap:10px;'
        f'background:white;border:2px solid rgba(102,126,234,0.22);'
        f'border-radius:10px;padding:8px 16px;margin-bottom:12px;'
        f'box-shadow:0 2px 8px rgba(102,126,234,0.08);">'
        f'<img src="{_llm_logo_url(llm)}" height="22" alt="{llm}"/>'
        f'<span style="font-weight:700;color:#1a1a2e;font-size:0.95rem;">'
        f'Target LLM: {llm}</span></div>',
        unsafe_allow_html=True,
    )
    # Progress bar — text shown separately to prevent overlap
    st.caption(f"Prompt completeness: **{coverage}%**")
    st.progress(coverage)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Found in your prompt**")
        if present:
            for k, v in present.items():
                icon = _COMPONENT_ICONS.get(k, "•")
                label = labels.get(k, k.replace("_", " ").title())
                with st.expander(f"{icon} {label}", expanded=False):
                    st.caption(v)
        else:
            st.caption("Nothing detected yet.")

    with col2:
        st.markdown("**Missing or unclear**")
        if missing:
            for k in missing:
                icon = _COMPONENT_ICONS.get(k, "•")
                label = labels.get(k, k.replace("_", " ").title())
                st.markdown(f"- {icon} {label}")
        else:
            st.caption("All components detected! 🎉")

    st.divider()
    st.subheader("How would you like to proceed?")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button(
            "Enhance with current info",
            use_container_width=True,
            help="Apply the LLM-specific format to what we already have.",
        ):
            err = _check_rate_limit()
            if err:
                st.error(err)
            else:
                with st.spinner("Building your enhanced prompt..."):
                    try:
                        _record_request()
                        enhanced = build_enhanced_prompt(
                            st.session_state.raw_prompt,
                            st.session_state.target_llm,
                            st.session_state.components,
                            _get_answers_with_format(),
                        )
                        st.session_state.enhanced_prompt = enhanced
                    except Exception as e:
                        st.error(_safe_api_error(e))
                        st.stop()
                st.session_state.stage = "result"
                st.rerun()

    with col_b:
        if st.button(
            "Ask me questions to improve →",
            type="primary",
            use_container_width=True,
            help="We'll ask up to 4 targeted questions to fill the most important gaps.",
        ):
            err = _check_rate_limit()
            if err:
                st.error(err)
            else:
                with st.spinner("Identifying what we need from you..."):
                    try:
                        _record_request()
                        questions = generate_clarifying_questions(
                            st.session_state.raw_prompt,
                            st.session_state.target_llm,
                            st.session_state.components,
                        )
                    except Exception as e:
                        st.error(_safe_api_error(e))
                        st.stop()
                if not questions:
                    # Nothing to ask — go straight to result
                    with st.spinner("Building your enhanced prompt..."):
                        try:
                            _record_request()
                            enhanced = build_enhanced_prompt(
                                st.session_state.raw_prompt,
                                st.session_state.target_llm,
                                st.session_state.components,
                                _get_answers_with_format(),
                            )
                            st.session_state.enhanced_prompt = enhanced
                        except Exception as e:
                            st.error(_safe_api_error(e))
                            st.stop()
                    st.session_state.stage = "result"
                else:
                    st.session_state.questions = questions
                    st.session_state.current_q = 0
                    st.session_state.answers = {}
                    st.session_state.draft = ""
                    st.session_state.stage = "questions"
                st.rerun()

    if st.button("← Start over", use_container_width=True):
        _reset()
        st.rerun()


# ---------------------------------------------------------------------------
# Stage 3 — Clarifying Questions
# ---------------------------------------------------------------------------


def render_questions():
    questions = st.session_state.questions
    idx = st.session_state.current_q
    total = len(questions)

    # All questions answered — build the enhanced prompt
    if idx >= total:
        with st.spinner("Building your enhanced prompt..."):
            try:
                _record_request()
                enhanced = build_enhanced_prompt(
                    st.session_state.raw_prompt,
                    st.session_state.target_llm,
                    st.session_state.components,
                    _get_answers_with_format(),
                )
                st.session_state.enhanced_prompt = enhanced
            except Exception as e:
                st.error(_safe_api_error(e))
                st.stop()
        st.session_state.stage = "result"
        st.rerun()
        return

    q = questions[idx]
    component_label = (
        LLM_PROFILES[st.session_state.target_llm]["component_labels"]
        .get(q["component"], q["component"].replace("_", " ").title())
    )

    _hero(
        "Let's fill in the gaps",
        f"Answering these questions helps us build the strongest possible prompt for {st.session_state.target_llm}.",
        badge=f"Step 3 of 4 · Question {idx + 1} of {total}",
    )
    st.progress((idx) / total, text=f"Question {idx + 1} of {total}")
    st.divider()

    icon = _COMPONENT_ICONS.get(q["component"], "•")
    st.caption(f"Improving: {icon} **{component_label}**")
    st.subheader(q["question"])

    # Inferred suggestion box — st.code() gives a built-in copy icon (top-right)
    if q.get("inferred_example"):
        st.markdown("💡 **Based on your prompt, we suggest** *(click the copy icon to copy, or accept below):*")
        st.code(q["inferred_example"], language="text", wrap_lines=True)

        use_col, _ = st.columns([1, 3])
        with use_col:
            if st.button("✓ Accept & Continue →", key=f"use_{idx}", type="primary"):
                # Save suggestion as the answer and auto-advance to next question
                st.session_state.answers[q["component"]] = q["inferred_example"]
                st.session_state.current_q += 1
                st.session_state.draft = ""
                st.rerun()

    st.markdown("**Or write your own answer below:**")
    answer = st.text_area(
        "Your answer",
        value=st.session_state.draft,
        placeholder=q.get("placeholder", "Type your answer here..."),
        height=120,
        label_visibility="collapsed",
        key=f"ta_{idx}",
        max_chars=_MAX_ANSWER_CHARS,
    )

    st.divider()
    col_next, col_skip = st.columns([3, 1])

    with col_next:
        if st.button("Next →", type="primary", use_container_width=True):
            if answer.strip():
                st.session_state.answers[q["component"]] = answer.strip()
            st.session_state.current_q += 1
            st.session_state.draft = ""
            st.rerun()

    with col_skip:
        if st.button("Skip", use_container_width=True):
            st.session_state.current_q += 1
            st.session_state.draft = ""
            st.rerun()

    with st.expander("View your original prompt"):
        st.text(st.session_state.raw_prompt)


# ---------------------------------------------------------------------------
# Stage 4 — Result
# ---------------------------------------------------------------------------


def render_result():
    _hero(
        "Your Enhanced Prompt",
        f"Optimized for {st.session_state.target_llm} · "
        "Click the copy icon in the top-right corner of the box below to copy.",
        badge="Step 4 of 4 · Done ✦",
    )

    enhanced = st.session_state.enhanced_prompt

    # st.code() has a built-in copy icon (top-right corner)
    st.code(enhanced, language="text", wrap_lines=True)

    st.divider()

    # Before / after comparison
    with st.expander("Compare: Original vs Enhanced"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Original**")
            st.text(st.session_state.raw_prompt)
        with c2:
            st.markdown("**Enhanced**")
            st.text(enhanced)

    # What the user contributed via answers
    if st.session_state.answers:
        with st.expander("What was added from your answers"):
            profile = LLM_PROFILES[st.session_state.target_llm]
            labels = profile["component_labels"]
            for comp, ans in st.session_state.answers.items():
                if ans:
                    label = labels.get(comp, comp.replace("_", " ").title())
                    st.markdown(f"**{label}:** {ans}")

    st.button(
        "← Start over with a new prompt",
        type="primary",
        use_container_width=True,
        on_click=_reset,
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

stage = st.session_state.stage

if stage == "input":
    render_input()
elif stage == "analysis":
    render_analysis()
elif stage == "questions":
    render_questions()
elif stage == "result":
    render_result()
