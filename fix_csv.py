import pandas as pd

# Load your original CSV (must have at least: text,intent)
df = pd.read_csv("banking_queries.csv")

# Define some known responses
default_responses = {
    "check_balance": "Your current account balance is ₹25,000.",
    "transfer_money": "Your transfer request has been initiated successfully.",
    "open_account": "You can open a new account online or at the nearest branch.",
    "loan_query": "We provide personal, home, and car loans. Which one are you interested in?",
    "get_interest_rate": "Our current loan interest rates vary depending on the loan type. Please specify personal, home, or business loan.",
    "get_branch_details": "You can find branch details using our branch locator or mobile app.",
    "atm_info": "Our ATMs are available 24/7. Would you like me to share the nearest one?",
    "card_issue": "If your card is lost or blocked, please contact customer care immediately.",
    "statement_request": "You can download your last 5 transactions from internet banking.",
    "unknown": "Sorry, I didn’t quite understand that. Can you rephrase?"
}

# Auto-generate a response for any missing intent
intent_list = df["intent"].unique()
intent_responses = {}

for intent in intent_list:
    if intent in default_responses:
        intent_responses[intent] = default_responses[intent]
    else:
        # Generate placeholder if not defined
        intent_responses[intent] = f"This is a response for intent '{intent}'. (Please customize me!)"

# Add response column
df["response"] = df["intent"].map(intent_responses)

# Save corrected CSV
output_file = "banking_queries_corrected.csv"
df.to_csv(output_file, index=False, encoding="utf-8")

print(f"✅ Corrected file saved as {output_file} with {len(df)} rows and responses for ALL intents.")
