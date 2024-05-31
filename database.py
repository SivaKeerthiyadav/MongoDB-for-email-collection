import os
import json
import base64
from pymongo import MongoClient

def get_mongo_client(uri='mongodb://localhost:27017/'):
    return MongoClient(uri)

def save_emails_to_mongodb(messages, service, db_name='email_db', collection_name='mails'):
    # Connect to MongoDB
    client = get_mongo_client()
    db = client[db_name]
    collection = db[collection_name]

    for idx, message in enumerate(messages):
        email_data = {}
        # Get message details
        message_details = service.users().messages().get(userId='me', id=message['id']).execute()
        
        # Extract sender email
        sender = ""
        for header in message_details['payload']['headers']:
            if header['name'] == 'From':
                sender = header['value']
                break
        email_data['sender'] = sender

        # Extract subject
        subject = ""
        for header in message_details['payload']['headers']:
            if header['name'] == 'Subject':
                subject = header['value']
                break
        email_data['subject'] = subject

        # Extract body
        if 'data' in message_details['payload']['body']:
            body = base64.urlsafe_b64decode(message_details['payload']['body']['data']).decode('utf-8')
        else:
            # If message body is in parts
            parts = message_details['payload']['parts']
            body = ''
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        email_data['body'] = body

        # Insert email data into MongoDB and get the inserted ID
        result = collection.insert_one(email_data)
        email_data['_id'] = str(result.inserted_id)  # Convert ObjectId to string for JSON serialization

        # Save email data as JSON file
        save_email_as_json(idx + 1, email_data)

def save_email_as_json(index, email_data, folder_path='emails'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, f'email_{index}.json')
    with open(file_path, 'w') as file:
        json.dump(email_data, file, indent=4)
