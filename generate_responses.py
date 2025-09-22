# generate_responses.py
import pandas as pd
import re
import os

# ---------- CONFIG ----------
INPUT_FILE = "banking_queries.csv"
OUTPUT_CORRECTED = "banking_queries_corrected.csv"
OUTPUT_INTENT_MAP = "intent_responses.csv"
# ----------------------------

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)

# Basic validation
if "intent" not in df.columns or "text" not in df.columns:
    raise ValueError("CSV must contain at least 'text' and 'intent' columns.")

# Helper: normalize intent string for pattern checks
def norm(x):
    return str(x).strip().lower()

# Common heuristic templates keyed by keywords or regex matches
TEMPLATES = [
    (re.compile(r"(balance|current balance|available balance|how much (do i|i) have)"), 
     "Your current account balance is ₹25,000. Would you like a mini statement?"),
    (re.compile(r"(transfer|send money|pay|remit|funds?)"), 
     "I can initiate the transfer. Please provide the amount and recipient account or confirm the details."),
    (re.compile(r"(loan|apply loan|loan status|emi|interest rate|rate)"), 
     "We offer personal, home, car and business loans. Rates depend on loan type — which one do you want details for?"),
    (re.compile(r"(branch|branch near|branch locator|nearest branch|branch details)"), 
     "You can find the nearest branch using our branch locator on the website or mobile app. Would you like me to share the address?"),
    (re.compile(r"(atm|atm near|nearest atm|cash machine)"),
     "The nearest ATM is usually listed in the app. Do you want me to find the nearest ATM now?"),
    (re.compile(r"(open account|create account|new account)"),
     "You can open a new account online in minutes. I can guide you through the documents required (ID proof, address proof)."),
    (re.compile(r"(close account|terminate account|close my account)"),
     "To close your account, please confirm the account number and reason. We will guide you with next steps."),
    (re.compile(r"(card|debit card|credit card|block card|lost card|stolen card|block my card)"),
     "If your card is lost or stolen we can block it immediately. Please confirm the last 4 digits of the card."),
    (re.compile(r"(pin|change pin|reset pin)"),
     "To change your PIN we will send an OTP to your registered mobile number. Proceed? (yes/no)"),
    (re.compile(r"(statement|account statement|download statement)"),
     "I can email your account statement. Which period do you need (1 month / 3 months / 6 months / 1 year)?"),
    (re.compile(r"(interest rate|rates|interest)"),
     "Interest rates depend on product and tenure. Tell me whether you mean savings, FD, or loan rates."),
    (re.compile(r"(fd|fixed deposit|fixed deposit rates)"),
     "FD rates vary by tenure. Tell me the amount and tenure (e.g., ₹50,000 for 1 year) and I will check the rate."),
    (re.compile(r"(kyc|update kyc|upload kyc)"),
     "To update KYC, please upload a government ID and a recent photo. I can guide you to the upload link."),
    (re.compile(r"(forgot password|reset password|can't login|login issue)"),
     "I will send a password reset link to your registered email. Do you want me to send it now?"),
    (re.compile(r"(fraud|unauthorised|unauthorized|unauthorised transaction|report fraud)"),
     "Sorry to hear that. We'll freeze the account and initiate an investigation. Please provide the transaction details (amount/date/merchant)."),
    (re.compile(r"(cheque|check book|stop cheque|cheque status)"),
     "Please provide the cheque number and we'll place a stop payment / check status for you."),
    (re.compile(r"(fee|minim(um )?balance|charges|account fees)"),
     "Monthly maintenance fee and minimum balance details vary by account type. Which account are you asking about?"),
    (re.compile(r"(contact support|customer care|complaint|raise a complaint)"),
     "You can call our customer support at 1800-123-4567 or describe your issue here and I'll raise a complaint for you."),
    (re.compile(r"(thanks|thank you|thx)"),
     "You're welcome! If you need anything else, just ask."),
    (re.compile(r"^(hi|hello|hey|good morning|good afternoon|good evening)$"),
     "Hello! How can I assist you today?"),
    (re.compile(r"(bye|goodbye|see you)"),
     "Thank you for banking with us. Have a great day!")
]

