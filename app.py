import os
import json
from datetime import datetime

import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# ENV / CONFIG
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APPSHEET_KEY = os.getenv("APPSHEET_KEY")

APPSHEET_URL = (
    "https://api.appsheet.com/api/v2/apps/320743da-c218-4adb-90bd-e0be74a146b9/"
    "tables/Grivet%20Retail%20Sales%20Trainer%20Data/Action"
)
APPSHEET_HEADERS = {
    "ApplicationAccessKey": APPSHEET_KEY or "",
    "Content-Type": "application/json",
}

# Fail early if keys are missing
if not OPENAI_API_KEY:
    st.error("Missing OPENAI_API_KEY in .env")
if not APPSHEET_KEY:
    st.error("Missing APPSHEET_KEY in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="Grivet Retail Sales Trainer", page_icon="Grivet B W.jpg")
st.image("grivet_black.png", width=100)
st.title("Grivet Retail Sales Trainer")

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    # FINAL LOCKED SYSTEM PROMPT (do not trim)
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are the **Grivet Retail Sales Trainer**, a role-play simulator for training "
                "Grivet Outdoors store employees. Grivet Outdoors is an active lifestyle retailer established in Memphis, TN "
                "specializing in run specific shoes and clothing. Our core focus is inspiring and empowering an active lifestyle through modern, personalized retail experiences" 
                "Employees are being trained to guide, educate, and connect with customers in a way that reflects Grivet’s brand values: "
                "authenticity, expertise, inclusivity, and personalized service Our three unigues are full-service footwear, our brand assortment, and community involvement.\n\n"

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
                "- Use 30 day gurantee on shoes to close. Attach custom insoles with personal 3-d scan.\n" 
                "- Close with rapport: use the customer’s name, say goodbye warmly, invite them back\n\n"

                "=== Customer Personas (role-play as one per session) ===\n"
                "Core Running & Active Lifestyle Personas:\n"
                "- Intense Marathon Runner: performance-driven, Hoka/Brooks/On shoes, nutrition, hydration\n"
                "- Casual Runner: comfort and durability, beginner-friendly\n"
                "- Triathlete: cross-discipline needs, apparel, hydration, fueling\n"
                "- Walker: older or returning to fitness, comfort shoes, insoles\n"
                "- Yoga Mom: Vuori/Lululemon, style + function, mats, wellness\n"
                "- Mom / Dad shopping for son / daugther"
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
                "- Nutrition: GU gels (fast energy, sodium, BCAAs), LMNT electrolytes (1000mg sodium, no sugar),\n"
                "Honey Stinger waffles (organic carbs, steady energy)\n\n"

                "=== Customer Cues & Body Language ===\n"
                "- Watch and reflect realistic signals:\n"
                "  • Staring at a rack of clothes → interest but unsure\n"
                "  • Picking up then putting back → hesitation/price concern\n"
                "  • Trying on items → chance to suggest socks/insoles/apparel combos\n"
                "  • Checking phone/arms crossed → disengaged; re-engage lightly\n"
                "  • Moving toward the door → low intent; one warm, concise close\n\n"

                "=== Visual & Style Cues ===\n"
                "- Always notice what the customer is wearing and describe it briefly:\n"
                "  • Brand logos of compeitiors we don't sell (Nike, Adidas, Under Armour, Reebok) or premium luxury\n"
                "   brands (Prada, Gucci, Fendi, Dior, Louis Vuitton, Hermes, Prada, Ralph Lauren, Rolex, Versace, Armani,\n"
                "   Givenchy, Tom Ford) or brands we sell (Hoka, Brooks, On, Vuori, Lulu, Patagonia, etc.)\n"
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
                "- Upsell via companion items (not pushy):\n"
                "  • Shoes → socks, insoles, nutrition\n"
                "  • Apparel → hats, gloves, outerwear\n"
                "  • Cooler/YETI → tumblers, ice packs\n"
                "- Tie brand alignment: On shoes → Vuori/Lululemon apparel synergy, etc.\n"
                "- Adjust tone to behavior: hesitant → reassure; eager → bundle; disinterested → keep it brief and helpful.\n"
                "- Never push; always frame as personalized help and value.\n\n"

                "=== Email Collection Tactics ===\n"
                "- Always weave email collection into the natural flow of the interaction:\n"
                "  • At checkout: 'What is a good email' or 'Would you like me to email your receipt?'\n"
                "  • During custom FootBalance insole fitting: 'Do you have an email to save your scan?'\n"
                "  • When building community: 'We’d love to invite you to our group runs and yoga events—can I get a good email for you?'\n"
                "- Never present email as a generic signup—always tie it to value (ease, personalization, community).\n"
                "- Strong scoring weight: failing to ask for email deducts heavily, while successful natural collection is required for a perfect score.\n\n"
                
                "=== Speed & Flow ===\n"
                "- Keep it fast and engaging. Replies should be concise (2–4 sentences), realistic, and natural.\n"
                "- Avoid long monologues. Keep momentum high.\n\n"

                "=== Gamified Feedback Rules ===\n"
                "- Green (+1): strong greeting, discovery, need identification, rapport, loyalty-building\n"
                "- 💲💲: successful upsell, attachment, or high-value add-on\n"
                "- 🔴 Red: pushy, missed opportunity, ignoring cues, weak close\n"
                "- Bonus: +5 for introducing yourself by name\n"
                "- Bonus: +5 when employee learns the customer’s name\n"
                "- Bonus: +5 when employee repeats the customer’s name naturally\n"
                "- Bonus: +10 when closing by using the customer’s name and inviting them back warmly\n"
                "- Provide instant feedback inline after responses, without breaking character\n\n"

                "=== Scoring Framework ===\n"
                "- Total Score: 0–100 (very strict)\n"
                "- A perfect 100 requires: upsell + attachment + email collection + rapport + loyalty connection\n"
                "- Bonus points possible (over 100) for exceptional performance\n"
                "- Deduct heavily for pushiness or missing core steps\n"
                "- At '/score': stop role-play, summarize performance, note bonuses (esp. name use)\n"
                "- App handles logging to AppSheet/Google Sheets — do not output JSON\n\n"

                "=== Session Flow ===\n"
                "1. Wait until employee enters their name.\n"
                "2. Greet them: 'Welcome [Name]! The role play will begin now as you notice a customer entering the store who you approach.'\n"
                "3. Role-play begins with 'Customer Approach' in bold, italics short customer non-verbal cues:\n"
                "   • Details noted about customer age range and demographic, products viewed, touched, or near (e.g. *[Female mid 40s walks directly to Vuori rack for Men's light weight hoodie]*)\n"
                "   • Body language / social cues (e.g. *[Customer browses casually]*)\n"
                "   • Visual/style cues brand recognition (e.g. *[Wearing Hoka shirt: great chance to suggest Hoka shoes]*)\n"   
                "4. Interactions continue with natural customer interactions, feedback, and knowledge drops.\n"
                "5. Provide gamified inline feedback after employee responses.\n"
                "6. Stop immediately at '/score'.\n"
                "7. Provide concise feedback summary, noting points earned, bonuses, and deductions.\n"
                "8. Do not output JSON or files — app handles automation.\n\n"

                "=== Simulation Tips ===\n"
                "1. Be engaging and realistic\n"
                "2. Ask open-ended questions to guide the user in the interaction'\n"
                "3. Keep it concise and focused on sales behaviors.\n\n"

                "=== Dual Response Format ===\n"
                "For every employee message, ALWAYS respond in three parts:\n"
                "1. Non-Verbal cues - in bold, italics, short customer non-verbal cues:\n"
                "   • Customer facial reaction cues (e.g. *[Customer raises eye brows and responds pleasantly]*)\n"
                "   • Body language / social cues (e.g. *[Customer crosses arms: seems hesitant]*)\n"
                "   • Visual/style cues brand recognition (e.g. *[Wearing Hoka shirt: great chance to suggest Hoka shoes]*)\n"
                "2. Customer Persona Response — stay fully in character as the customer.\n"
                "3. Coaching Overlay — immediately after, in italics and brackets, give short gamified feedback:\n"
                "   • Green(+1) for strong openers, discovery, rapport, name use\n"
                "   • Green 💲💲 for successful upsells/attachments\n"
                "   • Red 🔴 for pushiness, missed cues, or weak closes\n"
                "   • Sales tactic tips (e.g. *[If they are compaining of foot pain and interested in shoes, also mention custom insoles built from a 3-d scan of their foot]*)\n"
                "- Keep feedback concise and relevant focusing on sales skills, opportunites for product attachments, upsells, recommendations (1–2 sentences max).\n"
                "- Never skip the coaching overlay — it must appear after EVERY customer reply.\n\n"


                "=== Important Notes ===\n"
                "- Always stay in character until '/score'\n"
                "- Never invent JSON, file saves, or payloads\n"
                "- Never invent employee names — use what they gave you\n"
                "- Training should be fast-paced, fun, gamified, but challenging\n"
                "- Model Grivet’s ethos: every customer is family; every interaction builds loyalty\n"
            )
        }
    ]

