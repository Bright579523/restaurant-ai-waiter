"""
app.py — Streamlit UI for the ReDi Restaurant AI Waiter
========================================================
Provides a premium luxury restaurant interface with:
  • Two-tier navigation header (REDI RESTAURANT)
  • Sidebar filters (dietary, meal type, price, allergens, ingredients)
  • Chat panel — conversational interaction with the AI waiter
  • Results panel — styled cards showing the retrieved matching menu items
"""

import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Setup import paths
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "search_engine") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "search_engine"))
if str(PROJECT_ROOT / "agent") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "agent"))

from agent import ReDiRestaurantAIAgent

# Load environment variables
load_dotenv()

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="ReDi Restaurant AI Waiter — Restaurant Recommendations",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
def inject_css():
    """Inject premium warm luxury restaurant styling matching ReDi Dining brand."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Outfit:wght@300;400;600;700&display=swap');

        .stApp {
            background-color: #FAF7F2;
            color: #2C2520;
            font-family: 'Outfit', sans-serif;
        }

        /* ── Header Titles ── */
        .main-title {
            color: #800020;
            font-family: 'Cinzel', serif;
            font-size: 2.8rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }
        .sub-title {
            color: #5C4D42 !important;
            font-size: 1.05rem;
            text-align: center;
            margin-bottom: 25px;
            font-style: italic;
        }

        /* ── Sidebar styling ── */
        [data-testid="stSidebar"] {
            background-color: #F4EFEA !important;
            border-right: 1px solid #E3D9CD;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] li {
            color: #4A3B32 !important;
            font-family: 'Outfit', sans-serif;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #800020 !important;
            font-family: 'Cinzel', serif;
        }

        /* ── Chat messages & Input ── */
        div[data-testid="stChatMessage"] {
            background-color: #F1EAE0 !important;
            border: 1px solid #E8DEC3;
            border-radius: 12px;
            margin-bottom: 12px;
        }
        div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] span, div[data-testid="stChatMessage"] div {
            color: #2C2520 !important;
        }
        div[data-testid="stChatInput"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E3C588 !important;
            border-radius: 12px !important;
        }
        div[data-testid="stChatInput"] textarea {
            color: #2C2520 !important;
        }

        /* ── Input controls (Dropdowns, listboxes, inputs, checkboxes) ── */
        [data-testid="stSidebar"], .stApp {
            --background-color: #FAF7F2 !important;
            --secondary-background-color: #FFFFFF !important;
            --text-color: #2C2520 !important;
            --primary-color: #800020 !important;
        }

        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #2C2520 !important;
            border-color: #E3C588 !important;
        }
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
            background-color: #F1EAE0 !important;
            color: #2C2520 !important;
            border: 1px solid #E3C588 !important;
        }

        /* Sliders */
        div[data-testid="stSlider"] [data-testid="stSliderTrack"] > div > div {
            background-color: #800020 !important;
        }

        /* Buttons styling */
        .stButton button, .stDownloadButton button {
            background-color: #800020 !important;
            color: #FFFFFF !important;
            border: 1px solid #E3C588 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
            font-weight: 600;
        }
        .stButton button:hover, .stDownloadButton button:hover {
            background-color: #5C4D42 !important;
            color: #FAF7F2 !important;
            border-color: #FAF7F2 !important;
        }
        .stButton button p, .stDownloadButton button p {
            color: #FFFFFF !important;
        }

        /* ── Menu result cards ── */
        .menu-card {
            background-color: #FFFFFF;
            border: 1.5px solid #E3C588;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 2px 8px rgba(128, 0, 32, 0.04);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .menu-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(128, 0, 32, 0.08);
        }
        .badge-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }
        .badge-item {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
        }
        .badge-lunch {
            background-color: #FFF2CC;
            color: #7F6000;
            border: 1px solid #FFE599;
        }
        .badge-veg {
            background-color: #E2EFDA;
            color: #385723;
            border: 1px solid #C5E0B4;
        }
        .badge-vegan {
            background-color: #D9E1F2;
            color: #203864;
            border: 1px solid #B4C6E7;
        }
        .badge-allergen {
            background-color: #FCE4D6;
            color: #C55A11;
            border: 1px solid #F8CBAD;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# ── Load Agent ───────────────────────────────────────────────
@st.cache_resource(show_spinner="Initializing ReDi AI Waiter & Knowledge Base...")
def load_agent():
    return ReDiRestaurantAIAgent()


agent = load_agent()

# ── Sidebar Filters ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### ReDi Restaurant Menu Filters 🍛")

    st.subheader("Quick Dietary Preferences")
    is_veg = st.checkbox("🍀 Vegetarian Only")
    is_vegan = st.checkbox("🌱 Vegan Options Only")
    is_lunch = st.checkbox("🍛 Lunch Menu (Mittagsmenü)")

    st.markdown("---")
    meal_map = {
        "All Types": None,
        "Main Dishes 🍛": "main",
        "Soups & Salate 🥣": "starter",
        "Naan & Roti 🫓": "side",
        "Desserts 🍨": "dessert",
        "Drinks 🍹": "drink",
    }
    selected_meal = st.selectbox("Meal Category", list(meal_map.keys()))
    meal_type = meal_map[selected_meal]

    max_price = st.slider(
        "Maximum Price (EUR)", min_value=2.0, max_value=30.0, value=30.0, step=0.5
    )

    st.subheader("Exclude Allergens")
    allergen_map = {
        "Gluten (wheat/naan) [a]": "a",
        "Crustaceans [b]": "b",
        "Egg [c]": "c",
        "Fish [d]": "d",
        "Soybeans [e]": "e",
        "Milk / Lactose [f]": "f",
        "Nuts / Cashews [g]": "g",
        "Mustard (Senf) [i]": "i",
        "Sesame [j]": "j",
    }
    selected_allergens = st.multiselect(
        "Exclude items containing:", list(allergen_map.keys()), placeholder="Choose options"
    )
    excluded_codes = [allergen_map[a] for a in selected_allergens]

    st.subheader("Ingredient Focus")
    ingredients = ["chicken", "lamb", "fish", "shrimp", "duck", "paneer"]
    contains_ing = st.multiselect("Must contain:", ingredients)
    excludes_ing = st.multiselect("Must NOT contain:", ingredients)

    # Compile sidebar filters
    sidebar_filters = {}
    if is_veg:
        sidebar_filters["is_vegetarian"] = True
    if is_vegan:
        sidebar_filters["is_vegan_possible"] = True
    if is_lunch:
        sidebar_filters["is_lunch_menu"] = True
    if meal_type:
        sidebar_filters["meal_type"] = meal_type
    if max_price < 30.0:
        sidebar_filters["max_price"] = max_price
    if excluded_codes:
        sidebar_filters["exclude_allergens"] = excluded_codes
    if contains_ing:
        sidebar_filters["contains_ingredients"] = contains_ing
    if excludes_ing:
        sidebar_filters["exclude_ingredients"] = excludes_ing

    st.markdown("---")
    st.subheader("System Actions & Resources")

    if st.button("🔄 Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Welcome to ReDi Restaurant! 🍛 I am your digital waiter today. "
                    "Ask me anything about our menu, e.g., "
                    "'What are your popular vegetarian dishes?' or "
                    "'Suggest a mild chicken curry.'"
                ),
            }
        ]
        if "current_results" in st.session_state:
            st.session_state.current_results = []
        st.rerun()

    pdf_filename = PROJECT_ROOT / "raw_data" / "Menu of ReDi Restaurant.pdf"
    if pdf_filename.exists():
        with open(pdf_filename, "rb") as f:
            pdf_data = f.read()
        st.download_button(
            label="📄 Download Original PDF Menu",
            data=pdf_data,
            file_name="ReDi_Restaurant_Menu.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# ── Header Banner Mockup ──────────────────────────────────────
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #800020; padding-bottom: 10px; margin-bottom: 25px;">
        <span style="font-family: 'Cinzel', serif; font-size: 1.8rem; font-weight: 700; color: #800020; letter-spacing: 2px;">REDI RESTAURANT</span>
        <div style="display: flex; gap: 20px; font-size: 0.9rem; font-weight: 700; color: #5C4D42; font-family: 'Outfit', sans-serif;">
            <span style="cursor: pointer;">HOME</span>
            <span style="cursor: pointer;">MENU</span>
            <span style="cursor: pointer;">RESERVATIONS</span>
            <span style="color: #800020; border-bottom: 2px solid #800020; padding-bottom: 2px;">AI DINING ASSISTANT</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 class='main-title'>ReDi Restaurant AI Waiter</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-title'>"
    "Welcome to ReDi Fine Indian Dining. "
    "Consult our digital dining assistant or adjust preferences below."
    "</div>",
    unsafe_allow_html=True,
)


# ── Render Menu Card Helper ──────────────────────────────────
def render_menu_card(item: dict):
    score = item.get("similarity_score", 0.0)
    match_pct = min(100, int((score + 0.1) * 100)) if score > 0 else 0

    if match_pct >= 90:
        stars_html = "⭐⭐⭐⭐⭐ <span style='color:#385723; font-size:0.8rem; font-weight:700;'>(EXCELLENT MATCH)</span>"
    elif match_pct >= 75:
        stars_html = "⭐⭐⭐⭐ <span style='color:#7F6000; font-size:0.8rem; font-weight:700;'>(GREAT MATCH)</span>"
    else:
        stars_html = "⭐⭐⭐ <span style='color:#7A695E; font-size:0.8rem; font-weight:700;'>(GOOD MATCH)</span>"

    badges = []
    if item.get("is_lunch_menu"):
        badges.append("<span class='badge-item badge-lunch'>🍛 LUNCH OFFER</span>")
    if item.get("is_vegetarian"):
        badges.append("<span class='badge-item badge-veg'>🍀 VEG</span>")
    if item.get("is_vegan_possible"):
        badges.append("<span class='badge-item badge-vegan'>🌱 VEGAN</span>")
    if item.get("allergen_codes"):
        badges.append(f"<span class='badge-item badge-allergen'>Allergens: {item['allergen_codes']}</span>")

    st.markdown(
        f"""
        <div class='menu-card'>
            <div style='display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;'>
                <h4 style='color: #800020; margin: 0; font-family: Outfit, sans-serif; font-size: 1.15rem; font-weight: 700;'>{item['item_id']}. {item['name']}</h4>
                <span style='color: #800020; font-weight: 700; background: #FAF7F2; border: 1px solid #E8DEC3; padding: 2px 8px; border-radius: 6px; font-size: 0.95rem;'>{item['price']:.2f} €</span>
            </div>
            <div style='color: #5C4D42; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;'>
                {item['category']} &nbsp;|&nbsp; {stars_html}
            </div>
            <div style='color: #4A3B32; font-size: 0.9rem; line-height: 1.4; margin-bottom: 10px;'>{item['description_de']}</div>
            <div class='badge-container'>{"".join(badges)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Two-Column Layout ────────────────────────────────────────
col_chat, col_results = st.columns([3, 2])

# Session-state initialisation
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Welcome to ReDi Restaurant! 🍛 I am your digital waiter today. "
                "Ask me anything about our menu, e.g., "
                "'What are your popular vegetarian dishes?' or "
                "'Suggest a mild chicken curry.'"
            ),
        }
    ]

