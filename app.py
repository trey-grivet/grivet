import os
import json
import requests
import pandas as pd
import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

from scoring import (
    score_introduction, score_impression, score_discovery, score_solution,
    score_upselling, score_fullsolution, score_objections, score_closing,
    score_email, score_exit
)

# ---- Upbeat, transcript-aware coaching notes ----
PILLARS = ["Introduction","Impression","Discovery","Solution","Upselling","FullSolution",
           "Objections","Closing","Email","Exit"]

_POSITIVE = {
    "Introduction": "a warm, confident opener",
    "Impression":   "friendly, professional tone",
    "Discovery":    "solid discovery questions",
    "Solution":     "clear value explanation",
    "Upselling":    "smart add-on suggestions",
    "FullSolution": "connecting items into a complete solution",
    "Objections":   "calm, benefit-led objection handling",
    "Closing":      "a confident, natural close",
    "Email":        "a natural email ask",
    "Exit":         "a memorable send-off",
}

_COACH = {
    "Introduction": "introduce yourself by name and ask for theirs, then use it once or twice",
    "Impression":   "keep energy upbeat and mirror their pace",
    "Discovery":    "ask 2–3 open-ended questions about goals, frequency, and past issues",
    "Solution":     "tie features to felt benefits like comfort, durability, and injury prevention",
    "Upselling":    "bundle a simple add-on (quality socks, custom insoles, care kit)",
    "FullSolution": "present a complete solution, not just the hero item",
    "Objections":   "answer concerns with benefits and the 30-day guarantee",
    "Closing":      "close clearly and invite them back by name",
    "Email":        "collect email naturally (receipt, saving a FootBalance scan, or event invites)",
    "Exit":         "end with a warm, memorable send-off",
}

def _extract_flags(transcript: str, customer_name: str | None = None) -> dict:
    t = (transcript or "").lower()
    return {
        "pain": any(k in t for k in ["knee", "ankle", "heel", "arch", "plantar", "shin", "blister", "back pain", "shin splints"]),
        "insole": any(k in t for k in ["insole", "insoles", "superfeet", "footbalance", "orthotic"]),
        "socks": any(k in t for k in ["sock", "socks", "merino", "bamboo"]),
        "nutrition": any(k in t for k in ["gel", "gels", "gu", "lmnt", "electrolyte", "honey stinger", "waffle"]),
        "hydration": any(k in t for k in ["hydration", "bottle", "flask", "hydro flask", "yeti", "pack"]),
        "headlamp": ("headlamp" in t) or ("head lamp" in t),
        "email": ("email" in t) or ("e-receipt" in t) or ("receipt" in t),
        "guarantee": ("30 day" in t) or ("30-day" in t) or ("guarantee" in t) or ("return" in t),
        "name_use": bool(customer_name and customer_name.lower() in t),
        "price_only": "price" in t and not (("value" in t) or ("benefit" in t) or ("guarantee" in t)),
    }

def _persona_tip(persona: str) -> str:
    p = (persona or "").lower()
    if "triathlete" in p:
        return "Tie footwear to cross-discipline needs and add fueling/hydration."
    if "walker" in p or "comfortable dad" in p:
        return "Lean into comfort, stability, and insoles for pain relief."
    if "yoga" in p:
        return "Highlight Vuori/Lululemon fits; suggest mats or recovery."
    if "trendy" in p:
        return "Connect On/Vuori/Lululemon style with function; build a lifestyle bundle."
    if "explorer" in p or "outdoor" in p:
        return "Bundle shoes with a light pack or headlamp."
    if "casual runner" in p or "weekend" in p:
        return "Focus on injury-prevention wins (socks, recovery, electrolytes)."
    return "Keep it personal and value-driven."

def _top_strength_phrases(parsed: dict, k: int = 2) -> list[str]:
    strong = [p for p in PILLARS if parsed.get(p, 0) >= 8]
    strong.sort(key=lambda p: parsed.get(p, 0), reverse=True)
    return [_POSITIVE[p] for p in strong[:k]]

def _top_focus_phrases(parsed: dict, k: int = 2) -> list[str]:
    lows = [p for p in PILLARS if parsed.get(p, 0) <= 6]
    lows.sort(key=lambda p: parsed.get(p, 0))  # lowest first
    return [_COACH[p] for p in lows[:k]]

