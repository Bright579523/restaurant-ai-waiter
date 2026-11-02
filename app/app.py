"""
app.py — Streamlit UI for the ReDi Restaurant AI Waiter
========================================================
Luxury 3-column dining assistant interface matching the ReDi brand design:
  • Column 1: Dietary and Budget Preferences (Pills, Slider, Occasion toggles)
  • Column 2: ReDi AI Dining Assistant (Chat stream with RD avatar, pill input)
  • Column 3: Recommended Dishes (Photo cards, title, price, description, star ratings)
"""

import datetime
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
    # Match mockup exact values for signature dishes
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

        /* Hide sidebar for full 3-column experience */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* App background and typography */
        .stApp {
            background-color: #F8F5EE !important;
            color: #2A1D1A !important;
            font-family: 'Outfit', sans-serif !important;
        }

        .main .block-container {
            padding-top: 0rem !important;
            padding-bottom: 2rem !important;
            padding-left: 2.5rem !important;
            padding-right: 2.5rem !important;
            max-width: 1440px !important;
        }

        /* ── Top Navigation Bar ── */
        .luxury-navbar {
            background-color: #4A0E17;
            padding: 16px 36px;
            margin: -0rem -2.5rem 24px -2.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 14px rgba(74, 14, 23, 0.15);
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

        /* ── Section Titles ── */
        .col-main-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: #221411;
            margin-bottom: 18px;
            letter-spacing: -0.2px;
        }

        .col-sub-title {
            font-size: 1rem;
            font-weight: 600;
            color: #221411;
            margin-top: 14px;
            margin-bottom: 8px;
        }

        .col-desc-note {
            font-size: 0.82rem;
            color: #7A695E;
            margin-bottom: 6px;
        }

        /* ── St Pills Styling ── */
        div[data-testid="stPills"] {
            gap: 8px !important;
        }
        div[data-testid="stPills"] button {
            border-radius: 9999px !important;
            border: 1px solid #D9CEBF !important;
            background-color: #FDFBF8 !important;
            color: #3A2D28 !important;
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            padding: 4px 14px !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stPills"] button:hover {
            border-color: #4A0E17 !important;
            color: #4A0E17 !important;
        }
        div[data-testid="stPills"] button[aria-checked="true"],
        div[data-testid="stPills"] button[data-selected="true"] {
            background-color: #4A0E17 !important;
            color: #FFFFFF !important;
            border-color: #4A0E17 !important;
            font-weight: 600 !important;
        }

        /* ── St Slider ── */
        div[data-testid="stSlider"] div[data-baseweb="slider"] {
            color: #4A0E17 !important;
        }
        div[data-testid="stSlider"] [role="slider"] {
            background-color: #4A0E17 !important;
            border: 2px solid #FFFFFF !important;
            box-shadow: 0 1px 4px rgba(74, 14, 23, 0.3) !important;
        }
        div[data-testid="stSlider"] [data-testid="stSliderTrack"] > div > div {
            background-color: #4A0E17 !important;
        }

        /* ── St Toggle ── */
        div[data-testid="stToggle"] label > div > div[data-checked="true"],
        div[data-testid="stToggle"] input:checked ~ div {
            background-color: #4A0E17 !important;
        }
        div[data-testid="stToggle"] p {
            font-size: 0.95rem !important;
            color: #2A1D1A !important;
            font-weight: 500 !important;
        }

        /* ── Center Chat Panel ── */
        .chat-card-panel {
            background: #FFFFFF;
            border-radius: 18px;
            border: 1px solid #ECE3D7;
            padding: 20px 22px 14px 22px;
            box-shadow: 0 4px 18px rgba(42, 29, 26, 0.04);
            display: flex;
            flex-direction: column;
            min-height: 620px;
        }

        .chat-card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 14px;
            border-bottom: 1px solid #F2ECE3;
            margin-bottom: 18px;
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
        }

        .chat-header-name {
            font-size: 1.12rem;
            font-weight: 700;
            color: #221411;
            font-family: 'Outfit', sans-serif;
        }

        /* Messages */
        .msg-assistant-wrapper {
            display: flex;
            gap: 10px;
            margin-bottom: 16px;
            align-items: flex-start;
        }

        .msg-bubble-assistant {
            background-color: #FFFFFF;
            border: 1px solid #EBE2D7;
            border-radius: 14px;
            padding: 12px 16px;
            color: #2A1D1A;
            font-size: 0.92rem;
            line-height: 1.5;
            max-width: 86%;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
        }

        .msg-time-stamp {
            font-size: 0.72rem;
            color: #8C7E74;
            margin-top: 5px;
            display: block;
        }

        .msg-user-wrapper {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 16px;
        }

        .msg-bubble-user {
            background-color: #EADDC6;
            border-radius: 14px;
            padding: 12px 16px;
            color: #2A1D1A;
            font-size: 0.92rem;
            line-height: 1.5;
            max-width: 82%;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
        }

        /* ── St Chat Input Pill ── */
        div[data-testid="stChatInput"] {
            border-radius: 9999px !important;
            border: 1px solid #D9CEBF !important;
            background-color: #FFFFFF !important;
            box-shadow: 0 2px 8px rgba(74, 14, 23, 0.04) !important;
            padding: 2px 8px !important;
            margin-top: 10px !important;
        }

        div[data-testid="stChatInput"]:focus-within {
            border-color: #4A0E17 !important;
            box-shadow: 0 0 0 2px rgba(74, 14, 23, 0.12) !important;
        }

        div[data-testid="stChatInput"] textarea {
            color: #2A1D1A !important;
            font-size: 0.92rem !important;
        }

        div[data-testid="stChatInput"] button {
            background-color: #4A0E17 !important;
            color: #FFFFFF !important;
            border-radius: 50% !important;
            width: 32px !important;
            height: 32px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: none !important;
        }

        div[data-testid="stChatInput"] button svg {
            fill: #FFFFFF !important;
        }

        /* ── Right Column: Dish Cards ── */
        .dish-card {
            background: #FFFFFF;
            border: 1px solid #EAE2D8;
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 14px;
            display: flex;
            gap: 14px;
            box-shadow: 0 2px 8px rgba(42, 29, 26, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .dish-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(74, 14, 23, 0.08);
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
            font-size: 1.02rem;
            font-weight: 700;
            color: #221411;
            margin: 0;
        }

        .dish-price-txt {
            font-size: 1.02rem;
            font-weight: 700;
            color: #221411;
            margin: 0;
        }

        .dish-desc-txt {
            font-size: 0.82rem;
            color: #685A50;
            line-height: 1.35;
            margin: 2px 0 6px 0;
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
            gap: 6px;
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

        /* Action buttons in col 1 */
        .btn-clean button {
            background-color: #FAF7F2 !important;
            color: #5A4B40 !important;
            border: 1px solid #D9CEBF !important;
            border-radius: 8px !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }
        .btn-clean button:hover {
            border-color: #4A0E17 !important;
            color: #4A0E17 !important;
            background-color: #F4EFEA !important;
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
col_prefs, col_chat, col_dishes = st.columns([1.1, 1.8, 1.4], gap="medium")

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
        default=["Vegetarian"],
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

    if selected_budget < 50:
        active_filters["max_price"] = float(selected_budget)

    if occ_quick:
        active_filters["is_lunch_menu"] = True

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🔄 Clear Chat", use_container_width=True, key="clear_chat_btn"):
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
            st.session_state.current_results = []
            st.rerun()

    with col_b2:
        pdf_path = PROJECT_ROOT / "raw_data" / "Menu of ReDi Restaurant.pdf"
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📄 Menu PDF",
                data=pdf_bytes,
                file_name="ReDi_Restaurant_Menu.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


# ─────────────────────────────────────────────────────────────
# ── COLUMN 2: ReDi AI Dining Assistant (Chat) ────────────────
# ─────────────────────────────────────────────────────────────
with col_chat:
    st.markdown(
        """
        <div class="chat-card-panel">
            <div class="chat-card-header">
                <div class="chat-avatar-rd">RD</div>
                <div class="chat-header-name">ReDi AI Dining Assistant</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Render conversational chat messages
    for msg in st.session_state.messages:
        time_str = msg.get("time", "9:30 PM")
        if msg["role"] == "assistant":
            st.markdown(
                f"""
                <div class="msg-assistant-wrapper">
                    <div class="chat-avatar-rd" style="width: 32px; height: 32px; font-size: 0.8rem;">RD</div>
                    <div class="msg-bubble-assistant">
                        {msg["content"]}
                        <span class="msg-time-stamp">{time_str}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="msg-user-wrapper">
                    <div class="msg-bubble-user">
                        {msg["content"]}
                        <span class="msg-time-stamp" style="color: #6D5F54; text-align: right;">{time_str}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Pill chat input
    user_query = st.chat_input("Type your message...")
    if user_query:
        now_str = datetime.datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append(
            {"role": "user", "content": user_query, "time": now_str}
        )

        with st.spinner("ReDi Assistant is consulting the chef..."):
            # 1. Parse user intent with Groq
            parsed = agent.parse_user_intent(user_query)

            # 2. Merge user intent filters with active preference pills & toggles
            merged_filters = dict(active_filters)
            parsed_dict = parsed.filters.model_dump(exclude_none=True)
            merged_filters.update(parsed_dict)

            # 3. Retrieve matching items
            query_str = parsed.search_query
            if selected_spice:
                query_str += f" {selected_spice.lower()} spicy"

            results = agent.search_engine.search(
                query=query_str,
                filters=merged_filters,
                top_k=4,
            )
            st.session_state.current_results = results

            # 4. Generate recommendation response
            response = agent.generate_recommendation(user_query, parsed, results)

        st.session_state.messages.append(
            {"role": "assistant", "content": response, "time": now_str}
        )
        st.rerun()


# ─────────────────────────────────────────────────────────────
# ── COLUMN 3: Recommended Dishes ─────────────────────────────
# ─────────────────────────────────────────────────────────────
with col_dishes:
    st.markdown(
        "<div class='col-main-title'>Recommended Dishes</div>",
        unsafe_allow_html=True,
    )

    # If no search results yet, fetch signature recommendations matching mockup
    display_results = st.session_state.get("current_results")
    if not display_results:
        # Signature dishes matching design mockup: 58 (Paneer Tikka Masala), 45 (Daal Makhni), 55 (Palak Paneer)
        signature_ids = [58, 45, 55]
        sig_items = []
        for sid in signature_ids:
            row = agent.search_engine.df[agent.search_engine.df["item_id"] == sid]
            if not row.empty:
                item_dict = row.iloc[0].to_dict()
                item_dict["similarity_score"] = 0.95
                sig_items.append(item_dict)
        display_results = sig_items
        st.session_state.current_results = display_results

    if not display_results:
        st.info("No dishes match the selected preferences. Try adjusting the filters.")
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