# Fallback templates by intent keywords (if templates above didn't match text)
INTENT_KEYWORD_MAP = {
    "check_balance": "Your current account balance is ₹25,000.",
    "transfer_money": "Your transfer request has been initiated successfully. Please confirm the amount and recipient.",
    "loan_query": "We offer home, car, personal and business loans. Which loan type do you want information about?",
    "get_interest_rate": "Loan interest rates depend on loan type and your profile. Which loan are you asking about (personal/home/business)?",
    "get_branch_details": "You can locate branches using our branch locator on the website or app. Want me to find the nearest one?",
    "branch_info": "Check branch timings and location in the app. Want me to fetch the nearest branch?",
    "atm_info": "ATMs are available 24/7. I can find the nearest ATM for you.",
    "card_issue": "If your card is lost or compromised, we can block it immediately. Confirm last 4 digits to proceed.",
    "statement_request": "I can email your account statement. Which period would you like?",
    "password_reset": "I can send a password reset link to your registered email. Proceed?",
    "report_fraud": "We'll block the account temporarily and start an investigation. Please provide transaction details.",
    "unknown": "Sorry, I didn’t quite understand that. Can you rephrase or be more specific?"
}

# Build intent -> response mapping
unique_intents = sorted(df["intent"].dropna().unique().tolist())
intent_to_response = {}

# create responses
for intent in unique_intents:
    low_intent = norm(intent)

    # 1) If intent matches a direct keyword map, use that
    if intent in INTENT_KEYWORD_MAP:
        intent_to_response[intent] = INTENT_KEYWORD_MAP[intent]
        continue

    # 2) Try to find a matching template by scanning sample texts for that intent
    sample_texts = df.loc[df["intent"] == intent, "text"].astype(str).tolist()
    found = False
    for t in sample_texts[:10]:  # check first 10 examples for intent
        s = t.lower()
        for pattern, template in TEMPLATES:
            if pattern.search(s):
                intent_to_response[intent] = template
                found = True
                break
        if found:
            break
    if found:
        continue

    # 3) Heuristics: look for keywords in intent name itself
    if any(k in low_intent for k in ["balance", "check"]):
        intent_to_response[intent] = "Your current account balance is ₹25,000."
    elif any(k in low_intent for k in ["transfer", "send", "pay"]):
        intent_to_response[intent] = "I can help you transfer money. Please provide amount and recipient details."
    elif any(k in low_intent for k in ["loan", "emi", "interest", "rate"]):
        intent_to_response[intent] = "Loan rates depend on loan type and profile. Which loan do you want details for?"
    elif any(k in low_intent for k in ["branch", "atm", "location", "locator"]):
        intent_to_response[intent] = "You can find nearby branches/ATMs using our locator. Want me to find one now?"
    elif any(k in low_intent for k in ["card", "debit", "credit", "block"]):
        intent_to_response[intent] = "If your card is lost or compromised, we can block it immediately. Confirm last 4 digits."
    elif any(k in low_intent for k in ["statement", "pdf", "download"]):
        intent_to_response[intent] = "I can email your account statement. Which period do you need?"
    elif any(k in low_intent for k in ["password", "login", "reset"]):
        intent_to_response[intent] = "I can send a password reset link to your registered email. Proceed?"
    elif any(k in low_intent for k in ["fraud", "unauthorised", "unauthorized", "report"]):
        intent_to_response[intent] = "We will freeze the account and start an investigation — please provide transaction details."
    else:
        # 4) Default generic response for anything else
        intent_to_response[intent] = f"This is a default reply for intent '{intent}'. (Please customize me!)"

# Map responses back to dataframe
df["response"] = df["intent"].map(intent_to_response)

# Save corrected CSV (row-per-original-query with response)
df.to_csv(OUTPUT_CORRECTED, index=False, encoding="utf-8")

# Also save one-row-per-intent CSV for easy editing
intent_df = pd.DataFrame([{"intent": k, "response": v} for k, v in intent_to_response.items()])
intent_df.to_csv(OUTPUT_INTENT_MAP, index=False, encoding="utf-8")

print(f"✅ Saved corrected queries file: {OUTPUT_CORRECTED} ({len(df)} rows)")
print(f"✅ Saved intent->response map: {OUTPUT_INTENT_MAP} ({len(intent_df)} intents)")
print("You can now load 'banking_queries_corrected.csv' in your app or edit 'intent_responses.csv' to customize replies.")
