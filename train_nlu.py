import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example
import random
import json
import os

# Load or create a blank English pipeline
nlp = spacy.blank("en")

# Add the text classifier to the pipeline
if "textcat" not in nlp.pipe_names:
    textcat = nlp.add_pipe("textcat", last=True)
else:
    textcat = nlp.get_pipe("textcat")

# Load intent examples
with open("intent_config.json", "r") as f:
    intent_data = json.load(f)

# Add labels (intents) to the text classifier
for intent in intent_data:
    textcat.add_label(intent)

# Prepare training data
train_data = []
for intent, examples in intent_data.items():
    for text in examples:
        train_data.append((text, {"cats": {intent: 1.0}}))

# Shuffle data
random.shuffle(train_data)

# Optional: split into train and test
split = int(0.8 * len(train_data))
train_examples = train_data[:split]
test_examples = train_data[split:]

# Training loop
optimizer = nlp.begin_training()
print("Training NLU model...")

for epoch in range(20):  # 20 epochs
    losses = {}
    batches = minibatch(train_examples, size=compounding(4.0, 32.0, 1.5))
    for batch in batches:
        examples = []
        for text, annotations in batch:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            examples.append(example)
        nlp.update(examples, sgd=optimizer, drop=0.2, losses=losses)
    print(f"Epoch {epoch + 1} Losses: {losses}")

# Save the trained model
output_dir = "nlu_model"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
nlp.to_disk(output_dir)
print(f"Model saved to {output_dir}")

# -----------------------------
# Calculate accuracy on test set
# -----------------------------
correct = 0
total = 0

for text, annotations in test_examples:
    doc = nlp(text)
    predicted_label = max(doc.cats, key=doc.cats.get)
    true_label = max(annotations["cats"], key=annotations["cats"].get)
    if predicted_label == true_label:
        correct += 1
    total += 1

accuracy = correct / total if total > 0 else 0
print(f"Accuracy on test data: {accuracy:.2%}")