def build_notes_from_scores(parsed: dict, transcript: str, persona: str, customer_name: str | None = None) -> str:
    flags = _extract_flags(transcript, customer_name)

    # 1) Positives (up to 2)
    pos = _top_strength_phrases(parsed, k=2)
    if pos:
        s1 = f"Great job on {pos[0]}." if len(pos) == 1 else f"Great job on {pos[0]} and {pos[1]}."
    else:
        s1 = "Nice start engaging the customer."

    # 2) Coaching focuses (up to 2)
    focus = _top_focus_phrases(parsed, k=2)
    if focus:
        s2 = f"Next time, {focus[0]}." if len(focus) == 1 else f"Next time, {focus[0]} and {focus[1]}."
    else:
        s2 = ""

    # 3) Context nudges from transcript (choose up to 2)
    nudges = []
    if flags["pain"] and not flags["insole"]:
        nudges.append("Offer a custom FootBalance insole fitting to address the pain.")
    if flags["insole"] and not flags["socks"]:
        nudges.append("Pair insoles with technical socks to prevent blisters.")
    if flags["nutrition"] and not flags["hydration"]:
        nudges.append("Round out fueling with electrolytes and a simple hydration plan.")
    if flags["headlamp"]:
        nudges.append("Nice seasonal add-on opportunity with a headlamp for safety.")
    if not flags["guarantee"] and parsed.get("Objections", 0) <= 6:
        nudges.append("Use the 30-day guarantee to reduce risk and reinforce value.")
    if customer_name and not flags["name_use"]:
        nudges.append(f"Use {customer_name}’s name once or twice to strengthen connection.")
    if flags["price_only"]:
        nudges.append("Shift from price to value—comfort, longevity, and injury-prevention.")

    s3 = ""
    if nudges:
        s3 = " ".join(nudges[:2]).strip()
        if not s3.endswith("."):
            s3 += "."

    # 4) Persona cue (short)
    tip = _persona_tip(persona)
    s4 = f"For a {persona}, {tip}"
    if not s4.endswith("."):
        s4 += "."

    # Assemble 2–4 sentences, upbeat and clean
    sentences = [s1, s2, s3, s4]
    notes = " ".join(s for s in sentences if s).strip()
    if notes and notes[-1] not in ".!?":
        notes += "."
    return notes
# =========================
# ENV / CONFIG (single source of truth)
# =========================
import os
import streamlit as st
from openai import OpenAI

def get_secret(name: str, default: str | None = None):
    # Prefer environment var; fallback to Streamlit secrets
    val = os.getenv(name)
    if val is None:
        val = st.secrets.get(name, default)
    return (val or "").strip()

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
APPSHEET_KEY   = get_secret("APPSHEET_KEY")

# Fail fast with friendly messages
if not OPENAI_API_KEY:
    st.error('Missing OPENAI_API_KEY. In Streamlit → Settings → Secrets add:\n\nOPENAI_API_KEY = "sk-..."')
    st.stop()
if not (OPENAI_API_KEY.startswith("sk-") and len(OPENAI_API_KEY) > 40):
    st.error('OPENAI_API_KEY looks invalid. Use exact TOML (quotes):\n\nOPENAI_API_KEY = "sk-..."')
    st.stop()
if not APPSHEET_KEY:
    st.error('Missing APPSHEET_KEY. In Streamlit → Settings → Secrets add:\n\nAPPSHEET_KEY = "..."')
    st.stop()

# Let SDK read the key from env
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# --- Diagnostics to logs only (place above client = OpenAI()) ---
import logging, sys
import openai, httpx

log = logging.getLogger("diag")
if not log.handlers:  # avoid duplicate handlers on Streamlit reruns
    h = logging.StreamHandler()
    f = logging.Formatter("%(levelname)s diag | %(message)s")
    h.setFormatter(f)
    log.addHandler(h)
log.setLevel(logging.INFO)

log.info("python=%s openai=%s httpx=%s",
         sys.version.split()[0],
         getattr(openai, "__version__", "unknown"),
         getattr(httpx, "__version__", "unknown"))
# --- end diagnostics ---

# --- Single OpenAI client init ---
client = OpenAI()
# --- end OpenAI init ---

APPSHEET_URL = (
    "https://api.appsheet.com/api/v2/apps/320743da-c218-4adb-90bd-e0be74a146b9/"
    "tables/Grivet%20Retail%20Sales%20Trainer%20Data/Action"
)
APPSHEET_HEADERS = {
    "ApplicationAccessKey": APPSHEET_KEY,
    "Content-Type": "application/json",
}
st.set_page_config(page_title="Grivet Retail Sales Trainer", page_icon="Grivet B W.jpg")

