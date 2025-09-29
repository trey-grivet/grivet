# scoring.py — Structured Scoring Module for Grivet Retail Sales Trainer

def score_introduction(response, customer_name=None):
    score = 0
    r = response.lower()
    if response.strip():
        score += 3
    if any(kw in r for kw in ["i'm ", "my name is", "this is"]):
        score += 2
    if any(kw in r for kw in ["welcome to grivet", "thanks for stopping", "glad you came in", "welcome in"]):
        score += 2
    # Only award if customer actually shared their name
    if customer_name and customer_name.lower() in r:
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_impression(response):
    score = 0
    r = response.lower()
    if response.strip():
        score += 3
    if any(kw in r for kw in ["great to see", "awesome", "excited", "happy you're here", "what adventure"]):
        score += 2
    if any(kw in r for kw in ["favorite way to get outside", "trip", "treating yourself", "exploring new gear"]):
        score += 2
    if any(kw in r for kw in ["hats", "packs", "shoes", "trail", "street"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_discovery(transcript):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["what's the main activity", "tell me about", "how long do you usually", "hotspots", "blisters"]):
        score += 3
    if any(kw in t for kw in ["routine", "gear let you down", "support", "lightweight"]):
        score += 2
    if any(kw in t for kw in ["chews", "hydration", "events", "weather"]):
        score += 2
    if any(kw in t for kw in ["wish your gear", "last outing", "pain points"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_solution(transcript):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["these are great for", "you said you needed", "based on what you shared"]):
        score += 3
    if any(kw in t for kw in ["benefit", "perfect for", "works well if"]):
        score += 2
    if any(kw in t for kw in ["travel", "daily use", "long days", "support"]) and "because" in t:
        score += 2
    if any(kw in t for kw in ["fun fact", "most people don’t realize", "bamboo", "250,000 sweat glands"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_upselling(transcript):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["while you’re trying", "tech sock", "most people also like"]):
        score += 3
    if any(kw in t for kw in ["helps with comfort", "last longer", "works with your shoes"]):
        score += 2
    if any(kw in t for kw in ["hydration", "nutrition", "running hat", "headlamp"]):
        score += 2
    if any(kw in t for kw in ["just a recommendation", "might be worth trying"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_fullsolution(transcript):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["you’re investing", "let’s set you up", "want to check out the kit"]):
        score += 3
    if any(kw in t for kw in ["socks", "insole", "hydration", "shoe cleaner"]):
        score += 2
    if any(kw in t for kw in ["prepare for", "trail ready", "trip ready"]):
        score += 2
    if any(kw in t for kw in ["value", "bundle", "works together"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_objections(transcript):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["totally fair", "makes sense", "that’s valid"]):
        score += 3
    if any(kw in t for kw in ["most customers say", "investment", "long term comfort"]):
        score += 2
    if any(kw in t for kw in ["we have options", "depends on your routine", "never any pressure"]):
        score += 2
    if any(kw in t for kw in ["can solve problems you didn’t realize"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_closing(transcript, customer_name=None):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["ready to go", "box them up", "want to grab these"]):
        score += 3
    # Only award if customer actually shared their name
    if customer_name and customer_name.lower() in t:
        score += 2
    if any(kw in t for kw in ["guarantee", "great choice", "perfect fit"]):
        score += 2
    if any(kw in t for kw in ["invite you back", "next time", "love seeing you again"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_email(transcript):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["can I email", "email your receipt", "save your scan"]):
        score += 3
    if any(kw in t for kw in ["group runs", "tips", "community"]):
        score += 2
    if any(kw in t for kw in ["just for receipts", "no spam", "event invites"]):
        score += 2
    if any(kw in t for kw in ["confirm spelling", "what's a good email"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)

def score_exit(transcript, customer_name=None):
    score = 0
    t = transcript.lower()
    if any(kw in t for kw in ["thanks", "appreciate you", "great to see you"]):
        score += 3
    # Only award if customer actually shared their name
    if customer_name and customer_name.lower() in t:
        score += 2
    if any(kw in t for kw in ["group runs", "see you soon", "next adventure"]):
        score += 2
    if any(kw in t for kw in ["come back anytime", "enjoy your gear", "unstoppable"]):
        score += 2
    if score >= 9:
        score += 1
    return min(score, 10)
