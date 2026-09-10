import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL = ROOT / "data" / "retrieval"

def main():
    # 1. Load the historical replies
    replies_path = RETRIEVAL / "spotify_replies.csv"
    print(f"Loading historical replies from: {replies_path}")
    df = pd.read_csv(replies_path)
    print(f"Loaded {len(df)} historical Spotify replies.\n")
    
    # Clean up empty text
    df['text'] = df['text'].fillna("")
    
    # 2. Build the search index
    print("Building search index (this takes a few seconds)...")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
    tfidf_matrix = vectorizer.fit_transform(df['text'])
    print("Search index ready!\n")
    
    # 3. Test with a fake customer complaint
    customer_tweet = "@SpotifyCares my premium subscription was charged twice this month, I need a refund please!"
    
    print(f"Customer says: {customer_tweet}\n")
    print("Searching for the top 3 most similar historical replies...")
    print("-" * 50)
    
    # 4. Find the closest matches
    query_vec = vectorizer.transform([customer_tweet])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    
    # Get the indices of the top 3 highest scores
    top_indices = similarities.argsort()[-3:][::-1]
    
    for rank, i in enumerate(top_indices, 1):
        score = similarities[i]
        historical_reply = df.iloc[i]['text']
        print(f"Match #{rank} (Similarity Score: {score:.4f})")
        print(f"Spotify's Historical Reply: {historical_reply}\n")

if __name__ == "__main__":
    main()

