#just run this all the docs in documents & document_chunks are deleted
from pymongo import MongoClient

client = MongoClient("mongodb+srv://kirand:0PwWoixttlDiIS4q@myteacher-001.4avec70.mongodb.net/?retryWrites=true&w=majority&appName=myteacher-001")  # Use your actual URI
db = client["test_db"]  # Use your actual DB name

db.documents.delete_many({})
db.document_chunks.delete_many({})

print("Cleared!")