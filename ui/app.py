"""
Omni-IPS — Production-Grade Streamlit Chat Interface.

Provides a clean, professional web UI for interacting with the
Neuro-Symbolic & GraphRAG Multi-domain Intelligent Problem Solver.
"""

import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
DOMAINS = ["chemistry", "geometry", "algebra"]
DOMAIN_ICONS = {"chemistry": "🧪", "geometry": "📐", "algebra": "🔢"}
DOMAIN_PLACEHOLDERS = {
    "chemistry": "e.g. I have sodium and water, how do I make sodium hydroxide?",
    "geometry": "e.g. If Congruent(AB,CD) and Congruent(CD,EF), prove Congruent(AB,EF)",
    "algebra": "e.g. Given x+2=5, Subtract(2,both_sides), find x=3",
}


def check_backend_health() -> dict:
    """Check FastAPI backend connectivity with retry."""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def solve_query(query: str, domain: str) -> dict:
    """POST a natural language query to the GraphRAG solve endpoint."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/solve",
            json={"query": query, "domain": domain},
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "❌ Cannot reach backend. Please ensure the API server is running."}
    except requests.exceptions.Timeout:
        return {"error": "⏱️ Request timed out. The solver may be processing a complex query."}
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return {"error": f"⚠️ Backend error: {detail}"}
    except Exception as e:
        return {"error": f"❌ Unexpected error: {str(e)}"}


def explain_proof(query: str, domain: str, execution_trace: list, goal_reached: bool = True):
    """POST to the explain/stream endpoint and yield rich educational markdown chunks."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/explain/stream",
            json={
                "query": query,
                "domain": domain,
                "execution_trace": execution_trace,
                "goal_reached": goal_reached
            },
            stream=True,
            timeout=120
        )
        resp.raise_for_status()
        
        import codecs
        decoder = codecs.getincrementaldecoder('utf-8')()
        for raw_chunk in resp.iter_content(chunk_size=1024):
            if raw_chunk:
                chunk = decoder.decode(raw_chunk)
                for char in chunk:
                    yield char
                    time.sleep(0.002)  # Smooth, fluid typing speed (2ms per character)
        
        chunk = decoder.decode(b'', final=True)
        for char in chunk:
            yield char
            time.sleep(0.002)
    except Exception as e:
        yield f"\n\n*Explanation stream error: {str(e)}*"


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Omni-IPS — Intelligent Problem Solver",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Custom CSS for premium look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown label {
        color: #e0e0ff !important;
    }
    
    /* Status badge */
    .status-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 4px 0;
    }
    .status-online {
        background: linear-gradient(135deg, #00c853, #00e676);
        color: #003300;
    }
    .status-offline {
        background: linear-gradient(135deg, #ff1744, #ff5252);
        color: #fff;
    }
    
    /* Goal badge */
    .goal-badge {
        padding: 8px 18px;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 700;
        display: inline-block;
        margin: 8px 0;
    }
    .goal-reached {
        background: linear-gradient(135deg, #00c853, #69f0ae);
        color: #003300;
    }
    .goal-missed {
        background: linear-gradient(135deg, #ff6f00, #ffab40);
        color: #3e2700;
    }
    
    /* Trace path */
    .trace-path {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #0f3460;
        border-radius: 10px;
        padding: 14px 20px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 1rem;
        color: #e94560;
        letter-spacing: 1px;
    }
    
    /* Fact chips */
    .fact-chip {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 3px 4px;
    }
    
    /* Header */
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .main-header h1 {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #888;
        font-size: 0.95rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧠 Omni-IPS")
    st.markdown("**Neuro-Symbolic & GraphRAG**  \nIntelligent Problem Solver")
    st.markdown("---")
    
    # Domain selector
    st.markdown("### 🎯 Target Domain")
    domain = st.selectbox(
        "Select domain",
        DOMAINS,
        format_func=lambda d: f"{DOMAIN_ICONS.get(d, '📌')} {d.capitalize()}",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Backend config
    st.markdown("### ⚙️ Backend")
    backend_url_input = st.text_input("API URL", value=BACKEND_URL, label_visibility="collapsed")
    if backend_url_input != BACKEND_URL:
        BACKEND_URL = backend_url_input
    
    # Health check
    health = check_backend_health()
    if health:
        neo4j_status = "✅" if health.get("neo4j_connected") else "⚠️"
        st.markdown(
            f'<span class="status-badge status-online">● System Online</span>',
            unsafe_allow_html=True
        )
        st.markdown(f"- Neo4j: {neo4j_status}")
        qdrant_info = health.get("environment", {})
        st.markdown(f"- Qdrant: `{qdrant_info.get('qdrant_host', '?')}:{qdrant_info.get('qdrant_port', '?')}`")
    else:
        st.markdown(
            '<span class="status-badge status-offline">● Offline</span>',
            unsafe_allow_html=True
        )
        st.caption("Backend unreachable. Start with `make run-server`")
    
    st.markdown("---")
    st.markdown("### 📖 Quick Guide")
    st.markdown(f"*{DOMAIN_PLACEHOLDERS.get(domain, '')}*")
    
    st.markdown("---")
    st.caption("Powered by **Qdrant** + **Neo4j** + **LangChain**")


# ---------------------------------------------------------------------------
# Main Chat Area
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🧠 Omni-IPS Chat</h1>
    <p>Ask questions in natural language — the engine maps them to formal logic and solves them.</p>
</div>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar")):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            # Assistant response
            if "error" in msg:
                st.error(msg["error"])
            else:
                result = msg.get("result", {})
                explanation = msg.get("explanation", "")
                
                # Goal status badge
                goal_reached = result.get("goal_reached", False)
                if goal_reached:
                    st.markdown('<div class="goal-badge goal-reached">✅ Goal Reached!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="goal-badge goal-missed">⚠️ Goal Not Reached</div>', unsafe_allow_html=True)
                
                # GraphRAG Processing Info expander
                with st.expander("🔍 GraphRAG Processing Info", expanded=False):
                    # Mapped facts
                    st.markdown("**Qdrant-Mapped Initial Facts:**")
                    mapped_facts = result.get("mapped_initial_facts", [])
                    if mapped_facts:
                        chips = " ".join([f'<span class="fact-chip">{f}</span>' for f in mapped_facts])
                        st.markdown(chips, unsafe_allow_html=True)
                    else:
                        st.caption("No facts mapped.")
                    
                    # Mapped goal
                    st.markdown(f"**Mapped Goal:** `{result.get('mapped_goal', 'N/A')}`")
                    
                    # Raw trace data
                    st.markdown("**Execution Trace (Raw):**")
                    trace = result.get("execution_trace", [])
                    if trace:
                        for step in trace:
                            st.code(
                                f"Rule: {step.get('rule_id', '?')} → {step.get('fired_rule_repr', '?')}\n"
                                f"New facts: {step.get('new_facts', [])}",
                                language="text"
                            )
                    else:
                        st.caption("No rules fired.")
                    
                    # All known facts
                    st.markdown("**Final Known Facts:**")
                    known = result.get("known_facts", [])
                    if known:
                        st.code(", ".join(known), language="text")
                
                # Logical trace path
                rule_ids = result.get("applied_rule_ids", [])
                if rule_ids:
                    trace_str = " → ".join(rule_ids)
                    st.markdown(f'<div class="trace-path">📋 Proof Path: {trace_str}</div>', unsafe_allow_html=True)
                
                # Rich LLM Explanation
                st.markdown("---")
                if explanation:
                    st.markdown(explanation)
                else:
                    st.info("No explanation generated.")

# Chat input at the bottom
user_input = st.chat_input(
    placeholder=DOMAIN_PLACEHOLDERS.get(domain, "Type your query...")
)

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "avatar": "👤"
    })
    st.rerun()

# Assistant turn execution
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_msg = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("🔄 Routing through Neuro-Symbolic pipeline..."):
            result = solve_query(user_msg, domain)
        
        if "error" in result:
            error_msg = result["error"]
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "avatar": "🧠",
                "error": error_msg
            })
            st.rerun()
        else:
            # 1. Goal status badge
            goal_reached = result.get("goal_reached", False)
            if goal_reached:
                st.markdown('<div class="goal-badge goal-reached">✅ Goal Reached!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="goal-badge goal-missed">⚠️ Goal Not Reached</div>', unsafe_allow_html=True)
            
            # 2. GraphRAG Processing Info expander
            with st.expander("🔍 GraphRAG Processing Info", expanded=False):
                # Mapped facts
                st.markdown("**Qdrant-Mapped Initial Facts:**")
                mapped_facts = result.get("mapped_initial_facts", [])
                if mapped_facts:
                    chips = " ".join([f'<span class="fact-chip">{f}</span>' for f in mapped_facts])
                    st.markdown(chips, unsafe_allow_html=True)
                else:
                    st.caption("No facts mapped.")
                
                # Mapped goal
                st.markdown(f"**Mapped Goal:** `{result.get('mapped_goal', 'N/A')}`")
                
                # Raw trace data
                st.markdown("**Execution Trace (Raw):**")
                trace = result.get("execution_trace", [])
                if trace:
                    for step in trace:
                        st.code(
                            f"Rule: {step.get('rule_id', '?')} → {step.get('fired_rule_repr', '?')}\n"
                            f"New facts: {step.get('new_facts', [])}",
                            language="text"
                        )
                else:
                    st.caption("No rules fired.")
                
                # All known facts
                st.markdown("**Final Known Facts:**")
                known = result.get("known_facts", [])
                if known:
                    st.code(", ".join(known), language="text")
            
            # 3. Logical trace path
            rule_ids = result.get("applied_rule_ids", [])
            if rule_ids:
                trace_str = " → ".join(rule_ids)
                st.markdown(f'<div class="trace-path">📋 Proof Path: {trace_str}</div>', unsafe_allow_html=True)
            
            # 4. Rich LLM Explanation (Live streaming)
            st.markdown("---")
            explanation_str = ""
            trace_data = result.get("execution_trace", [])
            if trace_data:
                explanation_generator = explain_proof(user_msg, domain, trace_data, goal_reached)
                explanation_str = st.write_stream(explanation_generator)
            else:
                explanation_str = (
                    "No inference steps were generated. The solver could not find a valid "
                    "proof path with the available rules. Try rephrasing your query or "
                    "ensuring the knowledge base is populated (`make embed-knowledge`)."
                )
                st.info(explanation_str)
            
            # Save the complete result in the session state
            st.session_state.messages.append({
                "role": "assistant",
                "avatar": "🧠",
                "result": result,
                "explanation": explanation_str
            })
            st.rerun()
