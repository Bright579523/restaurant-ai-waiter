"""
agent.py — Swagat AI Waiter (RAG Agent)
=========================================
Ties together LLM-based intent parsing, hybrid vector search, and
natural-language response generation into a single conversational agent.

Pipeline per user turn:
  1. **parse_user_intent** — Groq / Llama-3.3-70B extracts a semantic
     query string + structured metadata filters from free-text input.
  2. **search** — MenuSearchEngine retrieves the top-k matches.
  3. **generate_recommendation** — The LLM writes a friendly waiter
     response grounded in the retrieved items (RAG).

A rule-based mock parser is provided as a fallback when no API key
is configured, so the demo still functions offline.

Usage:
    from agent import SwagatAIAgent
    agent = SwagatAIAgent()
    reply = agent.chat("I want a vegetarian dish with spinach")
"""

import json
import os
import re
from typing import Optional

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

# Add search_engine folder to sys.path
sys_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
if sys_dir not in sys.path:
    sys.path.append(sys_dir)
sys.path.append(os.path.join(sys_dir, "search_engine"))

from search_engine import MenuSearchEngine

# Load .env once at import time
load_dotenv()

DEFAULT_GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")


# ── Pydantic schemas for structured intent output ────────────
class SearchFilters(BaseModel):
    """Metadata constraints extracted from the user's natural-language query."""

    is_vegetarian: Optional[bool] = Field(
        None,
        description="True if user explicitly wants vegetarian food, False for meat, None if unspecified.",
    )
    is_vegan_possible: Optional[bool] = Field(
        None, description="True if user wants vegan options."
    )
    is_lunch_menu: Optional[bool] = Field(
        None,
        description="True if user asks for the lunch menu (Mittagsmenü).",
    )
    meal_type: Optional[str] = Field(
        None,
        description="One of: 'main', 'starter', 'side', 'dessert', 'drink'.",
    )
    max_price: Optional[float] = Field(
        None, description="Maximum price in EUR the user is willing to pay."
    )
    exclude_allergens: Optional[list[str]] = Field(
        None,
        description=(
            "Single-letter allergen codes to exclude. "
            "a=gluten, b=crustaceans, c=egg, d=fish, e=soy, "
            "f=milk/lactose, g=nuts, i=mustard, j=sesame."
        ),
    )
    contains_ingredients: Optional[list[str]] = Field(
        None,
        description="Ingredients user wants: chicken, lamb, fish, shrimp, duck, paneer.",
    )
    exclude_ingredients: Optional[list[str]] = Field(
        None,
        description="Ingredients user wants to avoid (same keys as above).",
    )


class ParsedIntent(BaseModel):
    """Complete parsed representation of a single user request."""

    search_query: str = Field(
        ...,
        description="Cleaned semantic query for vector search (e.g. 'spicy chicken').",
    )
    filters: SearchFilters = Field(
        ..., description="Structured metadata filters."
    )


# ── Allergen mapping used in the LLM system prompt ──────────
ALLERGEN_MAPPING = (
    "- Gluten (wheat, flour, bread, naan) → 'a'\n"
    "- Crustaceans → 'b'\n"
    "- Egg → 'c'\n"
    "- Fish → 'd'\n"
    "- Soybeans → 'e'\n"
    "- Milk / Lactose (yogurt, cream, butter, cheese, ghee, lassi) → 'f'\n"
    "- Nuts (cashews, almonds, pistachios, peanuts) → 'g'\n"
    "- Mustard (Senf) → 'i'\n"
    "- Sesame → 'j'\n"
)