# Safe image rendering
from pathlib import Path
if Path("grivet_black.png").exists():
    st.image("grivet_black.png", width=100)

st.title("Grivet Retail Sales Trainer")
BUILD = "2025-09-30"
st.caption(f"Build: {BUILD}")

# =========================
# SESSION STATE
# =========================
import random
if "started" not in st.session_state:
    st.session_state.started = False
if "customer_name" not in st.session_state:
    st.session_state.customer_name = None
if "last_input" not in st.session_state:
    st.session_state.last_input = None

# =========================
# RANDOMIZE CUSTOMER PERSONA + BRAND
# =========================
if "chosen_persona" not in st.session_state:
    personas = [
        "Walker", "Yoga Mom", "Comfortable Dad", "Trendy Brand Shopper",
        "Explorer/Outdoor Enthusiast", "Triathlete",
        "Weekend Warrior", "Casual Browser", "Uninterested Customer"
    ]
    persona = random.choice(personas)

    brand = None
    coaching_goal = None

    if persona == "Walker":
        brand = random.choice(["Hoka", "Brooks", "On Running", "Altra"])
    elif persona == "Yoga Mom":
        brand = random.choices(
            ["Vuori", "Lululemon", "Free Fly", "Beyond Yoga", "Birkenstock"],
            weights=[0.35, 0.35, 0.15, 0.1, 0.05], k=1
        )[0]
    elif persona == "Comfortable Dad":
        brand = random.choice(["Hoka", "On Running", "Birkenstock", "Chaco"])
    elif persona == "Trendy Brand Shopper":
        brand = random.choice(["Vuori", "Lululemon", "On Running"])
    elif persona == "Explorer/Outdoor Enthusiast":
        brand = random.choice(["Patagonia", "The North Face", "On Running"])
    elif persona == "Triathlete":
        brand = random.choice(["Hoka", "Altra", "Brooks", "On Running"])
        coaching_goal = "Highlight cross-discipline needs, apparel, hydration, and nutrition."
    elif persona in ["Weekend Warrior", "Casual Browser", "Uninterested Customer"]:
        brand = random.choice([
            "Hoka", "Brooks", "On Running", "Altra",
            "Vuori", "Lululemon", "Free Fly", "Beyond Yoga",
            "Patagonia", "The North Face", "Birkenstock", "Chaco"
        ])

    st.session_state["chosen_persona"] = persona
    st.session_state["chosen_brand"] = brand
    st.session_state["coaching_goal"] = coaching_goal


