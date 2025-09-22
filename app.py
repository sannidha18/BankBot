import os
import json
import csv
import uuid
from datetime import datetime, timedelta
from functools import wraps
import re
import random
from difflib import SequenceMatcher
from flask import Flask, request, jsonify, session, render_template
import re
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory
)

# ------------------------
# CONFIG
# ------------------------
DATA_USERS = "users.json"
DATA_TXNS = "transactions.csv"
SECRET_KEY = "change_this_to_a_random_secret_for_prod"

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SECRET_KEY




def set_transfer_step(step_data):
    session['transfer'] = step_data

def get_transfer_step():
    return session.get('transfer', None)

def clear_transfer_step():
    session.pop('transfer', None)



import csv

def load_banking_queries():
    queries = {}
    with open('banking_queries_corrected.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            queries[row['text'].strip().lower()] = row['response'].strip()
    return queries




# ------------------------
# Helper: initialize demo users (runs once if users.json missing)
# ------------------------
def init_data():
    if not os.path.exists(DATA_USERS):
        demo = {
            "alice": {"password": "alice123", "name": "Alice", "balance": 50000, "account": "100001"},
            "bob":   {"password": "bob123",   "name": "Bob",   "balance": 120000, "account": "100002"},
            "carol": {"password": "carol123", "name": "Carol", "balance": 75000, "account": "100003"},
            "dave":  {"password": "dave123",  "name": "Dave",  "balance": 20000, "account": "100004"},
            "eve":   {"password": "eve123",   "name": "Eve",   "balance": 98000, "account": "100005"}
        }
        with open(DATA_USERS, "w", encoding="utf-8") as f:
            json.dump(demo, f, indent=2)
        print("Initialized users.json with 5 demo users.")

    if not os.path.exists(DATA_TXNS):
        with open(DATA_TXNS, "w", newline='', encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "user", "type", "amount", "to_account", "timestamp", "balance_after", "description"])
        print("Created empty transactions.csv")

init_data()