class ReDiRestaurantAIAgent:
    """Conversational RAG agent backed by Groq + MenuSearchEngine."""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key) if api_key else None

        if not self.client:
            print(
                "\n[Warning] GROQ_API_KEY is not set in .env - running in demo/mock mode.\n"
            )

        self.search_engine = MenuSearchEngine()

    # ── Full pipeline ────────────────────────────────────────
    def chat(self, user_message: str) -> str:
        """Run the complete RAG pipeline and return the waiter's reply."""
        msg_safe = user_message.encode('ascii', errors='replace').decode('ascii')
        print(f"\nUser: {msg_safe}")

        # Step 1 — Intent parsing
        parsed = self.parse_user_intent(user_message)
        q_safe = parsed.search_query.encode('ascii', errors='replace').decode('ascii')
        print(f"  -> Query : '{q_safe}'")
        print(f"  -> Filters: {parsed.filters.model_dump(exclude_none=True)}")

        # Step 2 — Retrieval
        results = self.search_engine.search(
            query=parsed.search_query,
            filters=parsed.filters.model_dump(exclude_none=True),
            top_k=3,
        )

        # Step 3 — Response generation
        response = self.generate_recommendation(user_message, parsed, results)
        resp_safe = response.encode('ascii', errors='replace').decode('ascii')
        print(f"AI Waiter:\n{resp_safe}")
        return response

    # ── Step 1: Intent parsing ───────────────────────────────
    def parse_user_intent(self, user_message: str) -> ParsedIntent:
        """Translate a free-text message into a ParsedIntent via the LLM."""
        if not self.client:
            return self._mock_parse(user_message)

        system_prompt = (
            "You are a parser for an Indian restaurant menu recommendation system.\n"
            "Extract a semantic search query and structured filters from the user message.\n\n"
            "CRITICAL INSTRUCTIONS FOR FILTERS:\n"
            "- ONLY extract and set filters (like contains_ingredients, is_vegetarian, meal_type, etc.) "
            "if the user EXPLICITLY requests them in their query (e.g., 'must contain paneer', 'no dairy', 'vegetarian please').\n"
            "- DO NOT guess, assume, or infer filters based on dishes mentioned in the query. "
            "For example, if the user asks 'what is Boondi Raita', DO NOT add 'paneer' to contains_ingredients, "
            "and DO NOT set meal_type or is_vegetarian unless they explicitly asked for it.\n"
            "- Leave filters as null/empty if they are not explicitly specified.\n\n"
            f"Allergen code mappings:\n{ALLERGEN_MAPPING}\n"
            "Allowed ingredient keys: chicken, lamb, fish, shrimp, duck, paneer.\n\n"
            "Respond with a JSON object matching this schema:\n"
            f"{json.dumps(ParsedIntent.model_json_schema(), indent=2)}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=DEFAULT_GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f'User request: "{user_message}"'},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            return ParsedIntent.model_validate_json(
                completion.choices[0].message.content
            )
        except Exception as exc:
            print(f"[Warning] Groq parsing error: {exc} - falling back to mock parser")
            return self._mock_parse(user_message)

    # ── Step 3: Response generation ──────────────────────────
    def generate_recommendation(
        self,
        user_message: str,
        parsed: ParsedIntent,
        results: list[dict],
    ) -> str:
        """Generate a friendly waiter response grounded in retrieved items."""
        if not self.client:
            return self._format_fallback(results)

        # Build the RAG context block
        context_lines = []
        for i, item in enumerate(results, 1):
            context_lines.append(
                f"{i}. #{item['item_id']} {item['name']} — {item['price']:.2f} €\n"
                f"   Category: {item['category']}\n"
                f"   Description: {item['description_de']}\n"
                f"   Allergens: {item['allergen_codes'] or 'none'}\n"
                f"   Vegetarian: {item['is_vegetarian']} | "
                f"Vegan possible: {item['is_vegan_possible']}"
            )

        prompt = (
            f"User Query: {user_message}\n\n"
            f"Extracted Intent:\n"
            f"  Search term: {parsed.search_query}\n"
            f"  Filters: {parsed.filters.model_dump_json(exclude_none=True)}\n\n"
            f"Retrieved Menu Items:\n"
            + ("\n\n".join(context_lines) if context_lines else "No items matched.")
        )

        system_prompt = (
            "You are a polite, welcoming AI Waiter at ReDi Restaurant.\n"
            "Recommend the retrieved dishes to the customer.\n"
            "Write in the same language the customer used (English, German, or Thai).\n"
            "Describe the dishes nicely using their descriptions.\n"
            "Explain why these dishes fit their dietary requirements.\n"
            "If no results matched, apologize and suggest alternative keywords."
        )

        try:
            completion = self.client.chat.completions.create(
                model=DEFAULT_GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return completion.choices[0].message.content
        except Exception as exc:
            return f"[Error] {exc}\n\n" + self._format_fallback(results)

    # ── Fallback helpers (no API key) ────────────────────────
    def _mock_parse(self, msg: str) -> ParsedIntent:
        """Rule-based heuristic parser for offline / demo mode."""
        low = msg.lower()
        filters = SearchFilters()
        query = msg

        # Dietary flags
        if any(kw in low for kw in ("veg", "เจ", "มังสวิรัติ")):
            filters.is_vegetarian = True
            query = re.sub(r"\b(vegetarian|veg)\b", "", query, flags=re.I).strip()

        if "vegan" in low:
            filters.is_vegan_possible = True

        if any(kw in low for kw in ("lunch", "mittag", "กลางวัน")):
            filters.is_lunch_menu = True

        # Ingredient detection
        for ingredient in ("chicken", "lamb", "fish", "shrimp", "duck", "paneer"):
            if ingredient in low:
                filters.contains_ingredients = filters.contains_ingredients or []
                filters.contains_ingredients.append(ingredient)

        # Price ceiling
        price_match = re.search(
            r"(?:under|below|less than|ไม่เกิน|ต่ำกว่า)\s*(\d+)", low
        )
        if price_match:
            filters.max_price = float(price_match.group(1))

        # Allergen exclusion
        if any(kw in low for kw in ("no milk", "no lactose", "แพ้นม")):
            filters.exclude_allergens = ["f"]

        return ParsedIntent(search_query=query, filters=filters)

    @staticmethod
    def _format_fallback(results: list[dict]) -> str:
        """Render structured results when the LLM is unavailable."""
        header = "📋 [Demo Mode] Here are matching recommendations:\n"
        if not results:
            return header + "  No matching items found for your criteria."

        lines = []
        for r in results:
            lines.append(
                f"\n• **{r['name']}** — {r['price']:.2f} €\n"
                f"  {r['description_de']}\n"
                f"  Category: {r['category']} | "
                f"Allergens: {r['allergen_codes'] or 'none'}"
            )
        return header + "\n".join(lines)


# ── Standalone test ──────────────────────────────────────────
if __name__ == "__main__":
    agent = ReDiRestaurantAIAgent()
    agent.chat("I want a vegetarian main dish under 15 euros with spinach")