if "messages" not in st.session_state:
    chosen_persona = st.session_state.get("chosen_persona", "Unknown Persona")
    chosen_brand = st.session_state.get("chosen_brand", "Unknown Brand")
    coaching_goal = st.session_state.get("coaching_goal", None)

    # Hidden context (GPT sees it, employee never does)
    hidden_context = (
        f"[INTERNAL CONTEXT — DO NOT REVEAL TO EMPLOYEE: "
        f"Persona = {chosen_persona}, Brand = {chosen_brand}."
        + (f" Coaching goal = {coaching_goal}]" if coaching_goal else "]")
    )

    final_locked_prompt = (
        "You are the **Grivet Retail Sales Trainer**, a role-play simulator for training "
        "Grivet Outdoors store employees. Grivet Outdoors is an active lifestyle retailer established in Memphis, TN "
        "specializing in run specific shoes and clothing. Our core focus is inspiring and empowering an active lifestyle through modern, "
        "personalized retail experiences. "
        "Employees are being trained to guide, educate, and connect with customers in a way that reflects Grivet’s brand values: "
        "authenticity, expertise, inclusivity, and personalized service. Our three uniques are full-service footwear, our brand assortment, and community involvement.\n\n"

        "=== Training Goals ===\n"
        "- Greet customers warmly and authentically\n"
        "- Introduce yourself by name, and learn the customer’s name\n"
        "- Use the customer’s name naturally throughout the conversation\n"
        "- Use conversation starters to break the ice\n"
        "- Ask discovery questions to uncover needs, drivers, and behaviors\n"
        "- Effectively explain product value benefits, and demonstrate good active listening to customer needs and concerns\n"
        "- Recommend products with confidence and tie them to customer stories\n"
        "- Address customer concerns, handle complaints, and offer solutions to customer problems\n"
        "- Explain how products solve problems like knee, joint, foot pain, blisters, etc instead of cost. Express the value of health benefits and injury prevention\n"
        "- Focus on attachment rates and drive add-on sales (socks, insoles, care kits, hydration, headlamps, nutrition)\n"
        "- Ask for email to connect customers to our community and events\n"
        "- Use 30 day guarantee on shoes to close. Attach custom insoles with personal 3-D scan.\n"
        "- Close with rapport: use the customer’s name, say goodbye warmly, invite them back\n\n"

        "=== Customer Personas (role-play as one per session) ===\n"
        "Core Running & Active Lifestyle Personas:\n"
        "- Intense Marathon Runner: performance-driven, Hoka/Brooks/On shoes, nutrition, hydration\n"
        "- Casual Runner: comfort and durability, beginner-friendly\n"
        "- Triathlete: cross-discipline needs, apparel, hydration, fueling\n"
        "- Walker: older or returning to fitness, comfort shoes, insoles\n"
        "- Yoga Mom: Vuori/Lululemon, style + function, mats, wellness\n"
        "- Mom / Dad shopping for son / daughter\n"
        "- Comfortable Dad: everyday comfort gear, sandals, casual shoes\n"
        "- Trendy Brand Shopper: premium lifestyle (Vuori, Lululemon, On, Patagonia)\n\n"
        "Other Personas:\n"
        "- Weekend Warrior: mixes running, hiking, fitness classes\n"
        "- Casual Browser: not intent-driven, needs authentic engagement\n"
        "- Uninterested Customer: killing time, minimal intent\n"
        "- Gear Enthusiast: loves product details, compares brands\n"
        "- Explorer/Outdoor Enthusiast: browsing for hiking/travel gear\n\n"

        "=== Brand Knowledge (core inventory) ===\n"
        "- Footwear: Hoka, Brooks, On Running, Birkenstock, Chaco\n"
        "- Apparel: Vuori, Lululemon, Free Fly, Patagonia, The North Face, Kuhl, LL Bean, Beyond Yoga\n"
        "- Accessories: Volunteer Traditions, Hydro Flask, YETI, Jason Markk shoe care\n"
        "- Nutrition: GU, LMNT, Honey Stinger\n"
        "- Attachment mapping: Shoes → socks/custom insoles; Jackets → hats/gloves; Cooler → tumblers/ice packs\n\n"

        "=== Product Knowledge Nuggets ===\n"
        "- Socks: 250k sweat glands/foot, half pint sweat/day, 3–6 month lifespan, bamboo/merino > cotton\n"
        "- Insoles: Superfeet (structure), FootBalance (custom molded) → comfort, pain relief\n"
        "- Shoe Care: Jason Markk plant-based, 100+ pairs per bottle\n"
        "- Hydration Packs: hands-free, balanced weight, useful beyond trail\n"
        "- Headlamps: safety, hands-free, all-season utility\n"
        "- Nutrition: GU gels (fast energy, sodium, BCAAs), LMNT electrolytes (1000mg sodium, no sugar), Honey Stinger waffles (organic carbs, steady energy)\n\n"

        "=== Customer Cues & Body Language ===\n"
        "- Watch and reflect realistic signals:\n"
        "  • Staring at a rack of clothes → interest but unsure\n"
        "  • Picking up then putting back → hesitation/price concern\n"
        "  • Trying on items → chance to suggest socks/insoles/apparel combos\n"
        "  • Checking phone/arms crossed → disengaged; re-engage lightly\n"
        "  • Moving toward the door → low intent; one warm, concise close\n\n"

        "=== Visual & Style Cues ===\n"
        "- Always notice what the customer is wearing and describe it briefly:\n"
        "  • Brand logos of competitors we don't sell (Nike, Adidas, Under Armour, Reebok) or premium luxury brands (Prada, Gucci, Fendi, Dior, Louis Vuitton, Hermès, Ralph Lauren, Rolex, Versace, Armani, Givenchy, Tom Ford) or brands we sell (Hoka, Brooks, On, Vuori, Lululemon, Patagonia, etc.)\n"
        "  • Colors and patterns (bright = energetic, muted = casual, neutral = minimalist)\n"
        "  • Accessories (hat, watch, bag, bottle) → lead to product attachments\n"
        "  • Writing on shirts (race tees, yoga studios, local events) → connect with lifestyle/community\n"
        "- Use these as selling cues:\n"
        "  • Race shirt → ask about running goals, suggest performance shoes/nutrition\n"
        "  • Yoga gear → suggest Vuori/Lululemon apparel or mats\n"
        "  • Outdoor brands → suggest The North Face Jacket, Patagonia Jacket, hiking packs, headlamps, trail shoes\n"
        "  • Neutral/dad casual → suggest comfort shoes and daily wear\n"
        "- Always include these observations in the **coaching overlay** so employees learn to use them.\n\n"

        "=== Sales Tactics to Reinforce ===\n"
        "- Connect recommendations to actual interest shown (what they look at or touch).\n"
        "- Upsell via companion items (not pushy): Shoes → socks/insoles/nutrition; Apparel → hats/gloves/outerwear; Cooler/YETI → tumblers/ice packs\n"
        "- Tie brand alignment: On shoes → Vuori/Lululemon apparel synergy, etc.\n"
        "- Adjust tone to behavior: hesitant → reassure; eager → bundle; disinterested → keep it brief and helpful.\n"
        "- Never push; always frame as personalized help and value.\n\n"

        "=== Email Collection Tactics ===\n"
        "- Weave email collection naturally:\n"
        "  • At checkout: 'What is a good email?' or 'Would you like me to email your receipt?'\n"
        "  • During FootBalance fitting: 'Do you have an email to save your scan?'\n"
        "  • Community: 'We’d love to invite you to group runs and yoga—can I get a good email for you?'\n"
        "- Tie email to value (ease, personalization, community).\n\n"

        "=== Speed & Flow ===\n"
        "- Keep it fast and engaging. Replies 2–4 sentences, realistic, natural. Avoid monologues.\n\n"

        "=== Customer Name Rule ===\n"
        "- Only encourage name use after the customer has shared it. Don’t invent names.\n\n"

        "=== Gamified Feedback Rules ===\n"
        "- ✅ Positive action: strong greeting/discovery/rapport/loyalty-building\n"
        "- 🎯 Strategic win: well-executed upsell/attachment/value-driven recommendation\n"
        "- 🔴 Caution: pushy tone, missed cues, weak close\n"
        "- 💬 Name Power: +1 introduce self; +1 learn name; +1 repeat naturally; +2 use name during close\n"
        "- Provide instant feedback inline after responses, without breaking character\n\n"

        "=== Scoring Framework ===\n"
        "- Final evaluation uses 10 equally weighted categories, each scored 0–10.\n"
        "- Categories: Introduction, Impression, Discovery, Solution, Upselling Accessories, Full Solution, Handling Objections, Closing, E-mail Collection, Memorable Exit.\n"
        "- At '/score': stop role-play. Do **not** output JSON; the app handles scoring and logging.\n"
        "- Inline gamified feedback (✅, 🔴, 💬, 🎯) is encouraged during the conversation; final scoring happens only at '/score'.\n\n"

        "=== Session Flow ===\n"
        "1. Wait until employee enters their name.\n"
        "2. Greet them: 'Welcome [Name]! The role play will begin now as you notice a customer entering the store who you approach.'\n"
        "3. Role-play begins with 'Customer Approach' and short non-verbal cues.\n"
        "4. Interactions continue with natural customer replies, feedback, and knowledge drops.\n"
        "5. Provide gamified inline feedback after employee responses.\n"
        "6. Stop immediately at '/score'.\n"
        "7. Provide concise feedback summary (no JSON).\n\n"

        "=== Dual Response Format ===\n"
        "For every employee message, ALWAYS respond in three parts:\n"
        "1) **Non-Verbal cues** (bold/italics, short), 2) **Customer Persona Response**, 3) *Coaching Overlay* (brief, 1–2 sentences).\n\n"

        "=== Important Notes ===\n"
        "- Always stay in character until '/score'.\n"
        "- Never invent file saves or payloads.\n"
        "- Never invent employee names—use what they gave you.\n"
        "- Keep it fast, fun, and challenging. Model Grivet’s ethos.\n"
    )

    st.session_state.messages = [
        {"role": "system", "content": hidden_context},
        {"role": "system", "content": final_locked_prompt},
    ]

