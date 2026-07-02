from dataclasses import dataclass, field#, InitVar

import requests
import numpy as np
import re

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

#information about each unique word in the article, parallelized lists/dict
@dataclass
class Article_Words:
    # vectors: np.ndarray = field(init=False)
    # model: InitVar[KeyedVectors]
    words: dict[int, str] = field(default_factory=dict)  #NOTE: may be an unnecesary field
    locations: list[list[int]] = field(default_factory=list)
    best_words: list[str] = field(default_factory=list)
    similarities: list[float] = field(default_factory=list)

    # def __post_init__(self, model):
    #     self.vectors = np.array(model[word] for word in self.words.values())


# set up Article_Words object.
# - words is a dictionary mapping the first index of each unique word 
#   in the article to that word
# - locations is a list of the locations of each unique word in the article
# - best_words is a list of the best guess so far for each word
# - similarities is the similarity of the best guess for each word
#The key is the index and the value is an Info object
#NOTE: deal with punctuation and words not in the model when doing display
def setup_article_words(text, model):
    article_words = Article_Words()
    words = {} #unique words in the article mapped to their first index
    weird = set() #words not in the model

    #clean and tokenize the text
    text = re.sub(r'[.,?!\'"()-]', ' ', text)  # replace punctuation with space
    text = text.lower().split() 

    i = 0
    for word in text:
        #if word is not in the model save it and continue
        if word not in model:
            weird.add(word)
            continue
            
        #initialize word if not already seen, otherwise add location
        if word not in words:
            words[word] = i
            article_words.words[i] = word
            article_words.locations.append([i])
            article_words.best_words.append("")
            article_words.similarities.append(0.0)    
            i += 1      
        else:
            article_words.locations[words[word]].append(i)
        
    return article_words

def guess(word: str, article_words: Article_Words, word_matrix: np.ndarray, model):
    if word in model:
        word_vector = model[word]
        similarities = np.dot(word_matrix, word_vector) / (
            np.linalg.norm(word_matrix, axis=1) * np.linalg.norm(word_vector))

        #update the best word and similarity for each word in the article
        #T^T similarities = similarities > 0 should return only vals in s < 0
        i = 0
        for similarity in similarities:
            if similarity > 0:
                #article_words keys are the vectors
                # article_word = article_words.get(vector)
                if similarity > article_words.similarities[i]:
                    article_words.similarities[i] = similarity
                    article_words.best_words[i] = word
            i += 1
  
    else:
        print(f"Word '{word}' not in model.")

def main():
    # load the model from memory
    model = KeyedVectors.load('glove.kv', mmap='r')
    print(model.most_similar("hello", topn=20))

    # # text = get_article_text("Earth")
    # text = "Hello world! This is a test article. Hello again."
    # article_words = setup_article_words(text, model)
    # word_matrix = np.array([model[word] for word in article_words.words.values()])
    # # norm_matrix = word_matrix / np.linalg.norm(word_matrix, axis=1)

    # word = input("Enter a word: ")
    # while word != "exit":
    #     if word in model:
    #         # print(f"Vector for '{word}': {model[word]}")
    #         guess(word, article_words, word_matrix, model)

    #         for index in article_words.words.keys():
    #             print(f"Word: {article_words.words[index]}, Best Word: {article_words.best_words[index]}, Similarity: {article_words.similarities[index]}")
        
    #     word = input("Enter a word: ")

if __name__ == "__main__":
    main()