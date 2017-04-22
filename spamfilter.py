
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Spam Filter'
USER_ID = "me"


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-spam-filter.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    response = service.users().messages().list(userId=USER_ID, labelIds=["SPAM"]).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=USER_ID, labelIds=["SPAM"], pageToken=page_token).execute()
        messages.extend(response['messages'])

    i = 0
    for message in messages:
        msg_id = message["id"]
        message = service.users().messages().get(userId=USER_ID, id=msg_id).execute()
        for prop in message["payload"]["headers"]:
            if prop["name"] == "From":
                print("ID:", i, "\tFrom:", prop["value"].encode('ascii','replace'), end="\t")
            elif prop["name"] == "Subject":
                print("Subject:", prop["value"].encode('ascii','replace'))
        i += 1

    to_keep = raw_input("Do you want to keep any emails? [N / 0,1,...] ")
    if "," in to_keep:
        to_keep = to_keep.split(",")
        for i in range(len(to_keep)):
            to_keep[i] = int(to_keep[i])
    elif to_keep != "N":
        to_keep = [int(to_keep)]

    if isinstance(to_keep, list):
        for i in range(len(to_keep)-1,-1,-1):
            msg_labels = {'removeLabelIds': ["SPAM"], 'addLabelIds': ["INBOX"]}
            msg_id = messages[to_keep[i]]["id"]
            message = service.users().messages().modify(userId=USER_ID, id=msg_id, body=msg_labels).execute()
            del messages[to_keep[i]]

    # ANe1BmiDP-rAoJSwkw8T119UU0Z7oisOlVJ4xQ
    # filter0 = service.users().settings().filters().get(userId=USER_ID, id="ANe1BmiDP-rAoJSwkw8T119UU0Z7oisOlVJ4xQ").execute()
    # print(filter0)

    for message in messages:
        msg_id = message["id"]
        # for prop in message["payload"]["headers"]:
        #     if prop["name"] == "From":
        #         start_email = prop["value"].find("<")
        #         end_email = prop["value"].find(">", start_email + 1)
        #         email_address = prop["value"][start_email + 1:end_email]
        # filter0["criteria"]["from"] = filter0["criteria"]["from"] + " OR " + email_address
        service.users().messages().delete(userId=USER_ID, id=msg_id).execute()

    # service.users().settings().filters().delete(userId=USER_ID, id="ANe1BmiDP-rAoJSwkw8T119UU0Z7oisOlVJ4xQ").execute()
    # service.users().settings().filters().create(userId=USER_ID, body=filter0).execute()
    print("All Spam Deleted!")


if __name__ == '__main__':
    main()