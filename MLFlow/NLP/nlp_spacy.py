
###########################
# SPACY - IMPLÉMENTATION #
###########################

# Installation (à exécuter dans votre terminal):
# pip install spacy
# python -m spacy download fr_core_news_sm

import spacy

# # Charger le modèle français (petit modèle)
# nlp = spacy.load("fr_core_news_sm")
# Chargement du modèle spaCy pour le français

try:
    nlp = spacy.load("fr_core_news_md")
except:
    # Si le modèle n'est pas installé
    print("Installation du modèle spaCy français...")
    import os

    os.system("python -m spacy download fr_core_news_md")
    nlp = spacy.load("fr_core_news_md")

# Texte d'exemple
texte = """SpaCy est une bibliothèque moderne pour le NLP.
Apple et Google utilisent des technologies similaires."""

# Texte d'exemple
texte = """NLTK est une bibliothèque puissante pour le traitement
du langage naturel. Elle offre de nombreux outils pour l'analyse textuelle."""

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