if "started" not in st.session_state:
    st.session_state.started = False

# =========================
# SIDEBAR QUICK REF
# =========================
with st.sidebar:
    st.subheader("Quick Reference")
    st.markdown("**Main Brands**")
    st.write("Hoka • Brooks • On Running • Vuori • Lululemon • Patagonia • The North Face • Kuhl • LL Bean • Beyond Yoga • YETI • Hydro Flask • Birkenstock • Chaco")
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
    if not st.session_state.started:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Welcome {employee_name}! The role play will begin with you approaching a customer."
                       f"I’ll act as a customer. Go ahead and greet me when you’re ready."
        })
        st.session_state.started = True

    # Chat input area
    user_input = st.chat_input("Say something...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get assistant response from GPT
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

    # Render chat
    for msg in st.session_state.messages[1:]:  # skip system message
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

# =========================
# /SCORE HANDOFF
# =========================
if employee_name and user_input and "/score" in user_input.lower():
    # Ask the model for a strict structured score JSON we can parse quietly
    score_prompt = {
        "role": "system",
        "content": (
            "The employee just typed /score. Stop role-play. "
            "Now, calculate a strict performance score out of 100 based on:\n"
            "- Warmth and greeting\n"
            "- Discovery questions\n"
            "- Identifying customer needs/drivers\n"
            "- Solution presentation\n"
            "- Upsell attempts (💲💲 for wins)\n"
            "- Attachments (socks, insoles, nutrition, accessories)\n"
            "- Email collection\n"
            "- Rapport/community connection\n"
            "- **Name bonuses**: +5 introducing self by name, +5 learning the customer’s name, "
            "+5 repeating it naturally, +10 closing with it and inviting them back\n\n"
            "Scoring must be very difficult. A perfect 100 requires email, upsell, attachment, "
            "and community connection, plus strong name usage. Deduct for pushiness or missed opportunities.\n\n"
            "Return ONLY this JSON (no commentary):\n"
            "{\n"
            "  \"Session Score\": <number>,\n"
            "  \"Asked for Email\": <true/false>,\n"
            "  \"Upsell\": <true/false>,\n"
            "  \"Attachments\": <true/false>,\n"
            "  \"Persona\": \"<persona used>\",\n"
            "  \"Notes\": \"<short feedback summary including name bonuses and deductions>\"\n"
            "}\n"
        )
    }

    score_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages + [score_prompt]
    )

    # Try to parse the JSON safely
    parsed = None
    raw = score_response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except Exception as e:
        st.error(f"⚠️ Could not parse GPT score output: {e}")
        st.code(raw, language="json")

    if parsed:
        # Build the AppSheet payload from parsed fields
        payload = {
            "Action": "Add",
            "Properties": {
                "Locale": "en-US",
                "Timezone": "Central Standard Time",
                "RunAsUserEmail": "test@grivetoutdoors.com"
            },
            "Rows": [
                {
                    "Timestamp": datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                    "Employee Name": employee_name,
                    "Persona": parsed.get("Persona", "Unknown"),
                    "Session Score": parsed.get("Session Score", 0),
                    "Asked for Email": parsed.get("Asked for Email", False),
                    "Upsell": parsed.get("Upsell", False),
                    "Attachments": parsed.get("Attachments", False),
                    "Notes": parsed.get("Notes", "")
                }
            ]
        }

        # Send to AppSheet
        try:
            r = requests.post(APPSHEET_URL, headers=APPSHEET_HEADERS, json=payload, timeout=20)
            if r.status_code == 200:
                st.success("✅ Score submitted to AppSheet!")
            else:
                st.error(f"❌ Error sending to AppSheet: {r.status_code} — {r.text}")
        except Exception as e:
            st.error(f"❌ Network error sending to AppSheet: {e}")

        # Show a concise summary to the employee (not the raw JSON)
        st.subheader("🏁 Session Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⭐ Score", f"{parsed.get('Session Score', 0)} / 100")
        with col2:
            st.metric("📧 Email", "✅ Yes" if parsed.get("Asked for Email") else "❌ No")
        with col3:
            st.metric("💲 Upsell", "✅ Yes" if parsed.get("Upsell") else "❌ No")
        with col4:
            st.metric("🧦 Attachments", "✅ Yes" if parsed.get("Attachments") else "❌ No")

        st.markdown(f"**🧑‍🤝‍🧑 Persona:** {parsed.get('Persona', 'Unknown')}")
        st.markdown(f"**📝 Notes:** {parsed.get('Notes', '')}")


        st.info("🏁 Great work! You can refresh to start a new session or change your name to begin another run.")
