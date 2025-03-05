import re

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def evaluate_quality_words_over_thresh(text: str, threshold: int = 5) -> str:
    word_tokens = word_tokenize(text)
    return len(word_tokens) > threshold


def filter_stopwords(text: str) -> str:
    stop_words = set(stopwords.words("english"))
    word_tokens = text.split(" ")
    filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]
    return " ".join(filtered_sentence)


def strip_special_chars_and_lower(text: str) -> str:
    text = re.sub(r"[^\w\s.]", "", text)
    return text.strip().lower()


def replace_from_replacement_dict(text: str, replace_dict: dict) -> str:
    for k, v in replace_dict.items():
        if v != "PLACEHOLDER":
            text = text.replace(k, v)
    return text


def initial_components_processing(row, replace_dict: dict = {}) -> list:
    row = row.replace("\n", "").replace("\r", "").replace("\t", "")
    row = re.sub("([a-z0-9])([A-Z])", r"\1 \2", row)  # split words on Snake case
    row = row.lower()  # make row all lower case
    row = replace_from_replacement_dict(row, replace_dict)  # get rid of common GPT text
    row = re.sub(
        r"[^\w\s.,:]", "", row
    )  # get rid of special characters except for periods, commas, :
    return row.strip()


def identify_major_component_starting_sentence(major_categories, sentence_component):
    for major_component in major_categories:
        if sentence_component.startswith(major_component):
            return major_component, sentence_component.split(major_component)[1]
    return "", sentence_component


def clean_simplify_major_categories(text, category_dict: dict, strip_list: list):
    for k, v in category_dict.items():
        if text.startswith(k) and v != "PLACEHOLDER":
            text = text.replace(k, v)
    for k in strip_list:
        if text.startswith(k):
            return k
    return text


def clean_field_to_integral_components(row):
    row = initial_components_processing(row)
    components = [x.split(". ")[-1] for x in row.split(":")][:-1]
    # components = [initial_components_processing(x) for x in components]
    components = [
        re.sub(r"[^\w\s]", "", x).replace("  ", " ").replace("''", "").strip()
        for x in components
        if x.strip() != ""
    ]
    components = [" ".join(x.split(" ")[:5]) for x in components]
    return components


def build_sentiment_elements(incoming_row, category_dict: dict, strip_list: list):

    split_components = {}

    major_categories = clean_field_to_integral_components(incoming_row)

    row = initial_components_processing(incoming_row)

    for major_category in major_categories:
        this_entry = row.split(f"{major_category}:")[-1].split(".")[0]
        this_entry = re.sub(r"[^\w\s]", "", this_entry).replace("  ", " ").strip()
        this_entry = filter_stopwords(this_entry)
        split_components[major_category] = this_entry

    sentence_components = [
        f"{clean_simplify_major_categories(k, category_dict, strip_list)} {v}".replace(
            "  ", " "
        )
        for k, v in split_components.items()
    ]

    major_categories = [
        clean_simplify_major_categories(k, category_dict, strip_list)
        for k in major_categories
        if k != ""
    ]

    return major_categories, sentence_components
