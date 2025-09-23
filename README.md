# 🏕️ Grivet Sales Trainer

An interactive **Streamlit Cloud app** used by Grivet Outdoors to train retail associates.  
The app simulates customer role-play, lets associates score themselves, and shows a **leaderboard** of top performers pulled from a Google Sheet (linked with AppSheet).  

cat > README.md << 'EOF'
# 🏕️ Grivet Sales Trainer

An interactive **Streamlit Cloud app** used by Grivet Outdoors to train retail associates.  
The app simulates customer role-play, lets associates score themselves, and shows a **leaderboard** of top performers pulled from a Google Sheet (linked with AppSheet).  

---

## 🚀 Features
- Role-play retail training sessions  
- Scoring system (persona, session score, upsell, email capture, notes)  
- Automatic data logging to Google Sheets (via AppSheet)  
- Secure API keys & credentials via Streamlit Cloud **Secrets**  
- Top 20 Leaderboard displayed after each session summary  
- Auto-deploy on Streamlit Cloud with every `git push`  

---

## 📂 Project Structure


---

## 🛠️ Running Locally
1. Clone the repo:
2. Install dependencies: pip install -r requirements.txt
cat > README.md << 'EOF'
# 🏕️ Grivet Sales Trainer

An interactive **Streamlit Cloud app** used by Grivet Outdoors to train retail associates.  
The app simulates customer role-play, lets associates score themselves, and shows a **leaderboard** of top performers pulled from a Google Sheet (linked with AppSheet).  

---

## 🚀 Features
- Role-play retail training sessions  
- Scoring system (persona, session score, upsell, email capture, notes)  
- Automatic data logging to Google Sheets (via AppSheet)  
- Secure API keys & credentials via Streamlit Cloud **Secrets**  
- Top 20 Leaderboard displayed after each session summary  
- Auto-deploy on Streamlit Cloud with every `git push`  

---

## 📂 Project Structure


---

## 🛠️ Running Locally
1. Clone the repo:

2. Install dependencies:

3. Run the app:

4. Open your browser at `http://localhost:8501`.

---

## 🔑 Secrets
Never commit API keys or service account files.  
On **Streamlit Cloud**, store secrets in **Settings → Secrets** in TOML format:

```toml
OPENAI_API_KEY = "sk-your-key"
APPSHEET_KEY = "your-appsheet-key"

[gcp_service_account]
type="service_account"
project_id="..."
private_key_id="..."
private_key="-----BEGIN PRIVATE KEY-----..."
client_email="..."
client_id="..."
token_uri="https://oauth2.googleapis.com/token"

https://grivet.streamlit.app

## 📝 Deployment Checklist
See [DEPLOYMENT.md](DEPLOYMENT.md) for the full step-by-step process.  