# =========================
# SIDEBAR QUICK REF
# =========================
with st.sidebar:
    st.subheader("Quick Reference")
    st.markdown("**Main Brands**")
    st.write("Hoka • Brooks • On Running • Altra • Vuori • Lululemon • Patagonia • The North Face • Kuhl • LL Bean • Beyond Yoga • YETI • Hydro Flask • Birkenstock • Chaco")
    st.markdown("**Attachments**")
    st.write("Shoes → Socks, Custom Insoles • Jackets → Hats, Gloves • Coolers → Tumblers, Ice packs")
    st.markdown("**Nutrition**")
    st.write("GU • LMNT • Honey Stinger")
    st.caption("Tip: greet warmly, introduce yourself, learn & use the customer's name, attach, upsell, collect email, and invite them back.")

# =========================
# NAME / CHAT UI
# =========================
employee_name = st.text_input("Enter your name to begin training:")
user_input = None

if not employee_name:
    st.warning("The Sales Trainer is an interactive role-play program that teaches Grivet store teams to uncover customer needs, close confidently, drive add-on sales, and build customer loyalty.")
else:
    # First welcome on first name entry
    if not st.session_state.started:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Welcome {employee_name}! The role play will begin with you approaching a customer. I’ll act as a customer. Go ahead and greet me when you’re ready. Type /score to end the role play, receive your session score, feeback and view the Leaderboard."
        })
        st.session_state.started = True
        st.rerun()

    # 1) Get input FIRST (only chat_input in the whole file)
    user_input = st.chat_input("Say something...", key="main_chat_input")

    # Process each distinct input once per run
    if user_input and user_input != st.session_state.last_input:
        st.session_state.last_input = user_input
        st.session_state.messages.append({"role": "user", "content": user_input})

        if "/score" in user_input.lower():
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Thanks for completing the training! Your session score is being calculated and will be displayed below in the summary. Check out where you rank on the Leaderboard!"
            })
        else:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )
                reply = response.choices[0].message.content
            except Exception as e:
                st.error(f"Model error: {e}")
                reply = "([Temporary notice] I hit an error generating a response.)"

            st.session_state.messages.append({"role": "assistant", "content": reply})

            # Optional: detect customer name from assistant reply
            if st.session_state.get("customer_name") in (None, ""):
                m = re.search(r"\bmy name is\s+([A-Z][a-z]+)\b", reply, flags=re.IGNORECASE)
                if m:
                    st.session_state["customer_name"] = m.group(1).strip().capitalize()

    # 2) THEN render (skip system messages)
    for msg in (m for m in st.session_state.messages if m.get("role") != "system"):
        st.chat_message(msg["role"]).write(msg.get("content", ""))

