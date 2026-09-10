import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

class DenseRetriever:
    def __init__(self, replies_path: str, model_name: str = 'all-MiniLM-L6-v2'):
        print("Loading Dense Retrieval Model (this takes a minute on first run)...")
        self.model = SentenceTransformer(model_name)
        
        self.df = pd.read_csv(replies_path)
        self.df['text'] = self.df['text'].fillna("")
        
        print("Encoding 43,000 historical replies into dense vectors...")
        # Convert text to mathematical embeddings
        self.embeddings = self.model.encode(self.df['text'].tolist(), show_progress_bar=True, convert_to_numpy=True)
        print("Dense Retriever Ready!")

    def search(self, query: str, top_k: int = 3):
        # Encode the customer query
        query_embedding = self.model.encode([query])
        
        # Calculate Cosine Similarity using dot product (since MiniLM normalizes vectors)
        scores = np.dot(self.embeddings, query_embedding.T).flatten()
        
        # Get top K indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "text": self.df.iloc[idx]['text'],
                "score": float(scores[idx])
            })
        return results

