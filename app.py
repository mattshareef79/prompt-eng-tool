"""Prompt Enhancement Tool — Streamlit app."""

import time

import streamlit as st
import streamlit.components.v1 as components

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

/* ── LLM Dropdown (replaces button selector) ───────── */
[data-testid="stRadio"] [role="radiogroup"] {
    position: absolute !important; opacity: 0 !important;
    pointer-events: none !important; height: 0 !important; overflow: hidden !important;
}
[data-testid="stRadio"] > div { margin: 0 !important; padding: 0 !important; }
.llm-dd-container {
    position: relative; width: 280px; user-select: none; margin: 4px 0 10px 0;
}
.llm-dd-trigger {
    display: flex; align-items: center; gap: 10px; padding: 9px 14px;
    background: white; border: 2px solid #667eea; border-radius: 10px;
    cursor: pointer; font-weight: 600; font-size: 0.93rem; color: #1a1a2e;
    box-shadow: 0 2px 8px rgba(102,126,234,0.12); transition: all 0.18s;
}
.llm-dd-trigger:hover { border-color: #764ba2; box-shadow: 0 4px 14px rgba(102,126,234,0.25); }
.llm-dd-trigger img { width: 22px; height: 22px; object-fit: contain; }
.llm-dd-arrow { margin-left: auto; color: #667eea; transition: transform 0.18s; font-size: 0.8rem; }
.llm-dd-container.open .llm-dd-arrow { transform: rotate(180deg); }
.llm-dd-options {
    display: none; position: absolute; top: calc(100% + 4px); left: 0; right: 0;
    background: white; border: 2px solid rgba(102,126,234,0.22); border-radius: 10px;
    box-shadow: 0 8px 24px rgba(102,126,234,0.18); z-index: 99999; overflow: hidden;
}
.llm-dd-container.open .llm-dd-options { display: block; }
.llm-dd-option {
    display: flex; align-items: center; gap: 10px; padding: 10px 14px;
    cursor: pointer; font-size: 0.9rem; font-weight: 500; color: #1a1a2e;
    transition: background 0.12s; border-bottom: 1px solid rgba(102,126,234,0.07);
}
.llm-dd-option:last-child { border-bottom: none; }
.llm-dd-option:hover { background: rgba(102,126,234,0.06); }
.llm-dd-option.active { background: rgba(102,126,234,0.1); color: #667eea; font-weight: 700; }
.llm-dd-option img { width: 20px; height: 20px; object-fit: contain; }
.llm-dd-check { margin-left: auto; color: #667eea; font-size: 0.85rem; }

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

/* ── Share button (lives inside the hero banner) ── */
.share-top-btn {
    background: rgba(255,255,255,0.16);
    border: 1.5px solid rgba(255,255,255,0.48);
    border-radius: 20px; padding: 5px 16px;
    color: rgba(255,255,255,0.93); font-size: 0.8rem;
    cursor: pointer; font-weight: 500;
    font-family: inherit; white-space: nowrap;
    transition: all 0.18s ease; letter-spacing: 0.01em;
}
.share-top-btn:hover {
    background: rgba(255,255,255,0.28);
    border-color: rgba(255,255,255,0.8); color: white;
}
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
    "last_request_time": 0,   # unix timestamp of last API call
    "request_count": 0,       # total API calls this session
}

# Input limits
_MAX_PROMPT_CHARS = 6000
_MAX_ANSWER_CHARS = 1000

# Rate limiting — no enforced wait between requests; just a per-session cap
_MIN_SECONDS_BETWEEN_REQUESTS = 0   # no cooldown
_MAX_REQUESTS_PER_SESSION = 60      # ~20 full enhance flows per browser session



def _check_rate_limit() -> str | None:
    """Return an error message string if rate limited, else None."""
    now = time.time()
    if _MIN_SECONDS_BETWEEN_REQUESTS > 0:
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


def _hero(title: str, subtitle: str, badge: str = "", show_share: bool = False):
    """Render a gradient hero banner replacing st.title()."""
    badge_html = f'<div class="step-badge">{badge}</div>' if badge else ""
    text_block = f'{badge_html}<h1>{title}</h1><p>{subtitle}</p>'

    if show_share:
        share_btn = (
            '<button class="share-top-btn" '
            'onclick="var b=this;navigator.clipboard.writeText(window.location.href)'
            ".then(function(){b.textContent='\u2713 Link copied!';"
            "setTimeout(function(){b.textContent='\U0001f517 Share this tool';},2400);});"
            '">\U0001f517 Share this tool</button>'
        )
        inner = (
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;gap:16px;">'
            f'<div style="flex:1;">{text_block}</div>'
            f'<div style="flex-shrink:0;padding-top:6px;">{share_btn}</div>'
            f'</div>'
        )
    else:
        inner = text_block

    st.markdown(f'<div class="hero">{inner}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# LLM brand assets + helpers
# ---------------------------------------------------------------------------

# SimpleIcons CDN — append /<hex-color> for a coloured SVG
_LLM_LOGO_BASE = {
    "Claude":     "https://cdn.simpleicons.org/anthropic",
    "ChatGPT":    "https://cdn.simpleicons.org/chatgpt",
    "Gemini":     "https://cdn.simpleicons.org/googlegemini",
    "Perplexity": "https://cdn.simpleicons.org/perplexity",
}
_LLM_BRAND_COLOR = {
    "Claude": "CC785C", "ChatGPT": "74AA9C",
    "Gemini": "8E75B2", "Perplexity": "5436DA",
}


def _llm_logo_url(llm: str, color: str | None = None) -> str:
    base = _LLM_LOGO_BASE[llm]
    c = color or _LLM_BRAND_COLOR[llm]
    return f"{base}/{c}"




def _llm_badge():
    """Render the styled Target LLM badge with official logo (shown on pages 2–4)."""
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




# ---------------------------------------------------------------------------
# Dropdown injection — JavaScript via component iframe
# ---------------------------------------------------------------------------

_LLM_DROPDOWN_JS = """
<style>html,body{margin:0;padding:0;height:0;overflow:hidden}</style>
<script>
(function() {
    var LOGOS = {
        'Claude':     'https://cdn.simpleicons.org/anthropic/CC785C',
        'ChatGPT':    'https://cdn.simpleicons.org/chatgpt/74AA9C',
        'Gemini':     'https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg',
        'Perplexity': 'https://cdn.simpleicons.org/perplexity/5436DA'
    };
    var buildTimer = null;

    function buildDropdown() {
        try {
            var doc = window.parent.document;
            var stRadio = doc.querySelector('[data-testid="stRadio"]');
            if (!stRadio) return;
            var radioGroup = stRadio.querySelector('[role="radiogroup"]');
            if (!radioGroup) return;

            // Already built and current?
            var next = radioGroup.nextElementSibling;
            if (next && next.classList.contains('llm-dd-container')) return;

            // Remove stale dropdowns
            doc.querySelectorAll('.llm-dd-container').forEach(function(d) { d.remove(); });

            // Gather options from radio inputs
            var items = [];
            radioGroup.querySelectorAll('input[type="radio"]').forEach(function(inp) {
                var label = inp.closest('label');
                var text = label ? label.textContent.trim() : '';
                items.push({ input: inp, text: text, checked: inp.checked });
            });
            if (!items.length) return;

            var sel = items.find(function(i) { return i.checked; }) || items[0];

            // Build container
            var dd = doc.createElement('div');
            dd.className = 'llm-dd-container';

            // Trigger
            var trigger = doc.createElement('div');
            trigger.className = 'llm-dd-trigger';
            trigger.innerHTML =
                '<img class="llm-dd-logo" src="' + (LOGOS[sel.text]||'') + '" alt=""/>' +
                '<span class="llm-dd-name">' + sel.text + '</span>' +
                '<span class="llm-dd-arrow">&#9660;</span>';

            // Options list
            var optsList = doc.createElement('div');
            optsList.className = 'llm-dd-options';

            items.forEach(function(item) {
                var opt = doc.createElement('div');
                opt.className = 'llm-dd-option' + (item.checked ? ' active' : '');
                opt.innerHTML =
                    '<img src="' + (LOGOS[item.text]||'') + '" alt="' + item.text + '"/>' +
                    '<span>' + item.text + '</span>' +
                    (item.checked ? '<span class="llm-dd-check">&#10003;</span>' : '');

                opt.addEventListener('click', function(e) {
                    e.stopPropagation();
                    item.input.click();
                    item.input.dispatchEvent(new Event('change', { bubbles: true }));
                    dd.querySelector('.llm-dd-logo').src = LOGOS[item.text] || '';
                    dd.querySelector('.llm-dd-name').textContent = item.text;
                    optsList.querySelectorAll('.llm-dd-option').forEach(function(o) {
                        o.classList.remove('active');
                        var chk = o.querySelector('.llm-dd-check');
                        if (chk) chk.remove();
                    });
                    opt.classList.add('active');
                    var chk = doc.createElement('span');
                    chk.className = 'llm-dd-check'; chk.innerHTML = '&#10003;';
                    opt.appendChild(chk);
                    dd.classList.remove('open');
                });
                optsList.appendChild(opt);
            });

            dd.appendChild(trigger);
            dd.appendChild(optsList);

            trigger.addEventListener('click', function(e) {
                e.stopPropagation();
                dd.classList.toggle('open');
            });

            // Close on outside click — add listener only once per document
            if (!doc._llmDdListener) {
                doc._llmDdListener = true;
                doc.addEventListener('click', function() {
                    var d = doc.querySelector('.llm-dd-container');
                    if (d) d.classList.remove('open');
                });
            }

            radioGroup.parentNode.insertBefore(dd, radioGroup.nextSibling);
        } catch(e) {}
    }

    function schedule() {
        clearTimeout(buildTimer);
        buildTimer = setTimeout(buildDropdown, 80);
    }

    schedule();
    new MutationObserver(schedule).observe(
        window.parent.document.body,
        { childList: true, subtree: true }
    );
})();
</script>
"""


def _inject_llm_dropdown():
    """Transform the hidden st.radio into a custom logo+name dropdown via JS."""
    components.html(_LLM_DROPDOWN_JS, height=0, scrolling=False)


# ---------------------------------------------------------------------------
# Stage 1 — Input
# ---------------------------------------------------------------------------

_COMPONENT_ICONS = {
    "role": "👤", "task": "🎯", "context": "🗂️", "examples": "📋",
    "output": "📄", "constraints": "🚧", "instructions": "📌",
    "persona": "👤", "objective": "🎯", "steps": "🔢", "output_format": "📄",
    "chain_of_thought": "🧠", "background": "🗂️",
    "research_question": "🔍", "time_scope": "📅", "source_types": "📚",
    "inclusions": "✅", "exclusions": "❌",
    "desired_output_format": "🖨️",
}


def render_input():
    _hero(
        "✦ Prompt Enhancement Tool",
        "From rough draft to expert-crafted prompt — optimized for your chosen AI model.",
        badge="Step 1 of 4 · Enter Prompt",
        show_share=True,
    )

    # Brief description
    st.markdown(
        '<div style="background:white;border:1.5px solid rgba(102,126,234,0.15);'
        'border-radius:12px;padding:1rem 1.5rem;margin-bottom:1.2rem;">'
        '<p style="margin:0;color:#374151;font-size:0.91rem;line-height:1.7;">'
        'Paste any rough prompt, pick your target LLM — '
        '<strong>Claude, ChatGPT, Gemini,</strong> or <strong>Perplexity</strong> — '
        'and this tool applies that model\'s official prompt engineering framework to '
        'restructure it. We\'ll analyze what\'s missing, ask targeted clarifying questions, '
        'and deliver a ready-to-paste enhanced prompt that gets you significantly better responses.'
        '</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Select your target LLM**")
    llm_keys = list(LLM_PROFILES.keys())
    selected_llm = st.radio(
        "Target LLM",
        options=llm_keys,
        index=llm_keys.index(st.session_state.target_llm),
        horizontal=True,
        label_visibility="collapsed",
        key="llm_radio",
    )
    if selected_llm:
        st.session_state.target_llm = selected_llm
    _inject_llm_dropdown()
    st.caption(f"**Style:** {LLM_PROFILES[st.session_state.target_llm]['style_hint']}")

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
                st.session_state.components = {}
                st.rerun()


# ---------------------------------------------------------------------------
# Stage 2 — Analysis
# ---------------------------------------------------------------------------


def render_analysis():
    _hero(
        "Prompt Analysis",
        "We've scanned your prompt against the framework for your chosen LLM. "
        "Review what's present and decide how to proceed.",
        badge="Step 2 of 4 · Analysis",
    )

    if st.button("← Back", key="back_analysis"):
        st.session_state.stage = "input"
        st.session_state.components = {}
        st.rerun()

    _llm_badge()

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
                            st.session_state.answers,
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
            help="We'll ask targeted questions — including about your desired output format.",
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

    _hero(
        "Let's fill in the gaps",
        f"Answering these questions helps us build the strongest possible prompt for {st.session_state.target_llm}.",
        badge=f"Step 3 of 4 · Question {idx + 1} of {total}",
    )

    if st.button("← Back", key="back_questions"):
        st.session_state.stage = "analysis"
        st.session_state.questions = []
        st.session_state.answers = {}
        st.session_state.current_q = 0
        st.session_state.draft = ""
        st.rerun()

    _llm_badge()

    st.progress(idx / total)
    st.divider()

    icon = _COMPONENT_ICONS.get(q["component"], "•")
    st.caption(f"Improving: {icon} **{component_label}**")
    st.subheader(q["question"])

    if q.get("inferred_example"):
        st.markdown("💡 **Based on your prompt, we suggest** *(click the copy icon to copy, or accept below):*")
        st.code(q["inferred_example"], language="text", wrap_lines=True)

        use_col, _ = st.columns([1, 3])
        with use_col:
            if st.button("✓ Accept & Continue →", key=f"use_{idx}", type="primary"):
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

    if st.button("← Back to Analysis", key="back_result"):
        st.session_state.stage = "analysis"
        st.session_state.enhanced_prompt = ""
        st.rerun()

    _llm_badge()

    enhanced = st.session_state.enhanced_prompt
    st.code(enhanced, language="text", wrap_lines=True)

    st.divider()

    with st.expander("Compare: Original vs Enhanced"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Original**")
            st.text(st.session_state.raw_prompt)
        with c2:
            st.markdown("**Enhanced**")
            st.text(enhanced)

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

# ---------------------------------------------------------------------------
# Footer — shown on every page
# ---------------------------------------------------------------------------

st.markdown(
    '<div style="margin-top:3rem;padding-top:1.2rem;'
    'border-top:1px solid rgba(102,126,234,0.18);'
    'text-align:center;color:#9ca3af;font-size:0.8rem;line-height:2.2;">'
    '&copy; 2026 Motasem AlShareef &nbsp;&middot;&nbsp; All rights reserved<br>'
    'Built with&nbsp;'
    '<img src="https://cdn.simpleicons.org/anthropic/9ca3af" height="13" '
    'style="vertical-align:middle;margin:0 3px 2px;" alt="Claude"/>'
    '&nbsp;<strong style="color:#6b7280;">Claude Code</strong>'
    '</div>',
    unsafe_allow_html=True,
)