# Only run scoring and leaderboard when /score is typed
if employee_name and user_input and "/score" in user_input.lower():
    # user-only transcript for scoring
    transcript_user = "\n".join([m["content"] for m in st.session_state.messages if m["role"] == "user"])
    # combined transcript (user + assistant) for better coaching notes
    transcript_all  = "\n".join([m["content"] for m in st.session_state.messages if m["role"] in ("user", "assistant")])
    customer_name = st.session_state.get("customer_name", None)

    # --- compute scores & persist summary ---
    parsed = {
        "Introduction": score_introduction(transcript_user, customer_name=customer_name),
        "Impression":   score_impression(transcript_user),
        "Discovery":    score_discovery(transcript_user),
        "Solution":     score_solution(transcript_user),
        "Upselling":    score_upselling(transcript_user),
        "FullSolution": score_fullsolution(transcript_user),
        "Objections":   score_objections(transcript_user),
        "Closing":      score_closing(transcript_user, customer_name=customer_name),
        "Email":        score_email(transcript_user),
        "Exit":         score_exit(transcript_user, customer_name=customer_name),
    }

    persona_used = st.session_state.get("chosen_persona", "Unknown")
    parsed["Persona"] = persona_used
    parsed["Notes"] = build_notes_from_scores(
        parsed, transcript_all, persona_used, customer_name=customer_name
    )

    pillars = ["Introduction","Impression","Discovery","Solution","Upselling",
               "FullSolution","Objections","Closing","Email","Exit"]
    final_score = min(100, sum(int(parsed.get(p, 0)) for p in pillars))

    now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    st.session_state["last_summary"] = {
        "pillars": pillars,
        "parsed": parsed,
        "final_score": final_score,
        "timestamp": now,
    }

    # Send to AppSheet
    payload = {
        "Action": "Add",
        "Properties": {
            "Locale": "en-US",
            "Timezone": "Central Standard Time",
            "RunAsUserEmail": "test@grivetoutdoors.com"
        },
        "Rows": [{
            "Timestamp": now,
            "Employee Name": employee_name,
            "Persona": parsed.get("Persona", "Unknown"),
            "Session Score": final_score,
            **{pillar: parsed.get(pillar, 0) for pillar in pillars},
            "Notes": parsed.get("Notes", "")
        }]
    }
    try:
        r = requests.post(APPSHEET_URL, headers=APPSHEET_HEADERS, json=payload, timeout=20)
        if r.status_code == 200:
            st.success("✅ Score submitted to AppSheet!")
        else:
            st.error(f"❌ Error sending to AppSheet: {r.status_code} — {r.text}")
    except Exception as e:
        st.error(f"❌ Network error sending to AppSheet: {e}")


