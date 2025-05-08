###################################
# HUGGING FACE - IMPLÉMENTATION  #
###################################

# Installation (à exécuter dans votre terminal):
# pip install transformers torch

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# 1. Analyse de sentiment - Façon simple avec pipeline
sentiment_analyzer = pipeline(
    "sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment"
)

textes = [
    "J'adore ce produit, il est fantastique!",
    "Ce service est terrible, je ne recommande pas.",
]

for texte in textes:
    resultat = sentiment_analyzer(texte)
    print(f"Texte: {texte}")
    print(f"Sentiment: {resultat[0]['label']}, Score: {resultat[0]['score']:.4f}\n")

# 2. Classification de texte - Approche plus détaillée
# Chargement explicite du tokenizer et du modèle
model_name = "camembert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Préparation du texte
texte = "Hugging Face propose des modèles d'IA puissants."
encoding = tokenizer(
    texte, return_tensors="pt", padding=True, truncation=True, max_length=128
)

# Prédiction
import torch

with torch.no_grad():
    outputs = model(**encoding)

# 3. Génération de texte
from transformers import AutoModelForCausalLM, AutoTokenizer

# Pour une véritable génération, décommentez ces lignes (attention: téléchargement volumineux)
# tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-560m")
# model = AutoModelForCausalLM.from_pretrained("bigscience/bloom-560m")
# prompt = "Il était une fois, dans un monde où les données"
# inputs = tokenizer(prompt, return_tensors="pt")
# outputs = model.generate(**inputs, max_length=50, num_return_sequences=1, temperature=0.7)
# texte_généré = tokenizer.decode(outputs[0], skip_special_tokens=True)
# print(f"Texte généré: {texte_généré}")

# 4. Extraction d'information (Question-Réponse)
qa_pipeline = pipeline(
    "question-answering", model="distilbert-base-cased-distilled-squad"
)

context = "Paris est la capitale de la France. Elle est connue pour sa culture, son architecture et sa gastronomie."
question = "Quelle est la capitale de la France?"

reponse = qa_pipeline(question=question, context=context)
print(f"\nQuestion: {question}")
print(f"Réponse: {reponse['answer']} (score: {reponse['score']:.4f})")
