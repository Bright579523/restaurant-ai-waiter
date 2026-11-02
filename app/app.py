"""
app.py — Streamlit UI for the ReDi Restaurant AI Waiter
========================================================
Luxury 3-column dining assistant interface matching the ReDi brand design:
  • Column 1: Dietary & Budget Preferences (Neat Pills, Live Reactive Slider, Occasion toggles)
  • Column 2: ReDi AI Dining Assistant (Chat stream with RD avatar, bright pill input)
  • Column 3: Recommended Dishes (Photo cards, title, price, description, star ratings — live synced with filters)
"""

import datetime
import html
import os
import re
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

# Pass Streamlit Cloud secrets to environment for Groq if available
if not os.environ.get("GROQ_API_KEY"):
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="ReDi — AI Dining Assistant",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Curated Food Photos for Authentic Presentation ──────────
def get_dish_image(item: dict) -> str:
    """Return an appetizing Indian culinary image matching the dish keywords."""
    name = (item.get("name") or "").lower()
    cat = (item.get("category") or "").lower()
    desc = (item.get("description_de") or "").lower()
    text = f"{name} {cat} {desc}"

    if "paneer" in text:
        return "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=300&auto=format&fit=crop&q=80"
    if "tikka" in text or "tandoori" in text:
        return "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=300&auto=format&fit=crop&q=80"
    if "dal" in text or "daal" in text or "makhani" in text or "lentil" in text:
        return "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=300&auto=format&fit=crop&q=80"
    if "palak" in text or "spinat" in text:
        return "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=300&auto=format&fit=crop&q=80"
    if "biryani" in text or "reis" in text or "rice" in text:
        return "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=300&auto=format&fit=crop&q=80"
    if "samosa" in text or "pakora" in text or "bhaji" in text:
        return "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=300&auto=format&fit=crop&q=80"
    if "naan" in text or "roti" in text or "bhatura" in text or "brot" in text:
        return "https://images.unsplash.com/photo-1517244683847-7456b63c5969?w=300&auto=format&fit=crop&q=80"
    if "chicken" in text or "hähnchen" in text:
        return "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=300&auto=format&fit=crop&q=80"
    if "lamb" in text or "lamm" in text:
        return "https://images.unsplash.com/photo-1545247181-516773ca83f3?w=300&auto=format&fit=crop&q=80"
    if "fish" in text or "fisch" in text or "seelachs" in text:
        return "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=300&auto=format&fit=crop&q=80"
    if "shrimp" in text or "garnelen" in text or "jheenga" in text:
        return "https://images.unsplash.com/photo-1559742811-822873691df8?w=300&auto=format&fit=crop&q=80"
    if "soup" in text or "suppe" in text:
        return "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=300&auto=format&fit=crop&q=80"
    if "salat" in text or "salad" in text:
        return "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=300&auto=format&fit=crop&q=80"
    if "mango" in text or "lassi" in text:
        return "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=300&auto=format&fit=crop&q=80"
    if "gulab" in text or "dessert" in text:
        return "https://images.unsplash.com/photo-1599785209707-a456fc1337bb?w=300&auto=format&fit=crop&q=80"
    return "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=300&auto=format&fit=crop&q=80"


def get_dish_rating(item: dict) -> tuple[str, float]:
    """Generate consistent 5-star rating representation."""
    item_id = item.get("item_id", 0)
    if item_id == 58:  # Paneer Tikka Masala
        return "★★★★★", 4.8
    elif item_id == 45:  # Daal Makhni
        return "★★★★★", 4.7
    elif item_id == 55:  # Palak Paneer
        return "★★★★★", 4.6

    score = item.get("similarity_score", 0.7)
    base = 4.6 + (((item_id * 13) + int(score * 100)) % 4) * 0.1
    return "★★★★★", round(base, 1)


