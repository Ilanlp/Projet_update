##########################
# NLTK - IMPLÉMENTATION #
##########################

# Installation (à exécuter dans votre terminal):
# pip install nltk

import nltk

# Télécharger les ressources nécessaires (à faire une seule fois)
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Texte d'exemple
texte = "NLTK est une bibliothèque puissante pour le traitement du langage naturel. Elle offre de nombreux outils pour l'analyse textuelle."

# 1. Tokenisation - diviser le texte en mots
tokens = word_tokenize(texte)
print("Tokens:", tokens)

# 2. Filtrage des mots vides (stopwords)
stop_words = set(stopwords.words('french'))
tokens_filtrés = [mot for mot in tokens if mot.lower() not in stop_words]
print("Tokens sans stopwords:", tokens_filtrés)

# 3. Lemmatisation - réduire les mots à leur forme de base
lemmatizer = WordNetLemmatizer()
lemmes = [lemmatizer.lemmatize(mot) for mot in tokens_filtrés]
print("Lemmes:", lemmes)

# 4. Analyse de fréquence
from nltk import FreqDist
distribution = FreqDist(lemmes)
print("Fréquence des mots:", distribution.most_common(5))

# 5. Analyse syntaxique simple
# nltk.download('averaged_perceptron_tagger')
from nltk import pos_tag
tags = pos_tag(tokens)
print("Analyse grammaticale:", tags)


###########################
# SPACY - IMPLÉMENTATION #
###########################

# Installation (à exécuter dans votre terminal):
# pip install spacy
# python -m spacy download fr_core_news_sm

import spacy

# Charger le modèle français (petit modèle)
nlp = spacy.load("fr_core_news_sm")

# Texte d'exemple
texte = "SpaCy est une bibliothèque moderne pour le NLP. Apple et Google utilisent des technologies similaires."

# Traitement complet en une seule ligne!
doc = nlp(texte)

# 1. Tokenisation et analyse grammaticale
print("\nAnalyse spaCy:")
for token in doc:
    print(f"{token.text}\t{token.pos_}\t{token.dep_}\t{token.lemma_}")

# 2. Entités nommées (reconnaissance automatique)
print("\nEntités détectées:")
for entité in doc.ents:
    print(f"{entité.text}\t{entité.label_}")

# 3. Afficher la dépendance syntaxique
print("\nRelations syntaxiques:")
for token in doc:
    print(f"{token.text} --> {token.head.text}")

# 4. Similarité sémantique
doc1 = nlp("intelligence artificielle")
doc2 = nlp("machine learning")
print(f"\nSimilarité entre 'intelligence artificielle' et 'machine learning': {doc1.similarity(doc2)}")

# 5. Visualisation (à décommenter si vous êtes dans un notebook)
# from spacy import displacy
# displacy.render(doc, style='dep', jupyter=True)  # Visualiser la syntaxe
# displacy.render(doc, style='ent', jupyter=True)  # Visualiser les entités


###################################
# HUGGING FACE - IMPLÉMENTATION  #
###################################

# Installation (à exécuter dans votre terminal):
# pip install transformers torch

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# 1. Analyse de sentiment - Façon simple avec pipeline
sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

textes = ["J'adore ce produit, il est fantastique!",
         "Ce service est terrible, je ne recommande pas."]

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
encoding = tokenizer(texte, return_tensors="pt", padding=True, truncation=True, max_length=128)

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
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

context = "Paris est la capitale de la France. Elle est connue pour sa culture, son architecture et sa gastronomie."
question = "Quelle est la capitale de la France?"

reponse = qa_pipeline(question=question, context=context)
print(f"\nQuestion: {question}")
print(f"Réponse: {reponse['answer']} (score: {reponse['score']:.4f})")
