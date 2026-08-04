# Kaijaklike Bot — Deploy លើ Render

## ⚠️ ជំហានទី ០ — Rotate credentials ជាមុនសិន (សំខាន់បំផុត)
Token/API key ចាស់ធ្លាប់លេចមកលើ chat នេះហើយ ត្រូវចាត់ទុកថាមិនសុវត្ថិភាពទៀត៖
1. **Telegram**: ទៅ [@BotFather](https://t.me/BotFather) → `/mybots` → ជ្រើស bot → **API Token** → **Revoke current token** → យក token ថ្មី
2. **CamRapidPay**: ចូល dashboard CamRapidPay → generate API key ថ្មី → បិទ key ចាស់ចោល

កូដក្នុងឯកសារនេះលែងមាន token/key hardcode ទៀតហើយ (ត្រូវការ Environment Variable ១០០%)។

## ជំហានទី ១ — ដាក់ឡើង GitHub
```bash
git init
git add kaijaklike_bot.py requirements.txt render.yaml .env.example README_DEPLOY.md
git commit -m "Kaijaklike bot — ready for Render"
git remote add origin https://github.com/sovannarinsorn-droid/<REPO_NAME>.git
git push -u origin main
```
⚠️ កុំដាក់ `.env` ពិត (ដែលមាន token ពិត) ចូល GitHub ដាច់ខាត — មានតែ `.env.example` ប៉ុណ្ណោះ។

## ជំហានទី ២ — បង្កើត Web Service លើ Render
1. ចូល [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**
2. ភ្ជាប់ GitHub repo ខាងលើ
3. កំណត់៖
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 kaijaklike_bot.py`
   - **Plan**: Free (ឬខ្ពស់ជាងបើចង់)
4. ចូល **Environment** → បន្ថែម variables (តម្លៃពិត មិនមែនតម្លៃឧទាហរណ៍)៖
   | Key | Value |
   |---|---|
   | `BOT_TOKEN` | token ថ្មីពី BotFather |
   | `ADMIN_ID` | `8266854899` |
   | `CAMRAPID_API_KEY` | key ថ្មីពី CamRapidPay |
   | `CONTROL_KEY` | លេខសម្ងាត់ផ្ទាល់ខ្លួន (សម្រាប់ `/shutdown`, `/restart`, `/broadcast` endpoints) |
   | `BOT_DISPLAY_NAME` | `Kaijaklike` |
5. **Create Web Service** — Render នឹង build + deploy ស្វ័យប្រវត្តិ

## ជំហានទី ៣ — រក្សា bot កុំឲ្យដេក (Free tier)
Free tier របស់ Render នឹង "sleep" បើគ្មាន traffic ~15 នាទី។ កូដមាន `_self_ping()` ស្រាប់ដែលអាន `RENDER_EXTERNAL_URL` (Render ផ្តល់ automatically) ដើម្បី ping ខ្លួនឯងរាល់ពេលកំណត់ — មិនចាំបាច់កំណត់អ្វីបន្ថែមទេ។

## ជំហានទី ៤ — ពិនិត្យ
- `https://<your-app>.onrender.com/health` → គួរត្រឡប់ `{"status": "running", "bot": "Kaijaklike"}`
- ផ្ញើ `/start` ទៅ bot ក្នុង Telegram ដើម្បីសាកល្បង

## Premium Emoji (បន្ទាប់ពី deploy)
ប្រើ `/setemojis` (reply ទៅសារមាន premium emoji) និង `/emojilist` (មើលស្ថានភាព) — admin account (`ADMIN_ID`) ត្រូវការ Telegram Premium ដើម្បីឲ្យ icon លេចមុខ។ Bot មាន auto-fallback ស្រាប់ បើ premium emoji បដិសេធ ដោយ Telegram វានឹងប្រើ unicode emoji ធម្មតាវិញដោយស្វ័យប្រវត្តិ — button មិនដែលខូចដោយសារហេតុនេះទេ។
