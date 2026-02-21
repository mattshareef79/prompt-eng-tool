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

st.markdown(
    """
    <style>
    .block-container { max-width: 780px; padding-top: 2rem; }
    .stProgress > div > div { border-radius: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    "draft": "",            # holds the text area value for the current question
    "use_suggestion": False,
    "last_request_time": 0, # unix timestamp of last API call (rate limiting)
    "request_count": 0,     # total API calls this session
}

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


_init_state()

# ---------------------------------------------------------------------------
# Stage 1 — Input
# ---------------------------------------------------------------------------


def render_input():
    st.title("✦ Prompt Enhancement Tool")
    st.caption(
        "Enter your rough prompt, choose your target LLM, and we'll restructure "
        "it using that model's proven prompt engineering framework."
    )
    st.divider()

    target_llm = st.selectbox(
        "Target LLM",
        options=list(LLM_PROFILES.keys()),
        index=list(LLM_PROFILES.keys()).index(st.session_state.target_llm),
        key="llm_select",
    )
    # Persist selection across reruns
    st.session_state.target_llm = target_llm
    st.caption(f"**Style:** {LLM_PROFILES[target_llm]['style_hint']}")

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
    st.title("Prompt Analysis")

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

    st.caption(f"Target LLM: **{st.session_state.target_llm}**")
    st.progress(coverage, text=f"Prompt completeness: {coverage}%")

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
                            {},
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
                                {},
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
                    st.session_state.answers,
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

    st.title("Let's fill in the gaps")
    st.progress((idx) / total, text=f"Question {idx + 1} of {total}")
    st.divider()

    icon = _COMPONENT_ICONS.get(q["component"], "•")
    st.caption(f"Improving: {icon} **{component_label}**")
    st.subheader(q["question"])

    # Inferred suggestion box
    if q.get("inferred_example"):
        st.info(f"💡 **Based on your prompt, we think:**\n\n{q['inferred_example']}")

        use_col, _ = st.columns([1, 3])
        with use_col:
            if st.button("Use this suggestion", key=f"use_{idx}"):
                st.session_state.draft = q["inferred_example"]
                st.rerun()

    st.markdown("**Or write your own:**")
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
    st.title("Your Enhanced Prompt")
    st.caption(
        f"Optimized for **{st.session_state.target_llm}** · "
        "Click the copy icon in the top-right of the box below."
    )
    st.divider()

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