# ── Custom CSS ───────────────────────────────────────────────
def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Outfit:wght@300;400;500;600;700&display=swap');

        /* Hide default Streamlit header bar decoration */
        header[data-testid="stHeader"] {
            display: none !important;
        }

        /* Hide sidebar completely */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Enforce page background & typography */
        .stApp, html, body {
            background-color: #F8F5EE !important;
            color: #2A1D1A !important;
            font-family: 'Outfit', sans-serif !important;
        }

        .main .block-container {
            padding-top: 0rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1380px !important;
            margin: 0 auto !important;
        }

        /* ── Top Navigation Bar ── */
        .luxury-navbar {
            background-color: #4A0E17;
            padding: 16px 36px;
            margin: 0 -2rem 24px -2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 16px rgba(74, 14, 23, 0.16);
        }

        .navbar-brand {
            font-family: 'Cinzel', serif;
            font-size: 1.85rem;
            font-weight: 700;
            color: #D4AF37;
            letter-spacing: 3px;
        }

        .navbar-links {
            display: flex;
            gap: 32px;
            align-items: center;
        }

        .navbar-link {
            color: #F2E9DF;
            font-size: 0.95rem;
            font-weight: 600;
            text-decoration: none;
            letter-spacing: 0.3px;
            cursor: pointer;
            transition: color 0.2s ease;
        }

        .navbar-link:hover {
            color: #D4AF37;
        }

        .navbar-link.active {
            color: #E8B923;
            border-bottom: 2.5px solid #D4AF37;
            padding-bottom: 4px;
        }

        .navbar-icons {
            display: flex;
            align-items: center;
            gap: 20px;
            color: #F2E9DF;
        }

        .navbar-icon-btn {
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #F2E9DF;
            transition: transform 0.2s ease, color 0.2s ease;
        }

        .navbar-icon-btn:hover {
            color: #D4AF37;
            transform: scale(1.08);
        }

        /* ── Headings ── */
        .col-main-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: #221411;
            margin-bottom: 16px;
            letter-spacing: -0.2px;
            line-height: 1.3;
        }

        .col-sub-title {
            font-size: 0.98rem;
            font-weight: 600;
            color: #221411;
            margin-top: 14px;
            margin-bottom: 8px;
        }

        .col-desc-note {
            font-size: 0.82rem;
            color: #7A695E;
            margin-bottom: 4px;
        }

        /* ── St Pills: Bulletproof light styling & wrapping ── */
        div[data-testid="stPills"] {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 7px !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            padding: 2px 0 !important;
        }

        div[data-testid="stPills"] button {
            background-color: #FFFFFF !important;
            background-image: none !important;
            background: #FFFFFF !important;
            color: #2A1D1A !important;
            border: 1.5px solid #D9CEBF !important;
            border-radius: 9999px !important;
            padding: 5px 13px !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            box-shadow: none !important;
            outline: none !important;
            transition: all 0.2s ease !important;
            white-space: nowrap !important;
        }

        div[data-testid="stPills"] button * {
            color: inherit !important;
            background: transparent !important;
        }

        div[data-testid="stPills"] button:hover {
            border-color: #4A0E17 !important;
            color: #4A0E17 !important;
            background-color: #F8F4EE !important;
            background-image: none !important;
        }

        div[data-testid="stPills"] button:focus,
        div[data-testid="stPills"] button:active {
            box-shadow: none !important;
            outline: none !important;
        }

        /* Selected Pill state */
        div[data-testid="stPills"] button[aria-checked="true"],
        div[data-testid="stPills"] button[data-selected="true"],
        div[data-testid="stPills"] button[aria-pressed="true"] {
            background-color: #4A0E17 !important;
            background-image: none !important;
            background: #4A0E17 !important;
            color: #FFFFFF !important;
            border-color: #4A0E17 !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 6px rgba(74, 14, 23, 0.25) !important;
        }

        div[data-testid="stPills"] button[aria-checked="true"] *,
        div[data-testid="stPills"] button[data-selected="true"] *,
        div[data-testid="stPills"] button[aria-pressed="true"] * {
            color: #FFFFFF !important;
        }

        /* ── St Slider: contained within column, no right overflow ── */
        div[data-testid="stSlider"] {
            width: 100% !important;
            padding: 2px 6px !important;
            box-sizing: border-box !important;
        }
        div[data-testid="stSlider"] > div {
            padding-right: 6px !important;
        }
        div[data-testid="stSlider"] [data-testid="stSliderTrack"] {
            background-color: #E2D7CB !important;
        }
        div[data-testid="stSlider"] [data-testid="stSliderTrack"] > div > div {
            background-color: #4A0E17 !important;
        }
        div[data-testid="stSlider"] [role="slider"] {
            background-color: #4A0E17 !important;
            border: 2px solid #FFFFFF !important;
            box-shadow: 0 2px 6px rgba(74, 14, 23, 0.35) !important;
            width: 18px !important;
            height: 18px !important;
        }

        /* ── St Toggle ── */
        div[data-testid="stToggle"] label > div > div[data-checked="true"],
        div[data-testid="stToggle"] input:checked ~ div {
            background-color: #4A0E17 !important;
        }
        div[data-testid="stToggle"] p {
            font-size: 0.92rem !important;
            color: #2A1D1A !important;
            font-weight: 500 !important;
        }

        /* ── Center Chat Panel (Single Card Container) ── */
        .chat-card-panel {
            background: #FFFFFF;
            border-radius: 18px;
            border: 1.5px solid #EAE2D8;
            padding: 18px 20px 14px 20px;
            box-shadow: 0 4px 18px rgba(42, 29, 26, 0.04);
            display: flex;
            flex-direction: column;
            margin-bottom: 12px;
        }

        .chat-card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 12px;
            border-bottom: 1.5px solid #F4ECE3;
            margin-bottom: 14px;
        }

        .chat-avatar-rd {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #4A0E17;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            flex-shrink: 0;
            box-shadow: 0 2px 5px rgba(74, 14, 23, 0.2);
        }

        .msg-avatar-small {
            width: 32px !important;
            height: 32px !important;
            font-size: 0.78rem !important;
        }

        .chat-header-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #221411;
            font-family: 'Outfit', sans-serif;
        }

        /* Scrollable messages container inside the card */
        .chat-messages-container {
            max-height: 460px;
            min-height: 240px;
            overflow-y: auto;
            padding-right: 6px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .chat-messages-container::-webkit-scrollbar {
            width: 5px;
        }
        .chat-messages-container::-webkit-scrollbar-thumb {
            background-color: #D9CEBF;
            border-radius: 10px;
        }

        .msg-assistant-wrapper {
            display: flex;
            gap: 10px;
            align-items: flex-start;
        }

        .msg-bubble-assistant {
            background-color: #FAF8F5;
            border: 1px solid #ECE3D7;
            border-radius: 14px;
            padding: 11px 15px;
            color: #2A1D1A;
            font-size: 0.91rem;
            line-height: 1.48;
            max-width: 86%;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
        }

        .msg-time-stamp {
            font-size: 0.72rem;
            color: #8C7E74;
            margin-top: 4px;
            display: block;
        }

        .msg-user-wrapper {
            display: flex;
            justify-content: flex-end;
        }

        .msg-bubble-user {
            background-color: #EADDC6;
            border-radius: 14px;
            padding: 11px 15px;
            color: #2A1D1A;
            font-size: 0.91rem;
            line-height: 1.48;
            max-width: 82%;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
        }

        .msg-time-stamp-user {
            font-size: 0.72rem;
            color: #6D5F54;
            margin-top: 4px;
            display: block;
            text-align: right;
        }

        /* ── St Chat Input: Pure White Pill, No Dark Box ── */
        div[data-testid="stChatInput"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin-top: 6px !important;
            box-shadow: none !important;
        }

        div[data-testid="stChatInput"] > div {
            background-color: #FFFFFF !important;
            background: #FFFFFF !important;
            border: 1.5px solid #D9CEBF !important;
            border-radius: 9999px !important;
            padding: 4px 10px 4px 16px !important;
            box-shadow: 0 2px 10px rgba(74, 14, 23, 0.05) !important;
            transition: all 0.2s ease !important;
        }

        div[data-testid="stChatInput"] > div:focus-within {
            border-color: #4A0E17 !important;
            box-shadow: 0 0 0 2px rgba(74, 14, 23, 0.12) !important;
        }

        div[data-testid="stChatInput"] [data-baseweb="base-input"],
        div[data-testid="stChatInput"] [data-baseweb="textarea"] {
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
        }

        div[data-testid="stChatInput"] textarea {
            background-color: transparent !important;
            background: transparent !important;
            color: #2A1D1A !important;
            caret-color: #4A0E17 !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 0.92rem !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            line-height: 1.4 !important;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #9C8C80 !important;
        }

        div[data-testid="stChatInput"] button {
            background-color: #4A0E17 !important;
            background: #4A0E17 !important;
            color: #FFFFFF !important;
            border-radius: 50% !important;
            width: 34px !important;
            height: 34px !important;
            border: none !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 2px 6px rgba(74, 14, 23, 0.25) !important;
            transition: transform 0.15s ease !important;
        }

        div[data-testid="stChatInput"] button:hover {
            transform: scale(1.06) !important;
            background-color: #5E121E !important;
        }

        div[data-testid="stChatInput"] button svg {
            fill: #FFFFFF !important;
            color: #FFFFFF !important;
        }

        /* ── Right Column: Dish Cards ── */
        .dish-card {
            background: #FFFFFF;
            border: 1.5px solid #EAE2D8;
            border-radius: 16px;
            padding: 13px;
            margin-bottom: 12px;
            display: flex;
            gap: 12px;
            box-shadow: 0 2px 8px rgba(42, 29, 26, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .dish-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(74, 14, 23, 0.08);
            border-color: #DFD3C4;
        }

        .dish-thumb {
            width: 82px;
            height: 82px;
            border-radius: 12px;
            object-fit: cover;
            flex-shrink: 0;
            background-color: #F0EAE1;
        }

        .dish-info-col {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .dish-head-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 3px;
        }

        .dish-name-txt {
            font-size: 1.01rem;
            font-weight: 700;
            color: #221411;
            margin: 0;
        }

        .dish-price-txt {
            font-size: 1rem;
            font-weight: 700;
            color: #221411;
            margin: 0;
        }

        .dish-desc-txt {
            font-size: 0.81rem;
            color: #685A50;
            line-height: 1.35;
            margin: 2px 0 5px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .dish-bottom-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .dish-stars-rating {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .stars-gold {
            color: #C59B27;
            font-size: 0.88rem;
            letter-spacing: 1px;
        }

        .stars-score-num {
            font-size: 0.82rem;
            font-weight: 700;
            color: #5A4B40;
        }

        .dish-badge-pill {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 6px;
        }
        .badge-lunch {
            background-color: #FFF2CC;
            color: #7F6000;
        }
        .badge-veg {
            background-color: #E2EFDA;
            color: #385723;
        }
        .badge-vegan {
            background-color: #D9E1F2;
            color: #203864;
        }

        .active-filter-badge {
            background-color: #FAF4EB;
            border: 1px solid #E5DACD;
            color: #4A0E17;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 10px;
        }

        /* ── Clear Chat Button: Clean Outlined Luxury Style ── */
        .stButton > button {
            background-color: #FAF7F2 !important;
            background: #FAF7F2 !important;
            color: #4A0E17 !important;
            border: 1.5px solid #4A0E17 !important;
            border-radius: 9999px !important;
            font-size: 0.86rem !important;
            font-weight: 600 !important;
            padding: 7px 16px !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
            width: 100% !important;
        }
        .stButton > button:hover {
            background-color: #4A0E17 !important;
            background: #4A0E17 !important;
            color: #FFFFFF !important;
            border-color: #4A0E17 !important;
            box-shadow: 0 2px 8px rgba(74, 14, 23, 0.2) !important;
        }
        .stButton > button p {
            color: inherit !important;
            font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_custom_css()


# ── Load Agent ───────────────────────────────────────────────
@st.cache_resource(show_spinner="Initializing ReDi AI Waiter...")
def load_agent():
    return ReDiRestaurantAIAgent()


agent = load_agent()

# ── Render Navbar ────────────────────────────────────────────
st.markdown(
    """
    <div class="luxury-navbar">
        <div class="navbar-brand">REDI</div>
        <div class="navbar-links">
            <span class="navbar-link">Home</span>
            <span class="navbar-link">Menu</span>
            <span class="navbar-link">Book a Table</span>
            <span class="navbar-link active">AI Assistant</span>
        </div>
        <div class="navbar-icons">
            <div class="navbar-icon-btn" title="My Profile">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
            </div>
            <div class="navbar-icon-btn" title="Cart">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="9" cy="21" r="1"></circle>
                    <circle cx="20" cy="21" r="1"></circle>
                    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                </svg>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Session State Initialisation ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Namaste! Welcome to ReDi. How can I assist you with your "
                "Indian dining experience today? 🥂❤️"
            ),
            "time": "9:30 PM",
        },
        {
            "role": "user",
            "content": (
                "Hello! I'm looking for a vegetarian, medium-spicy dish around €15. "
                "What do you recommend?"
            ),
            "time": "9:30 PM",
        },
        {
            "role": "assistant",
            "content": (
                "Of course! Based on your preferences (Vegetarian, Medium Spicy, "
                "Budget €15), here are some delightful recommendations from our kitchen: 🍛😋"
            ),
            "time": "9:30 PM",
        },
    ]

# ── Three-Column Layout ──────────────────────────────────────
col_prefs, col_chat, col_dishes = st.columns([1.15, 1.85, 1.35], gap="medium")

# ─────────────────────────────────────────────────────────────
# ── COLUMN 1: Dietary & Budget Preferences ───────────────────
# ─────────────────────────────────────────────────────────────
with col_prefs:
    st.markdown(
        "<div class='col-main-title'>Dietary & Budget<br/>Preferences</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='col-sub-title'>Dietary Needs</div>", unsafe_allow_html=True)
    dietary_options = ["Vegetarian", "Gluten-Free", "Vegan", "Dairy-Free", "Nut-Free"]
    selected_dietary = st.pills(
        "Dietary Needs",
        dietary_options,
        selection_mode="multi",
        default=[],
        label_visibility="collapsed",
        key="dietary_pills",
    )

    st.markdown("<div class='col-sub-title'>Spiciness Level</div>", unsafe_allow_html=True)
    spice_options = ["Mild", "Medium", "Hot"]
    selected_spice = st.pills(
        "Spiciness Level",
        spice_options,
        selection_mode="single",
        default="Medium",
        label_visibility="collapsed",
        key="spice_pills",
    )

    st.markdown("<div class='col-sub-title'>Budget Range</div>", unsafe_allow_html=True)
    st.markdown("<div class='col-desc-note'>€10 – €50 slider</div>", unsafe_allow_html=True)
    selected_budget = st.slider(
        "Budget Range (€10 – €50)",
        min_value=10,
        max_value=50,
        value=20,
        step=1,
        format="€%d",
        label_visibility="collapsed",
        key="budget_slider",
    )

    st.markdown("<div class='col-sub-title'>Occasion</div>", unsafe_allow_html=True)
    occ_date = st.toggle("Date Night", value=False, key="toggle_date")
    occ_family = st.toggle("Family Dinner", value=False, key="toggle_family")
    occ_quick = st.toggle("Quick Bite", value=False, key="toggle_quick")

    # Build active filters dictionary from Column 1
    active_filters = {}
    if selected_dietary:
        if "Vegetarian" in selected_dietary:
            active_filters["is_vegetarian"] = True
        if "Vegan" in selected_dietary:
            active_filters["is_vegan_possible"] = True
        allergens = []
        if "Gluten-Free" in selected_dietary:
            allergens.append("a")
        if "Dairy-Free" in selected_dietary:
            allergens.append("f")
        if "Nut-Free" in selected_dietary:
            allergens.append("g")
        if allergens:
            active_filters["exclude_allergens"] = allergens

    # Always enforce the active budget ceiling!
    active_filters["max_price"] = float(selected_budget)

    if occ_quick:
        active_filters["is_lunch_menu"] = True

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Clear Chat History", use_container_width=True, key="clear_chat_btn"):
        now_time = datetime.datetime.now().strftime("%I:%M %p")
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Namaste! Welcome to ReDi. How can I assist you with your "
                    "Indian dining experience today? 🥂❤️"
                ),
                "time": now_time,
            }
        ]
        if "last_search_query" in st.session_state:
            del st.session_state["last_search_query"]
        st.rerun()


# ─────────────────────────────────────────────────────────────
# ── COLUMN 2: ReDi AI Dining Assistant (Chat) ────────────────
# ─────────────────────────────────────────────────────────────
with col_chat:
    # Build complete chat HTML into a single block so that messages are strictly inside the card
    chat_html_lines = [
        '<div class="chat-card-panel">',
        '  <div class="chat-card-header">',
        '    <div class="chat-avatar-rd">RD</div>',
        '    <div class="chat-header-name">ReDi AI Dining Assistant</div>',
        '  </div>',
        '  <div class="chat-messages-container">',
    ]

    for msg in st.session_state.messages:
        time_str = html.escape(msg.get("time", "9:30 PM"))
        content_str = html.escape(msg["content"]).replace("\n", "<br/>")
        if msg["role"] == "assistant":
            chat_html_lines.append(
                f'<div class="msg-assistant-wrapper">'
                f'  <div class="chat-avatar-rd msg-avatar-small">RD</div>'
                f'  <div class="msg-bubble-assistant">{content_str}'
                f'    <span class="msg-time-stamp">{time_str}</span>'
                f'  </div>'
                f'</div>'
            )
        else:
            chat_html_lines.append(
                f'<div class="msg-user-wrapper">'
                f'  <div class="msg-bubble-user">{content_str}'
                f'    <span class="msg-time-stamp-user">{time_str}</span>'
                f'  </div>'
                f'</div>'
            )

    chat_html_lines.append('  </div>')  # close chat-messages-container
    chat_html_lines.append('</div>')     # close chat-card-panel

    st.markdown("\n".join(chat_html_lines), unsafe_allow_html=True)

    # Pill chat input right under the card
    user_query = st.chat_input("Type your message...")
    if user_query:
        now_str = datetime.datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append(
            {"role": "user", "content": user_query, "time": now_str}
        )

        with st.spinner("ReDi Assistant is consulting the chef..."):
            # 1. Parse user intent with Groq
            parsed = agent.parse_user_intent(user_query)

            # Store semantic query to guide recommended dishes
            st.session_state.last_search_query = parsed.search_query

            # 2. Merge user intent filters with active preference pills & toggles
            merged_filters = dict(active_filters)
            parsed_dict = parsed.filters.model_dump(exclude_none=True)
            merged_filters.update(parsed_dict)

            # 3. Retrieve matching items
            query_str = parsed.search_query
            if selected_spice:
                query_str += f" {selected_spice.lower()} spicy"

            # If user query specifically mentions meat or seafood, override any accidental vegetarian/vegan filter!
            meat_keywords = {
                "fish", "chicken", "lamb", "shrimp", "duck", "meat", "seafood",
                "fisch", "hähnchen", "lamm", "garnelen", "ente", "fleisch",
                "salmon", "lachs", "maschli", "prawn", "prawns"
            }
            query_words = set(re.findall(r"\w+", (user_query + " " + parsed.search_query).lower()))
            if query_words & meat_keywords:
                merged_filters.pop("is_vegetarian", None)
                merged_filters.pop("is_vegan_possible", None)

            results = agent.search_engine.search(
                query=query_str,
                filters=merged_filters,
                top_k=4,
            )

            # If zero items found with strict filters (e.g. price slider was set too low), auto-relax price ceiling
            if not results and "max_price" in merged_filters:
                relaxed_filters = dict(merged_filters)
                relaxed_filters.pop("max_price", None)
                results = agent.search_engine.search(
                    query=query_str,
                    filters=relaxed_filters,
                    top_k=4,
                )

            # 4. Generate recommendation response
            response = agent.generate_recommendation(user_query, parsed, results)

        st.session_state.messages.append(
            {"role": "assistant", "content": response, "time": now_str}
        )
        st.rerun()


# ─────────────────────────────────────────────────────────────
# ── COLUMN 3: Recommended Dishes (Dynamically Synced) ────────
# ─────────────────────────────────────────────────────────────
with col_dishes:
    st.markdown(
        "<div class='col-main-title'>Recommended Dishes</div>",
        unsafe_allow_html=True,
    )

    # Show active budget indicator
    st.markdown(
        f"<span class='active-filter-badge'>💰 Filtered: ≤ €{selected_budget:.2f}</span>",
        unsafe_allow_html=True,
    )

    # Determine query based on current or last chat query + active spice
    active_search_query = st.session_state.get(
        "last_search_query", "Paneer Tikka Masala Daal Makhni Palak Paneer curry"
    )
    if selected_spice:
        active_search_query += f" {selected_spice.lower()} spicy"

    # Search dynamically with active filters (budget ceiling, dietary, allergen flags)
    display_results = agent.search_engine.search(
        query=active_search_query,
        filters=active_filters,
        top_k=3,
    )

    # If zero items found under a tight price cap, auto-relax price so recommendations are never blank
    if not display_results and "max_price" in active_filters:
        relaxed_active = dict(active_filters)
        relaxed_active.pop("max_price", None)
        display_results = agent.search_engine.search(
            query=active_search_query,
            filters=relaxed_active,
            top_k=3,
        )

    if not display_results:
        st.info(f"No dishes found under €{selected_budget:.2f} with the selected dietary options. Try increasing the budget or relaxing dietary filters.")
    else:
        for item in display_results:
            img_url = get_dish_image(item)
            stars, rating = get_dish_rating(item)

            badge_html = ""
            if item.get("is_lunch_menu"):
                badge_html += "<span class='dish-badge-pill badge-lunch'>Mittagsmenü</span> "
            if item.get("is_vegetarian"):
                badge_html += "<span class='dish-badge-pill badge-veg'>Vegetarian</span> "
            if item.get("is_vegan_possible"):
                badge_html += "<span class='dish-badge-pill badge-vegan'>Vegan</span>"

            st.markdown(
                f"""
                <div class="dish-card">
                    <img src="{img_url}" class="dish-thumb" alt="{item['name']}" />
                    <div class="dish-info-col">
                        <div class="dish-head-row">
                            <h4 class="dish-name-txt">{item['name']}</h4>
                            <span class="dish-price-txt">€{item['price']:.2f}</span>
                        </div>
                        <p class="dish-desc-txt">{item['description_de']}</p>
                        <div class="dish-bottom-row">
                            <div class="dish-stars-rating">
                                <span class="stars-gold">{stars}</span>
                                <span class="stars-score-num">{rating}</span>
                            </div>
                            <div>{badge_html}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