# === RESULTS / SUMMARY (persists across reruns) ===
summary = st.session_state.get("last_summary")
if summary:
    st.subheader("🏁 Session Summary")

    pillars = summary["pillars"]
    parsed = summary["parsed"]
    final_score = summary["final_score"]

    # Show all 10 pillars in two rows
    cols = st.columns(5)
    for i, pillar in enumerate(pillars[:5]):
        with cols[i]:
            st.metric(pillar, parsed.get(pillar, 0))

    cols = st.columns(5)
    for i, pillar in enumerate(pillars[5:]):
        with cols[i]:
            st.metric(pillar, parsed.get(pillar, 0))

    # Total score, persona, and notes
    st.metric("⭐ Total Score", f"{final_score} / 100")
    st.markdown(f"**🧑‍🤝‍🧑 Persona:** {parsed.get('Persona', 'Unknown')}")
    st.markdown(f"**📝 Notes:** {parsed.get('Notes', '')}")
    st.info("🏁 Great work! You can refresh to start a new session.")

    # Leaderboard toggle
    if st.button("📊 View Leaderboard", key="leaderboard_btn"):
        st.session_state["show_leaderboard"] = True

    if st.session_state.get("show_leaderboard"):
        APP_ID = "GrivetRetailSalesTrainerData-242284010"
        TABLE_NAME = "Grivet Retail Sales Trainer Data"
        api_key = APPSHEET_KEY
        url = f"https://api.appsheet.com/api/v2/apps/{APP_ID}/tables/{TABLE_NAME}/Action"

        @st.cache_data(ttl=300)
        def fetch_leaderboard():
            payload = {"Action": "Find", "Properties": {}, "Rows": []}
            headers = {"ApplicationAccessKey": api_key, "Content-Type": "application/json"}
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            return r.json() if r.status_code == 200 else []

        data = fetch_leaderboard()
        if data:
            df = pd.DataFrame(data)

            # Clean types
            df["Session Score"] = pd.to_numeric(df["Session Score"], errors="coerce")
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            df["Employee Name"] = df["Employee Name"].astype(str).str.strip()

            # Drop empties and sort
            df = df.dropna(subset=["Employee Name", "Session Score"])
            df_sorted = df.sort_values("Session Score", ascending=False).reset_index(drop=True)

            # Top 20 Leaderboard
            leaderboard = df_sorted.head(20).copy()
            ranks = []
            for i in range(len(leaderboard)):
                if i == 0: ranks.append("🥇 1")
                elif i == 1: ranks.append("🥈 2")
                elif i == 2: ranks.append("🥉 3")
                else: ranks.append(str(i + 1))
            leaderboard.insert(0, "Rank", ranks)

            st.subheader("🏆 Top Performers Leaderboard")
            st.dataframe(leaderboard[["Rank", "Employee Name", "Persona", "Session Score"]], use_container_width=True)

            # Current Employee's best rank
            if isinstance(employee_name, str) and employee_name.lower() in df_sorted["Employee Name"].str.lower().values:
                st.subheader("📌 Your Rank")
                your_row = df_sorted[df_sorted["Employee Name"].str.lower() == employee_name.lower()].copy()
                your_row = your_row.sort_values(["Session Score", "Timestamp"], ascending=[False, False]).head(1).copy()
                your_row_rank = your_row.index[0] + 1
                your_row.insert(0, "Rank", [str(your_row_rank)])  # one row => list of len 1
                st.dataframe(your_row[["Rank", "Employee Name", "Persona", "Session Score"]], use_container_width=True)
            else:
                st.info("Your score has not been logged yet.")
        else:
            st.info("No leaderboard data yet.")


    
    
