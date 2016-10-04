import os
import sys
import json
from core import watson

workspace_id = 'b574127f-00aa-433e-b84b-ef92f4ec7aaa'
watson = watson.ConversationAPI(workspace_id)

import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message
                    received_message(messaging_event)
                if messaging_event.get("delivery"):  # delivery confirmation
                    received_delivery(messaging_event)
                if messaging_event.get("optin"):  # optin confirmation
                    received_confirmation(messaging_event)
                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    received_postback(messaging_event)

    return "ok", 200


def received_message(messaging_event):
    
    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
    reply = "Sorry, cannot help you at this time!"
    if "text" in messaging_event["message"]:
        message_text = messaging_event["message"]["text"]
        reply = unicode(watson.message(sender_id, message_text),'utf-8')

    send_message(sender_id, reply)

def received_delivery(messaging_event):
      sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
      recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

#      send_message(sender_id, ", thanks!")
      
def received_confirmation(messaging_event):
      sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
      recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

#      send_message(sender_id, "got the confirmation, thanks!")

def received_postback(messaging_event):
      sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
      recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

      send_message(sender_id, "got the postback, thanks!")

      
def send_message(recipient_id, message_text, quick_replies = []):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    }

    data["message"]["quick_replies"] = []

    for reply in quick_replies:
        item = {}
        item["content_type"] = "text"
        item["title"] = reply
        item["payload"] = reply + " payload"
        data["message"]["quick_replies"].append(item)

    data = json.dumps(data)
    log(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':

    app.run(debug=True)
