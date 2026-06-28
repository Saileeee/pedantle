import requests

#from gensim.models import KeyedVectors # type: ignore

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
    
def main():
    # # load the model from memory
    # model = KeyedVectors.load('glove.kv', mmap='r')

    # word = input("Enter a word: ")
    # if word in model:
    #     print(f"Vector for '{word}': {model[word]}")

    get_article_text("Earth")
    #HERE! determine return type and figure out how to store the vectors

if __name__ == "__main__":
    main()