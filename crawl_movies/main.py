from google.cloud import storage
from config import CONFIG

def crawl_page(request):
    try:
        storage.Client(credentials=[...])
        client = storage.Client(project=CONFIG['PROJECT_NAME'])
        bucket = client.get_bucket(CONFIG['CLOUD_STORAGE_BUCKET'])
        blob = bucket.blob('test.txt')
        blob.upload_from_string('test')
    except Exception as e:
        return str(e)
    
    return 'hello-world'
