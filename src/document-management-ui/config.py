# Imports
# Env var
import os
import sys
from dotenv import load_dotenv, find_dotenv


_env = ".env"

def get_env():
    return _env

def set_env(env):
    global _env 
    _env = env
    _ = load_dotenv(find_dotenv(env), override=True)

sys.path.append('.')
_ = load_dotenv(find_dotenv(get_env()), override=True)

PATH_NAME_SPLITTER = './splitted_docs.jsonl'
EVALUATION_DATASET = '../data/evaluation_dataset.tsv'

def get_env_var(key, default=None):
    """Get environment variable with optional default"""
    return os.environ.get(key, default)

# Firestore configuration
GCP_PROJECT_ID = get_env_var("GCP_PROJECT_ID")
FIRESTORE_DATABASE = get_env_var("FIRESTORE_DATABASE", "(default)")
FIRESTORE_COLLECTION = get_env_var("FIRESTORE_COLLECTION", "documents")
FIRESTORE_CREDENTIALS_PATH = get_env_var("FIRESTORE_CREDENTIALS_PATH")