# ------------------------
# Data helpers
# ------------------------
def load_users():
    with open(DATA_USERS, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(DATA_USERS, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def record_transaction(username, tx_type, amount, to_account=None, description=""):
    users = load_users()
    now = datetime.utcnow().isoformat()
    tx_id = str(uuid.uuid4())
    if username in users:
        if tx_type in ("deposit",):
            users[username]["balance"] = float(users[username]["balance"]) + amount
        elif tx_type in ("withdraw","transfer_out"):
            users[username]["balance"] = float(users[username]["balance"]) - amount
        save_users(users)
        balance_after = users[username]["balance"]
    else:
        balance_after = None

    with open(DATA_TXNS, "a", newline='', encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([tx_id, username, tx_type, amount, to_account or "", now, balance_after, description])

    return {
        "id": tx_id,
        "user": username,
        "type": tx_type,
        "amount": amount,
        "to_account": to_account,
        "timestamp": now,
        "balance_after": balance_after,
        "description": description
    }

def get_user_by_account(account_number):
    users = load_users()
    for u, info in users.items():
        if info.get("account") == str(account_number):
            return u, info
    return None, None

def get_transactions_for_user(username, limit=20):
    rows = []
    if not os.path.exists(DATA_TXNS):
        return rows
    with open(DATA_TXNS, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["user"] == username:
                rows.append(row)
    rows.sort(key=lambda x: x["timestamp"], reverse=True)
    return rows[:limit]

# ------------------------
# Auth decorator
# ------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

# ------------------------
# Routes: login / logout / homepage / portal pages etc.
# (Your original code unchanged for all these below)
# ------------------------
@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        users = load_users()
        if username in users and users[username]["password"] == password:
            session["user"] = username
            return redirect(url_for("homepage"))
        else:
            flash("Invalid username or password", "danger")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))

@app.route("/homepage")
@login_required
def homepage():
    users = load_users()
    username = session["user"]
    info = users[username]
    
    # Pass complete user info like dashboard does
    user_data = {
        "name": info["name"],
        "balance": info["balance"],
        "account": info["account"],
        "username": username
    }
    
    return render_template("homepage.html", user=info["name"], info=user_data)

@app.route("/portal")
@login_required
def portal():
    return redirect(url_for("dashboard"))

@app.route("/portal/dashboard")
@login_required
def dashboard():
    users = load_users()
    username = session["user"]
    info = users[username]

    info_chart = {
        "balance": info["balance"],
        "account_no": info["account"],
        "categories": ["Food", "Rent", "Shopping", "Entertainment", "Other"],
        "amounts": [400, 1000, 500, 300, 300]
    }

    recent = get_transactions_for_user(username, limit=5)
    return render_template("dashboard.html", user=info["name"], info=info_chart, recent=recent)
from functools import wraps
from flask import session, redirect, url_for, request, flash

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            # Redirect to login and pass the original requested path in "next"
            flash("Please login to access this page", "warning")
            return redirect(url_for("login", next=request.path))
        # If user is authenticated, continue to requested route
        return f(*args, **kwargs)
    return decorated
@app.route("/portal/transactions")
@login_required
def transactions():
    users = load_users()
    username = session["user"]
    info = users[username]  # load user info for template
    txs = get_transactions_for_user(username, limit=200)
    return render_template("transactions.html", user=username, txs=txs, info=info)

@app.route("/portal/account", methods=["GET"])
@login_required
def account_page():
    users = load_users()
    username = session["user"]
    info = users.get(username)
    return render_template("account.html", user=username, info=info)


# ------------------------
# API endpoints: deposit, withdraw, transfer, balance, recent
# unchanged from original
# ------------------------
@app.route("/api/deposit", methods=["POST"])
@login_required
def api_deposit():
    username = session["user"]
    amount = float(request.json.get("amount", 0))
    if amount <= 0:
        return jsonify({"error":"Invalid amount"}), 400
    tx = record_transaction(username, "deposit", amount, description="Deposit via portal")
    return jsonify({"ok": True, "tx": tx, "balance": load_users()[username]["balance"]})

@app.route("/api/withdraw", methods=["POST"])
@login_required
def api_withdraw():
    username = session["user"]
    amount = float(request.json.get("amount", 0))
    users = load_users()
    if amount <= 0:
        return jsonify({"error":"Invalid amount"}), 400
    if users[username]["balance"] < amount:
        return jsonify({"error":"Insufficient funds"}), 400
    tx = record_transaction(username, "withdraw", amount, description="Withdraw via portal")
    return jsonify({"ok": True, "tx": tx, "balance": load_users()[username]["balance"]})

@app.route("/api/transfer", methods=["POST"])
@login_required
def api_transfer():
    username = session["user"]
    amount = float(request.json.get("amount", 0))
    to_account = str(request.json.get("to_account", "")).strip()
    users = load_users()
    if amount <= 0:
        return jsonify({"error":"Invalid amount"}), 400
    if users[username]["balance"] < amount:
        return jsonify({"error":"Insufficient funds"}), 400
    recipient_user, rec_info = get_user_by_account(to_account)
    if not recipient_user:
        return jsonify({"error":"Recipient account not found"}), 404
    tx_out = record_transaction(username, "transfer_out", amount, to_account=to_account, description=f"Transfer to {to_account}")
    users = load_users()
    users[recipient_user]["balance"] = float(users[recipient_user]["balance"]) + amount
    save_users(users)
    tx_in = record_transaction(recipient_user, "transfer_in", amount, to_account=users[username]["account"], description=f"Received from {username}")
    return jsonify({"ok": True, "tx_out": tx_out, "tx_in": tx_in, "balance": load_users()[username]["balance"]})

@app.route("/api/balance")
@login_required
def api_balance():
    users = load_users()
    username = session["user"]
    return jsonify({"balance": users[username]["balance"], "account": users[username]["account"]})

@app.route("/api/recent")
@login_required
def api_recent():
    username = session["user"]
    txs = get_transactions_for_user(username, limit=20)
    return jsonify({"transactions": txs})

# ------------------------
# Static files
# ------------------------
@app.route("/static/<path:p>")
def static_proxy(p):
    return send_from_directory("static", p)

# ------------------------
# BankChatbot class with enhanced AI logic
# ------------------------
class BankChatbot:
    def __init__(self):
        
        self.query_responses = load_banking_queries() 
        self.intents = {
    'check_balance': [
        'balance', 'money', 'funds', 'available', 'account balance',
        'how much', 'current balance', 'balance check', 'check balance',
        'show balance', 'my balance', 'amount left', 'what is my balance',
        'show me my balance', 'how much money do i have'
    ],
    'transfer_money': [
        'transfer', 'send', 'move', 'pay', 'payment', 'remit',
        'send money', 'transfer funds', 'make payment', 'wire',
        'remittance', 'i want to transfer', 'send money to',
        'transfer funds to', 'make a payment'
    ],
    'account_info': [
        'account', 'details', 'information', 'account number',
        'account details', 'my account', 'account info', 'personal info',
        'what is my account number', 'show account details',
        'account information', 'profile'
    ],
    'check_history': [
        'history', 'transactions', 'statement', 'mini statement',
        'transaction history', 'recent transactions', 'last', 'past',
        'previous', 'show transaction history',
        'my recent transactions', 'transaction statement'
    ],
    'apply_loan': [
        'loan', 'apply', 'borrow', 'credit', 'mortgage',
        'home loan', 'car loan', 'personal loan',
        'business loan', 'education loan',
        'i want a loan', 'apply for loan', 'loan application'
    ],
    'get_interest_rate': [
        'interest', 'rate', 'interest rate', 'charges',
        'what is the rate', 'loan rate', 'current rates', 'emi',
        'what are the interest rates', 'loan interest rates',
        'current interest rates'
    ],
    'card_info': [
        'card', 'credit card', 'debit card', 'atm card',
        'visa', 'mastercard', 'rupay', 'platinum', 'gold',
        'types of cards', 'what cards do you offer',
        'credit card details', 'debit card information'
    ],
    'lost_card': [
        'lost', 'stolen', 'block', 'missing', 'lost card',
        'card lost', 'card stolen', 'block card', 'freeze card',
        'my card is lost', 'card has been stolen', 'block my card'
    ],
    'create_account': [
        'open', 'create', 'new account', 'account opening',
        'start account', 'begin account',
        'i want to open account', 'create new account',
        'account opening process'
    ],
    'get_branch_details': [
        'branch', 'location', 'address', 'office', 'nearest',
        'branch details', 'find branch', 'bank location', 'atm',
        'where is nearest branch', 'branch locations',
        'find branch near me'
    ],
    'greeting_hi': [
        'hi', 'hello', 'hey', 'good morning', 'good afternoon',
        'good evening', 'help', 'assist', 'start', 'begin',
        'hello there', 'can you help me'
    ],
    'greeting_bye': [
        'bye', 'goodbye', 'thanks', 'thank you', 'done',
        'exit', 'quit', 'finished', "that's all",
        'thank you for your help', "that's all for now"
    ]
}


        self.responses = {
            'check_balance': "Your current account balance is ₹{balance}. Would you like a mini statement?",
            'transfer_money': "Your transfer request has been initiated successfully. Please confirm the amount and recipient.",
            'account_info': "Your account number is {account}. Your account type is {account_type}. Need any other details?",
            'check_history': "Here are your recent transactions. Would you like to see more details for any specific transaction?",
            'apply_loan': "We offer personal, home, car and business loans. Rates depend on loan type — which one do you want details for?",
            'get_interest_rate': "Loan interest rates depend on loan type and your profile. Which loan are you asking about (personal/home/business)?",
            'card_info': "We offer various cards like credit, debit, Visa, Mastercard, RuPay, platinum, and more. Which one would you like details about?",
            'lost_card': "If your card is lost or stolen we can block it immediately. Please confirm the last 4 digits of the card.",
            'create_account': "You can open a new account online in minutes. I can guide you through the documents required (ID proof, address proof).",
            'get_branch_details': "You can locate branches using our branch locator on the website or app. Want me to find the nearest one?",
            'greeting_hi': "Hello! How can I assist you with your banking needs today?",
            'greeting_bye': "You're welcome! If you need anything else, just ask. Have a great day!",
            'default': "I'm here to help with banking services. You can ask about balance, transfers, loans, account details, or branch locations."
        }

        self.branches = [
            {"name": "Main Branch", "address": "123 Banking Street, City Center", "phone": "+91-9876543210"},
            {"name": "Mall Branch", "address": "456 Shopping Mall, Commercial Area", "phone": "+91-9876543211"},
            {"name": "Airport Branch", "address": "789 Airport Road, Terminal 2", "phone": "+91-9876543212"}
        ]

        self.loan_rates = {
            'personal': 12.5,
            'home': 8.5,
            'car': 9.75,
            'business': 11.25,
            'education': 10.5,
            'gold': 8.0
        }

    def extract_amount_and_account(self, text):
        amount_patterns = [
            r'₹\s*([0-9,]+)',
            r'(\d+)\s*rupees?',
            r'rs\.?\s*(\d+)',
            r'(\d+)\s*rs',
            r'transfer\s+(\d+)',
            r'send\s+(\d+)',
            r'(\d+)\s*dollars?'
        ]
        amount = None
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(',', '')
                break

        account_patterns = [
            r'account\s+(?:number\s+)?(\d{6,12})',
            r'to\s+(\d{6,12})',
            r'account\s+(\w+\d+)',
        ]
        account = None
        for pattern in account_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                account = match.group(1)
                break

        return amount, account

    def extract_date_info(self, text):
        today = datetime.now()
        if 'yesterday' in text.lower():
            return today - timedelta(days=1)
        elif 'last week' in text.lower():
            return today - timedelta(days=7)
        elif 'last month' in text.lower():
            return today - timedelta(days=30)
        elif 'today' in text.lower():
            return today
        elif 'tomorrow' in text.lower():
            return today + timedelta(days=1)
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.group(1)) == 4:
                        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                    else:
                        return datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                except ValueError:
                    pass
        return None

    def similarity(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def classify_intent(self, text):
        text_lower = text.lower()
        intent_scores = {}
        for intent, keywords in self.intents.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += len(keyword) * 2
                max_similarity = max([self.similarity(keyword, word) for word in text_lower.split()])
                if max_similarity > 0.7:
                    score += max_similarity * 3
            intent_scores[intent] = score
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                return best_intent[0]
        return 'default'

    def process_message(self, message, username, users_data):
        user_info = users_data.get(username, {})
        intent = self.classify_intent(message)
        response_data = {'response': '', 'action': None, 'data': {}, 'intent': intent}
        
        



        message_lower = message.lower().strip()  
        if message_lower in self.query_responses:
            return {
            'response': self.query_responses[message_lower],
            'action': None,
            'data': {},
            'intent': 'predefined_query'

        }

        if intent == 'check_balance':
            balance = user_info.get('balance', 0)
            response_data['response'] = f"Your current account balance is ₹{balance:,.2f}"
            response_data['data'] = {'balance': balance}
            

        elif intent == 'transfer_money':
            amount, account = self.extract_amount_and_account(message)
            if amount and account:
                response_data['response'] = (
                    f"I can help you transfer ₹{amount:,.2f} to account {account}. "
                    f"Please confirm by replying with your password."
                )
                response_data['action'] = 'awaiting_password'
                response_data['data'] = {'amount': amount, 'to_account': account}
            else:
                response_data['response'] = (
            "I'd be happy to help with your transfer. Please specify the amount and recipient account or username."
        )
        elif intent == 'account_info':
            account_num = user_info.get('account', 'N/A')
            name = user_info.get('name', username)
            response_data['response'] = f"Here are your account details:\n• Account Number: {account_num}\n• Account Holder: {name}\n• Account Type: Savings Account"
            response_data['data'] = {'account': account_num, 'name': name}

        elif intent == 'check_history':
            date_info = self.extract_date_info(message)
            transactions = []
            try:
                if date_info:
            # Filter transactions by date
                    all_txs = get_transactions_for_user(username, limit=200)
                    for tx in all_txs:
                        try:
                            tx_date = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))
                    
                    # Check if transaction matches the requested time period
                            if 'last week' in message.lower():
                                week_ago = datetime.now() - timedelta(days=7)
                                if tx_date >= week_ago:
                                    transactions.append(tx)
                            elif 'last month' in message.lower():
                                month_ago = datetime.now() - timedelta(days=30)
                                if tx_date >= month_ago:
                                    transactions.append(tx)
                            elif 'yesterday' in message.lower():
                                yesterday = datetime.now() - timedelta(days=1)
                                if tx_date.date() == yesterday.date():
                                        transactions.append(tx)
                            elif 'today' in message.lower():
                                if tx_date.date() == datetime.now().date():
                                    transactions.append(tx)
                            else:
                        # Specific date match
                                if tx_date.date() == date_info.date():
                                    transactions.append(tx)
                        except:
                           continue
                    
                    transactions = transactions[:10]  # Limit to 10 most recent
            
                    if transactions:
                        tx_text = f"Recent transactions ({len(transactions)} found):\n\n"
                        for i, tx in enumerate(transactions, 1):
                            try:
                                tx_date = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))
                                date_str = tx_date.strftime('%b %d, %Y %I:%M %p')
                                amount = float(tx['amount'])
                                tx_type = tx['type'].replace('_', ' ').title()
                        
                                if tx['type'] == 'transfer_out':
                                    tx_text += f"{i}. -₹{amount:,.2f} | {tx_type} to {tx.get('to_account', 'N/A')} | {date_str}\n"
                                elif tx['type'] == 'transfer_in':
                                    tx_text += f"{i}. +₹{amount:,.2f} | {tx_type} from {tx.get('to_account', 'N/A')} | {date_str}\n"
                                elif tx['type'] == 'deposit':
                                    tx_text += f"{i}. +₹{amount:,.2f} | {tx_type} | {date_str}\n"
                                elif tx['type'] == 'withdraw':
                                    tx_text += f"{i}. -₹{amount:,.2f} | {tx_type} | {date_str}\n"
                                else:
                                    tx_text += f"{i}. ₹{amount:,.2f} | {tx_type} | {date_str}\n"
                            
                        # Add description if available
                                if tx.get('description'):
                                    tx_text += f"    Description: {tx['description']}\n"
                                tx_text += "\n"
                            except Exception as e:
                                continue
                        
                        response_data['response'] = tx_text.strip()
                    else:
                        time_period = "that period" 
                        if 'last week' in message.lower():
                            time_period = "the last week"
                        elif 'last month' in message.lower():
                            time_period = "the last month"
                        elif 'yesterday' in message.lower():
                            time_period = "yesterday"
                        elif 'today' in message.lower():
                            time_period = "today"
                    
                        response_data['response'] = f"No transactions found for {time_period}."
                else:
            # No specific date, show recent transactions
                    transactions = get_transactions_for_user(username, limit=10)
            
                    if transactions:
                        tx_text = f"Your recent transactions ({len(transactions)} most recent):\n\n"
                        for i, tx in enumerate(transactions, 1):
                            try:
                                tx_date = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))
                                date_str = tx_date.strftime('%b %d, %Y %I:%M %p')
                                amount = float(tx['amount'])
                                tx_type = tx['type'].replace('_', ' ').title()
                        
                                if tx['type'] == 'transfer_out':
                                    tx_text += f"{i}. -₹{amount:,.2f} | {tx_type} to {tx.get('to_account', 'N/A')} | {date_str}\n"
                                elif tx['type'] == 'transfer_in':
                                    tx_text += f"{i}. +₹{amount:,.2f} | {tx_type} from {tx.get('to_account', 'N/A')} | {date_str}\n"
                                elif tx['type'] == 'deposit':
                                    tx_text += f"{i}. +₹{amount:,.2f} | {tx_type} | {date_str}\n"
                                elif tx['type'] == 'withdraw':
                                    tx_text += f"{i}. -₹{amount:,.2f} | {tx_type} | {date_str}\n"
                                else:
                                    tx_text += f"{i}. ₹{amount:,.2f} | {tx_type} | {date_str}\n"
                            
                        # Add description if available
                                if tx.get('description'):
                                    tx_text += f"    Description: {tx['description']}\n"
                                tx_text += "\n"
                            except Exception as e:
                                continue
                        
                        response_data['response'] = tx_text.strip()
                    else:
                        response_data['response'] = "No transactions found in your account."
                
            except Exception as e:
                response_data['response'] = "Sorry, I couldn't retrieve your transactions at the moment. Please try again."
                app.logger.error(f"Transaction history error: {e}")
    
            response_data['data'] = {'transactions': transactions}

        elif intent == 'apply_loan':
            loan_types = ['personal', 'home', 'car', 'business', 'education']
            detected_loan = None
            for loan_type in loan_types:
                if loan_type in message.lower():
                    detected_loan = loan_type
                    break
            if detected_loan:
                rate = self.loan_rates.get(detected_loan, 'Variable')
                response_data['response'] = f"For {detected_loan} loans, our current interest rate is {rate}% per annum. Would you like to start the application process?"
            else:
                response_data['response'] = "We offer personal, home, car, business, and education loans. Which type interests you?"

        elif intent == 'get_interest_rate':
            loan_types_mentioned = [loan for loan in self.loan_rates.keys() if loan in message.lower()]
            if loan_types_mentioned:
                rates_info = []
                for loan_type in loan_types_mentioned:
                    rate = self.loan_rates[loan_type]
                    rates_info.append(f"{loan_type.title()}: {rate}% p.a.")
                response_data['response'] = f"Current interest rates:\n• " + "\n• ".join(rates_info)
            else:
                response_data['response'] = "Here are our current interest rates:\n• Personal Loan: 12.5% p.a.\n• Home Loan: 8.5% p.a.\n• Car Loan: 9.75% p.a.\n• Business Loan: 11.25% p.a."
        elif intent == 'card_info':
            card_types = {
                'credit': "A credit card lets you borrow funds up to a certain limit and pay later with interest.",
                'debit': "A debit card is linked to your account and allows you to spend only your available balance.",
                'visa': "Visa cards are globally accepted and backed by Visa’s secure payment network.",
                'mastercard': "Mastercard provides secure global payments and a range of rewards options.",
                'rupay': "RuPay is an Indian domestic card scheme offering debit and credit cards.",
                'platinum': "Platinum cards offer higher credit limits and premium benefits.",
                'gold': "Gold cards come with additional perks and a slightly higher credit limit than standard cards.",
                'business': "Business cards are designed for company expenses with special accounting features.",
                'prepaid': "A prepaid card is preloaded with funds and is not linked to your bank account."
            }

            detected_card = None
            for card in card_types.keys():
                if card in message.lower():
                    detected_card = card
                    break

            if detected_card:
                response_data['response'] = card_types[detected_card]
            else:
                response_data['response'] = self.responses['card_info']

        elif intent == 'lost_card':
            card_types = ['debit', 'credit', 'atm', 'visa', 'mastercard', 'rupay']
            detected_card = 'card'
            for card_type in card_types:
                if card_type in message.lower():
                    detected_card = f"{card_type} card"
                    break
            response_data['response'] = f"I can immediately block your {detected_card}. For security, please confirm the last 4 digits of your card number."
            response_data['action'] = 'block_card'

        elif intent == 'create_account':
            account_types = ['savings', 'current', 'salary', 'zero balance', 'joint']
            detected_type = None
            for acc_type in account_types:
                if acc_type in message.lower():
                    detected_type = acc_type
                    break
            if detected_type:
                response_data['response'] = f"Great! You can open a {detected_type} account online. You'll need ID proof, address proof, and a passport photo. Shall I guide you through the process?"
            else:
                response_data['response'] = "You can open a new account online in minutes. We offer savings, current, salary, and zero balance accounts. Which type would you prefer?"

        elif intent == 'get_branch_details':
            cities = ['bangalore', 'mumbai', 'delhi', 'chennai', 'hyderabad', 'pune']
            detected_city = None
            for city in cities:
                if city in message.lower():
                    detected_city = city.title()
                    break
            if detected_city:
                sample_branch = random.choice(self.branches)
                response_data['response'] = f"Here's our {detected_city} branch:\n• {sample_branch['name']}\n• Address: {sample_branch['address']}\n• Phone: {sample_branch['phone']}"
            else:
                response_data['response'] = "I can help you find our nearest branch. Could you please share your location or preferred area?"

        elif intent == 'greeting_hi':
            greetings = [
                f"Hello! I'm your SecureBank assistant. How can I help you today?",
                f"Hi there! I'm here to help with all your banking needs.",
                f"Welcome! How may I assist you with your banking services?"
            ]
            response_data['response'] = random.choice(greetings)

        elif intent == 'greeting_bye':
            farewells = [
                "Thank you for using SecureBank! Have a wonderful day!",
                "You're welcome! Feel free to reach out anytime you need help.",
                "Goodbye! We're always here when you need banking assistance."
            ]
            response_data['response'] = random.choice(farewells)

        else:
            response_data['response'] = "I'm here to help with your banking needs! I can assist with:\n• Balance inquiries\n• Money transfers\n• Account information\n• Transaction history\n• Loan applications\n• Branch locations\n\nWhat would you like to know?"
            response_data['intent'] = 'default'
        return response_data

