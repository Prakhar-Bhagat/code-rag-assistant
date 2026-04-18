from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_community.document_loaders.blob_loaders import FileSystemBlobLoader

def load_codebase(repo_path: str):
    # Manually setting up the loader to be more robust
    loader = GenericLoader(
        FileSystemBlobLoader(
            repo_path, 
            glob="**/*", 
            suffixes=[".py", ".js", ".ts"]
        ),
        LanguageParser(parser_threshold=500)
    )
    return loader.load()