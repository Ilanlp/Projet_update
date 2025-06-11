"""Configuration du package MLFlow pipeline."""

from setuptools import setup, find_packages

setup(
    name="jobmarket_ml",
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
        "spacy==3.7.2",
        "transformers==4.51.3",
        "sentence-transformers==4.1.0",
        "huggingface-hub",
        "tqdm==4.66.1",
        "nltk==3.9.1",
        "seaborn==0.13.2",
        "psutil==7.0.0",
    ],
    python_requires=">=3.11",
    author="maikimike",
    description="Pipeline de matching d'emplois avec MLflow",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)