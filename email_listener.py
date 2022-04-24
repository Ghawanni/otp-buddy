from logging import info

import grpc
import email_exchange_pb2
import email_exchange_pb2_grpc

import os.path
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(
            userId='me', maxResults=1, labelIds=["INBOX"]).execute()
        messages = results.get('messages', [])
        if not messages:
            print('No Messages found.')
            return
        raw_emails = get_emails_from_id(service, messages)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


def get_emails_from_id(service, messages):
    message_ids = [msg["id"] for msg in messages]
    # print('Messages count: ', len(messages))
    # print('Messages ids: ', message_ids)
    info('Messages count: ', len(messages))
    info('Messages ids: ', message_ids)
    for message in messages:
        message_instance = service.users().messages().get(
            userId='me', id=message["id"], format="raw").execute()
        base64_encoded_html = message_instance["raw"]
        base64_decoded_html = base64.urlsafe_b64decode(
            base64_encoded_html).decode("utf-8")
        # print(base64_decoded_html)
        email_parser(base64_decoded_html)


def email_parser(email) -> None:
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = email_exchange_pb2_grpc.EmailExchangeStub(channel)
        # print(f"email var type: {type(email)}")
        parse_request = email_exchange_pb2.EmailParserRequest(email=email)
        response = stub.SendToParser(parse_request)
        if response.received is True:
            print("Email sent to parser using gRPC successfully: " + str(response))
            return
        print("Something wrong happened please learn gRPC LOOOOL")


if __name__ == '__main__':
    main()