# ── Left Column: Chat ────────────────────────────────────────
with col_chat:
    st.markdown("### Chat with the Waiter 💬")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask the waiter...")
    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Checking the kitchen & menu..."):
                # 1. Parse intent
                parsed = agent.parse_user_intent(user_query)

                # 2. Merge user intent filters with active sidebar filters
                active_filters = dict(sidebar_filters)
                parsed_dict = parsed.filters.model_dump(exclude_none=True)
                active_filters.update(parsed_dict)

                # 3. Retrieve matching items
                results = agent.search_engine.search(
                    query=parsed.search_query,
                    filters=active_filters,
                    top_k=3,
                )
                st.session_state.current_results = results

                # 4. Generate waiter response
                response = agent.generate_recommendation(user_query, parsed, results)
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# ── Right Column: Matching Dishes ────────────────────────────
with col_results:
    st.markdown("### Matching Dishes 🍽️")

    current_results = st.session_state.get("current_results", [])

    # If no search has been performed yet, show top items matching sidebar filters
    if not current_results:
        current_results = agent.search_engine.search(
            query="popular dishes", filters=sidebar_filters, top_k=3
        )

    if not current_results:
        st.info(
            "No matching items found for the active filters. "
            "Try adjusting the sidebar or your search terms."
        )
    else:
        for item in current_results:
            render_menu_card(item)