# ------------------------
# Enhanced Chat route replacing simple chat API
# ------------------------
@app.route("/portal/chat", methods=["GET", "POST"])
@login_required
def enhanced_chat():
    if request.method == "GET":
        return render_template("chat.html")
    else:
        try:
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({"error": "No message provided"}), 400

            message = data.get('message', '').strip()
            if not message:
                return jsonify({"error": "Empty message"}), 400

            username = session["user"]
            users = load_users()
            user_info = users.get(username, {})
            balance = float(user_info.get('balance', 0))

            transfer_state = get_transfer_step()

            def parse_amount_and_recipient(message):
                import re
                msg = message.lower().replace(',', '')
                amounts = re.findall(r'\b\d+(?:\.\d+)?\b', msg)
                amount = float(amounts[0]) if amounts else None

                # Try to find recipient after "to" or "account" keywords
                recipient = None
                recipient_match = re.search(r'(to|account|recipient)\s+(\w+)', msg)
                if recipient_match:
                    recipient = recipient_match.group(2)
                else:
                    # Fallback: take last non-numeric word as recipient
                    words = [w for w in msg.split() if not re.match(r'\b\d+(?:\.\d+)?\b', w)]
                    recipient = words[-1] if words else None

                return amount, recipient

            def verify_password(username, password):
                try:
                    users = load_users()
                    return users.get(username, {}).get("password") == password
                except Exception as e:
                    app.logger.error(f"Password verify error: {e}")
                    return False

            def is_transfer_intent(message):
                """Better transfer detection - only trigger on clear transfer requests"""
                msg_lower = message.lower()
                
                # Clear transfer indicators
                transfer_keywords = ['transfer', 'send money', 'pay', 'remit']
                has_transfer_keyword = any(keyword in msg_lower for keyword in transfer_keywords)
                
                # Must have both transfer keyword AND (amount OR recipient)
                has_amount = bool(re.search(r'\b\d+(?:\.\d+)?\b', msg_lower))
                has_recipient = bool(re.search(r'(to|account|recipient)\s+\w+', msg_lower))
                
                return has_transfer_keyword and (has_amount or has_recipient)

            # Handle existing transfer flow
            if transfer_state:
                if transfer_state.get("stage") == "awaiting_details":
                    # Check if user wants to cancel
                    if message.lower() in ["cancel", "stop", "abort"]:
                        clear_transfer_step()
                        return jsonify({"response": "Transfer cancelled."})
                        
                    amount, recipient = parse_amount_and_recipient(message)
                    if not amount or not recipient:
                        return jsonify({"response": "Please specify both amount and recipient username or account number."})

                    recipient_user, recipient_info = None, None
                    if recipient.isdigit():
                        recipient_user, recipient_info = get_user_by_account(recipient)
                    else:
                        recipient_user = recipient.lower()
                        recipient_info = users.get(recipient_user)

                    if not recipient_info:
                        return jsonify({"response": f"Recipient '{recipient}' not found. Please check username or account number."})

                    set_transfer_step({
                        "stage": "awaiting_password",
                        "amount": amount,
                        "to_account": recipient_info['account']
                    })

                    return jsonify({"response": f"You're transferring ₹{amount:,.2f} to {recipient_user}. Please enter your password to confirm."})

                elif transfer_state.get("stage") == "awaiting_password":
                    if message.lower() == "cancel":
                        clear_transfer_step()
                        return jsonify({"response": "Transfer cancelled."})

                    if not verify_password(username, message):
                        return jsonify({"response": "Incorrect password. Please try again or type CANCEL to abort."})

                    set_transfer_step({
                        "stage": "awaiting_confirmation",
                        "amount": transfer_state['amount'],
                        "to_account": transfer_state['to_account']
                    })

                    return jsonify({"response": "Password verified. Please reply CONFIRM to proceed or CANCEL to abort."})

                elif transfer_state.get("stage") == "awaiting_confirmation":
                    if message.upper() == "CONFIRM":
                        amount = transfer_state['amount']
                        to_account = transfer_state['to_account']

                        # Execute transfer manually instead of using test_client
                        try:
                            # Refresh user data to get current balance
                            current_users = load_users()
                            current_balance = float(current_users[username]["balance"])
                            
                            # Check sufficient balance with fresh data
                            if current_balance < amount:
                                clear_transfer_step()
                                return jsonify({"response": f"Transfer failed: Insufficient funds. Your current balance is ₹{current_balance:,.2f}."})
                            
                            # Find recipient
                            recipient_user, recipient_info = get_user_by_account(to_account)
                            if not recipient_user:
                                clear_transfer_step()
                                return jsonify({"response": "Transfer failed: Recipient account not found."})
                                
                            # Execute the transfer
                            # 1. Record outgoing transaction (this updates sender's balance)
                            tx_out = record_transaction(username, "transfer_out", amount, 
                                                      to_account=to_account, 
                                                      description=f"Transfer to {to_account}")
                            
                            # 2. Update recipient balance and record incoming transaction
                            current_users = load_users()  # Reload after sender update
                            current_users[recipient_user]["balance"] = float(current_users[recipient_user]["balance"]) + amount
                            save_users(current_users)
                            
                            # 3. Record incoming transaction for recipient
                            tx_in = record_transaction(recipient_user, "transfer_in", amount, 
                                                     to_account=current_users[username]['account'], 
                                                     description=f"Received from {username}")
                            
                            clear_transfer_step()
                            
                            # Get final updated balance
                            final_users = load_users()
                            new_balance = final_users[username]["balance"]
                            
                            return jsonify({
                                "response": f"✅ Transfer successful! ₹{amount:,.2f} sent to {recipient_user}. Your new balance is ₹{new_balance:,.2f}."
                            })
                            
                        except Exception as e:
                            app.logger.error(f"Transfer execution error: {e}")
                            clear_transfer_step()
                            return jsonify({"response": "Transfer failed due to system error. Please try again."})

                    elif message.upper() in ["CANCEL", "NO", "ABORT"]:
                        clear_transfer_step()
                        return jsonify({"response": "Transfer cancelled."})

                    return jsonify({"response": "Please reply CONFIRM to complete or CANCEL to abort the transfer."})
            # Handle new messages (no active transfer)
            else:
                # Check for clear transfer intent
                if is_transfer_intent(message):
                    # Try to extract details immediately
                    amount, recipient = parse_amount_and_recipient(message)
                    
                    if amount and recipient:
                        # Check if recipient exists
                        recipient_user, recipient_info = None, None
                        if recipient.isdigit():
                            recipient_user, recipient_info = get_user_by_account(recipient)
                        else:
                            recipient_user = recipient.lower()
                            recipient_info = users.get(recipient_user)
                            
                        if not recipient_info:
                            return jsonify({"response": f"Recipient '{recipient}' not found. Please check username or account number."})
                        
                        set_transfer_step({
                            "stage": "awaiting_password",
                            "amount": amount,
                            "to_account": recipient_info['account']
                        })
                        
                        return jsonify({"response": f"You're transferring ₹{amount:,.2f} to {recipient_user}. Please enter your password to confirm."})
                    else:
                        # Start transfer flow
                        set_transfer_step({"stage": "awaiting_details"})
                        return jsonify({"response": "I'll help you transfer money. Please provide the amount and recipient username or account number."})

                # Use chatbot for all other messages
                chatbot = BankChatbot()
                result = chatbot.process_message(message, username, users)
                return jsonify(result)

        except Exception as e:
            import traceback
            app.logger.error(f"Chat error: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                "response": "I'm sorry, I encountered an error. Please try again or contact support if the issue persists.",
                "error": "internal_error"
            }), 500
# ------------------------
# Run
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
