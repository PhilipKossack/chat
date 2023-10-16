#from langchain.llms import CTransformers
from llama_cpp import Llama
from dotenv import find_dotenv, load_dotenv
import box
import yaml
import requests
import os

def download_file(url, filename):
    local_filename = filename
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):  
                f.write(chunk)
    return local_filename

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Import config vars
with open('/config/config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))



url= cfg.MODEL_DOWNLOAD_URL
filename = cfg.MODEL_BIN_PATH


def build_llm():
    if not os.path.exists(filename):
        print("Specified Model not found. Downloading Model...")
        download_file(url,filename)
        print("Download complete.")
    llm = Llama(model_path=cfg.MODEL_BIN_PATH,n_ctx=cfg.NUMBER_OF_TOKENS, n_batch=128,verbose=cfg.VERBOSE) #verbose = False leads to error
    return llm

