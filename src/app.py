import logging

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import json
import os

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def get_service(credential_json='credentials.json'):
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credential_json, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def get_messages(service, pageToken=None):
    if pageToken:
        return service.users() \
            .messages() \
            .list(userId='me', maxResults=500, pageToken=pageToken) \
            .execute()
    return service.users() \
        .messages() \
        .list(userId='me', maxResults=500) \
        .execute()


def get_all_messages(service):
    totalResults = list()
    pageToken = None
    while True:
        results = get_messages(service, pageToken=pageToken)
        totalResults.append(results)
        if 'nextPageToken' in results:
            pageToken = results['nextPageToken']
            break
        else:
            break
    return totalResults


def count_messages(all_messages):
    totalMessages = 0
    for result in all_messages:
        totalMessages += len(result.get('messages'))
    return totalMessages

def get_message_content(service, msgId):
    return service.users().messages().get(userId='me',id=msgId,format='metadata').execute()


def header_as_json(header):
    fields = 'Date,From,To'.split(',')
    mail_header = {}
    for item in header:
        name = item.get('name')
        if name in fields:
            mail_header[name] = item.get('value')
    return mail_header


def get_headers(service, msgId):
    message = get_message_content(service, msgId)
    try:
        return header_as_json(message['payload']['headers'])
    except:
        return {'Date': None,'From': None,'To': None}


logging.info('Conectando ao Gmail')
service = get_service(credential_json='../credentials.json')

logging.info('Recuperando ID das Mensagens')
all_messages = get_all_messages(service)

total_messages = count_messages(all_messages)
logging.info(f'Total de mensagens capturadas: {total_messages}')

logging.info('Unificando resultados')
ids = list()
for messages in all_messages:
    ids = ids + messages.get('messages')

logging.info('Buscando headers no GMAIL')
headers = list()
for msg in ids[:10]:
    header = get_headers(service, msg.get('id'))
    headers.append(header)

file_output = 'result_headers'
logging.info(f'Gravando resultado em {file_output}')
with open(file_output, 'w') as fopen:
    for header in headers:
        fopen.write(json.dumps(header) + '\n')