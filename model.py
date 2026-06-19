# Loads Glove vectors and saves them in a format that can be loaded by gensim. 
# This should only need to be run once (and creates the files glove.kv and glove.kv.vectors.npy).

from gensim.models import KeyedVectors

# Load GloVe vectors https://nlp.stanford.edu/projects/glove/
model = KeyedVectors.load_word2vec_format(
    'wiki_giga_2024_300_MFT20_vectors_seed_2024_alpha_0.75_eta_0.05_combined.txt',
    binary=False,
    no_header=True
)

# Save model
model.save('glove.kv')

