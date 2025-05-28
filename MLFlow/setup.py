"""Configuration du package MLFlow pipeline."""

from setuptools import setup, find_packages

setup(
    name="pipeline_grid_search",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "setuptools",
        "wheel==0.42.0",
        "numpy==1.24.3",
        "pandas==2.0.3",
        "scikit-learn==1.6.0",
        "mlflow==2.22.0",
        "spacy==3.8.4",
        "transformers==4.51.3",
        "sentence-transformers==4.1.0",
        "huggingface-hub",
        "tqdm==4.66.1",
        "nltk==3.9.1",
    ],
    python_requires=">=3.8",
    author="Mika",
    description="Pipeline de matching d'emplois avec MLflow",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # Dépendances spaCy qui nécessitent un traitement spécial
    dependency_links=[
        "https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.8.0/fr_core_news_sm-3.8.0.tar.gz#egg=fr_core_news_sm",
        "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.tar.gz#egg=en_core_web_sm"
    ]
) 