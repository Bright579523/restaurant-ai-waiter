"""
app.py — Streamlit UI for ReDi Restaurant AI Waiter
=====================================================
Interactive chat interface and menu explorer powered by:
- Hybrid Retrieval (Metadata Filtering + SentenceTransformer Cosine Similarity)
- Groq API (Qwen / Llama LLM)
- ReDi Restaurant Menu Database
"""

import base64
import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "agent") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "agent"))
if str(PROJECT_ROOT / "search_engine") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "search_engine"))

from agent import ReDiRestaurantAIAgent

# Page config
st.set_page_config(
    page_title="ReDi Restaurant AI Waiter",
    page_icon="🍛",
    layout="wide",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        padding: 24px 30px;
        border-radius: 16px;
        background: linear-gradient(135deg, #fff7ed 0%, #fef3c7 45%, #ecfccb 100%);
        border: 1px solid #fed7aa;
        margin-bottom: 20px;
    }
    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #1f2937;
        margin-bottom: 6px;
    }
    .main-subtitle {
        font-size: 16px;
        color: #4b5563;
        line-height: 1.5;
    }
    .badge-pill {
        display: inline-block;
        background: white;
        color: #9a3412;
        border: 1px solid #fdba74;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 8px;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Initializing ReDi AI Waiter & Knowledge Base...")
def get_agent():
    return ReDiRestaurantAIAgent()


agent = get_agent()

# Sidebar
with st.sidebar:
    st.header("🍛 ReDi AI Waiter")
    st.write("Your intelligent multilingual dining assistant for ReDi Restaurant.")

    st.divider()

    st.subheader("💡 Example Questions")
    examples = [
        "",
        "I want a vegetarian main dish under 15 euros with spinach",
        "What spicy chicken dishes do you have?",
        "Do you have vegan options?",
        "Welche Gerichte sind ohne Milch und Laktose?",
        "What are the lunch menu options under 12 euros?",
        "มีเมนูปลาที่ไม่เผ็ดแนะนำไหม",
        "What does allergen code F mean?",
    ]
    selected_example = st.selectbox("Select an example:", examples)

    if st.button("Use Example Question", use_container_width=True):
        if selected_example:
            st.session_state.pending_input = selected_example
            st.rerun()

    st.divider()

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_input = ""
        st.rerun()

    st.caption("Powered by Sentence-Transformers, Hybrid Vector Search, and Groq LLM.")

# Main Header Banner
st.markdown(
    """
    <div class="main-header">
        <div class="main-title">🍛 ReDi Restaurant AI Waiter</div>
        <div class="main-subtitle">
            Ask naturally about dishes, prices, ingredients, spice levels, allergens, and dietary preferences (English, German, Thai).
        </div>
        <div>
            <span class="badge-pill">🛡️ Allergy-Safe</span>
            <span class="badge-pill">🌱 Vegetarian & Vegan Aware</span>
            <span class="badge-pill">💰 Budget Conscious</span>
            <span class="badge-pill">🧠 Hybrid Vector RAG</span>
            <span class="badge-pill">🌐 Multilingual</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["💬 Chat with AI Waiter", "📋 Menu Explorer & PDF"])

with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! 👋 Welcome to **ReDi Restaurant**. "
                    "I am your AI Waiter. Tell me your budget, dietary requirements "
                    "(e.g., vegetarian, vegan, lactose-free), or what ingredients you are craving!"
                ),
            }
        ]

    if "pending_input" not in st.session_state:
        st.session_state.pending_input = ""

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle user input
    user_input = st.chat_input("Ask about dishes, ingredients, allergens, or recommendations...")
    active_prompt = user_input or st.session_state.pending_input

    if active_prompt:
        st.session_state.pending_input = ""

        # Append and display user message
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user"):
            st.markdown(active_prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Checking the kitchen & menu..."):
                try:
                    response = agent.chat(active_prompt)
                except Exception as e:
                    response = f"Sorry, I encountered an error: {e}"
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with tab2:
    st.subheader("📋 Menu Dataset Explorer")
    csv_path = PROJECT_ROOT / "data_output" / "redi_menu.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        col1, col2, col3 = st.columns(3)
        with col1:
            cat_filter = st.multiselect("Category", options=df["category"].dropna().unique())
        with col2:
            veg_filter = st.selectbox("Dietary", ["All", "Vegetarian Only", "Vegan Possible Only"])
        with col3:
            max_p = st.slider("Max Price (EUR)", min_value=2.0, max_value=30.0, value=30.0, step=0.5)

        filtered_df = df.copy()
        if cat_filter:
            filtered_df = filtered_df[filtered_df["category"].isin(cat_filter)]
        if veg_filter == "Vegetarian Only":
            filtered_df = filtered_df[filtered_df["is_vegetarian"].astype(str).str.lower() == "true"]
        elif veg_filter == "Vegan Possible Only":
            filtered_df = filtered_df[filtered_df["is_vegan_possible"].astype(str).str.lower() == "true"]
        filtered_df = filtered_df[filtered_df["price"] <= max_p]

        st.dataframe(
            filtered_df[["item_id", "name", "price", "category", "is_vegetarian", "allergen_codes", "description_de"]],
            use_container_width=True,
            height=350,
        )
    else:
        st.warning("Menu CSV dataset not found at data_output/redi_menu.csv")

    st.divider()
    st.subheader("📄 Original Menu PDF")
    pdf_path = PROJECT_ROOT / "raw_data" / "Menu of ReDi Restaurant.pdf"
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="700px"
            type="application/pdf">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("PDF menu file not found in raw_data folder.")
