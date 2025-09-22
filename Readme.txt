v3mb8R1jGkfZCZpq  - csbs211536

mongodb compass - mongodb+srv://csbs211536:v3mb8R1jGkfZCZpq@bankingchatbotdb.9efdeu3.mongodb.net/

mongoose - mongodb+srv://csbs211536:v3mb8R1jGkfZCZpq@bankingchatbotdb.9efdeu3.mongodb.net/?retryWrites=true&w=majority&appName=BankingChatbotDB



admin token - eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2ODk0M2Q1NDk0ODU1OTZjMmYxMTY3OTIiLCJyb2xlIjoiYWRtaW4iLCJpYXQiOjE3NTQ1NDU1ODYsImV4cCI6MTc1NDYzMTk4Nn0.MoOQxP3B1BAxc6ZBT40Q1u5VjGwv63UfXMUrt_3-Yb8
id - 68943d549485596c2f116792


python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python train_nlu.py
python app.py