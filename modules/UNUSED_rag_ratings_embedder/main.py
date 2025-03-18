from utils.local_file_handler import LocalFileHandler
from modules.rag_ratings_embedder.text_embedder import TextEmbedderToFile

if __name__ == "__main__":
    configs = LocalFileHandler().load_file(
        file_path="modules/rag_ratings_embedder/config.json"
    )
    embedder = TextEmbedderToFile(info_configs=configs)
    print(embedder.df.head())

    embedder.embed_text()
    embedder.save_embeddings()
