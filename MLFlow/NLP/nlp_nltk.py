##########################
# NLTK - IMPLÉMENTATION #
##########################

# Installation (à exécuter dans votre terminal):
# pip install nltk

import nltk

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import FreqDist
from nltk import pos_tag


# Télécharger les ressources nécessaires (à faire une seule fois)
nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("averaged_perceptron_tagger")
nltk.download("averaged_perceptron_tagger_eng")

# Texte d'exemple
texte = """NLTK est une bibliothèque puissante pour le traitement
du langage naturel. Elle offre de nombreux outils pour l'analyse textuelle."""

# 1. Tokenisation - diviser le texte en mots
tokens = word_tokenize(texte)
print("\nTokens:", tokens, "\n")

# 2. Filtrage des mots vides (stopwords)
stop_words = set(stopwords.words("french"))
tokens_filtrés = [mot for mot in tokens if mot.lower() not in stop_words]
print("Tokens sans stopwords:", tokens_filtrés, "\n")

# 3. Lemmatisation - réduire les mots à leur forme de base
lemmatizer = WordNetLemmatizer()
lemmes = [lemmatizer.lemmatize(mot) for mot in tokens_filtrés]
print("Lemmes:", lemmes, "\n")

# 4. Analyse de fréquence

distribution = FreqDist(lemmes)
print("Fréquence des mots:", distribution.most_common(5))

# 5. Analyse syntaxique simple
tags = pos_tag(tokens)
print("Analyse grammaticale:", tags)
