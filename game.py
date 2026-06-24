from gensim.models import KeyedVectors

# load the model from memory
model = KeyedVectors.load('glove.kv', mmap='r')

word = input("Enter a word: ")
if word in model:
    print(f"Vector for '{word}': {model[word]}")
