from utils.text_embedder import TextEmbedderToFile

if __name__ == "__main__":
    embedder = TextEmbedderToFile(config_file="ratings/config.json")
    print(embedder.df.head())
    embedder.embed_text()
    embedder.save_embeddings()
