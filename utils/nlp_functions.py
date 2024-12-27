from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def filter_stopwords(text: str) -> str:
    stop_words = set(stopwords.words("english"))
    word_tokens = word_tokenize(text)
    filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]
    return " ".join(filtered_sentence)
