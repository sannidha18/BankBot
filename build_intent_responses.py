import pandas as pd

# Step 1: Load your banking queries
df = pd.read_csv("banking_queries.csv")

# Step 2: Get all unique intents
all_intents = df["intent"].dropna().unique().tolist()
print(f"✅ Found {len(all_intents)} unique intents.")

# Step 3: Define some default responses
default_responses = {
    "check_balance": "Your current account balance is ₹25,000.",
    "transfer_money": "Your transfer request has been initiated successfully.",
    "open_account": "You can open a new account online or at the nearest branch.",
    "loan_query": "We provide personal, home, and car loans. Which one are you interested in?",
    "branch_info": "You can find the nearest branch using our branch locator on the website.",
    "atm_info": "Our ATMs are available 24/7 across the city. Would you like me to share the nearest one?",
    "card_issue": "If your card is lost or blocked, please contact customer care immediately.",
    "statement_request": "You can download your last 5 transactions from internet banking.",
    "unknown": "Sorry, I didn’t quite understand that. Can you rephrase?"
}

# Step 4: Build mapping for ALL intents
data = []
for intent in all_intents:
    if intent in default_responses:
        response = default_responses[intent]
    else:
        response = f"Sorry, I don’t have a response configured yet for '{intent}'."
    data.append({"intent": intent, "response": response})

# Step 5: Save to new CSV
output_file = "intent_responses.csv"
pd.DataFrame(data).to_csv(output_file, index=False, encoding="utf-8")

print(f"✅ Intent-response mapping saved to {output_file}")
