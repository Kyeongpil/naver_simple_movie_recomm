import sentencepiece as spm
import ujson as json
from google.cloud import storage


storage.Client()
client = storage.Client.from_service_account_json('My First Project-a8fa96d92514.json')