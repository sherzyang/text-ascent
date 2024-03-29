import pickle
import os
import requests

import numpy as np
import pandas as pd
import textstat
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine, cdist


def download_and_open(url, mode="rb", folder="data"):
    """Downloads the specified file if it isn't already downloaded, then opens it."""
    filename = os.path.basename(url)
    pathname = os.path.join(folder, filename)
    if not os.path.exists(pathname):
        response = requests.get(url)
        with open(pathname, "wb") as f:
            f.write(response.content)
    return open(pathname, mode)


with download_and_open(
    r"https://text-ascent.s3-us-west-2.amazonaws.com/clean_df.pkl", "rb"
) as input_file:
    clean_df = pickle.load(input_file)
    clean_df["url"] = clean_df["title"].apply(
        lambda title: f'https://en.wikipedia.org/wiki/{title.replace(" ", "_")}'
    )


def load_vectorizer(
    pickle_file="https://text-ascent.s3-us-west-2.amazonaws.com/vectorizer.pkl"
):
    """Loads the trained TF/IDF vectorizer."""
    with download_and_open(pickle_file, "rb") as f:
        return pickle.load(f)


def load_corpus_vectors(
    pickle_file="https://text-ascent.s3-us-west-2.amazonaws.com/corpus_vectors.pkl"
):
    """Loads the corpus vectors."""
    with download_and_open(pickle_file, "rb") as f:
        return pickle.load(f)


def get_vocab_arr(vec):
    """Get the vocabulary array."""
    n_features = len(vec.vocabulary_)
    vocab_arr = np.empty(n_features, dtype=object)
    for word, idx in vec.vocabulary_.items():
        vocab_arr[idx] = word
    return vocab_arr


def get_top_k_vector(vector, feature_ranking, k=20):
    """Return the top k vector according to feature_ranking."""
    return vector[:, feature_ranking[:k]]


def top_k_text(text, k=50):
    """Return fifty of the most similar articles to the user input sorted by reading score. Display five articles at a time."""
    vec = load_vectorizer()
    corpus_vectors = load_corpus_vectors()
    sample_vector = vec.transform([text]).toarray()
    feature_ranking = np.argsort(sample_vector[0])[::-1]
    vocab_arr = get_vocab_arr(vec)

    distances = cdist(
        get_top_k_vector(sample_vector, feature_ranking),
        get_top_k_vector(corpus_vectors, feature_ranking),
    )

    nearest_article_idxs = np.argsort(distances)
    nearest_articles = clean_df.loc[nearest_article_idxs[0], :]

    top_k = nearest_articles[:k].copy()
    top_k = top_k.sort_values(["score"], ascending=False)
    top_k["i"] = list(range(k))[::-1]  # won't change
    top_k["style"] = "display: none"
    top_k.loc[(top_k["i"] >= 22) & (top_k["i"] < 27), "style"] = ""
    return top_k
