from dataclasses import dataclass

import requests
import numpy as np

from gensim.models import KeyedVectors # type: ignore

#returns the summary of an article given the title, uses wikipedias REST API
def get_article_text(title):
    #make api call to get the summary of the article
    api = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    header = {"User-Agent": "PedantleVersion/1.0 (vardesailee@gmail.com)"}
    response = requests.get(api, headers = header, timeout = 30)

    try:
        response.raise_for_status()
        response = response.json()
        return response.get("extract")

    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

#information about each unique word in the article 
@dataclass
class Info:
    word: str
    locations: list[int]
    best_word: str = ""
    similarity: float = 0.0

#set up dictionary to store the Info for each unique word in the article
#NOTE: deal with punctuation and words not in the model when doing display
def setup_word_info(text, model):
    word_info = {}
    weird = [] #words not in the model
    i = 0
    
    #clean and tokenize the text
    text = text.lower().replace('.,!?()[]{}"\'', ' ').split() 

    for word in text:
        if word not in model:
            weird.append(word)
        elif word not in word_info:
            word_info[word] = Info(word=word, locations=[i])
        else:
            word_info[word].locations.append(i)
        i += 1

    return word_info

def main():
    # load the model from memory
    model = KeyedVectors.load('glove.kv', mmap='r')

    # word = input("Enter a word: ")
    # if word in model:
    #     print(f"Vector for '{word}': {model[word]}")

    text = get_article_text("Earth")
    # text = "Hello world! This is a test article. Hello again."
    article_words = setup_word_info(text, model)
    word_matrix = np.array([model[word] for word in article_words.keys()])
    #word_normalized = word_matrix / np.linalg.norm(word_matrix, axis=1, keepdims=True)

    # for word in article_words:
    #     print(f"Word: {article_words[word].word}, Locations: {article_words[word].locations}")

if __name__ == "__main__":
    main()