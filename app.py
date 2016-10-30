import os
import sys
import json
from core import watson
import csv

workspace_id = '0a4faa68-f36a-4d78-85b9-107e4e94e300'
watson = watson.ConversationAPI(workspace_id)

import requests
from flask import Flask, request
from flask import render_template

app = Flask(__name__)

question_user = None
intent_user = None
intent_watson = None
entity_user = None
entity_watson = None

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/feedback', methods=['GET','POST'])
def displayQuestionForm():
    global entity_watson,intent_watson,question_user,entity_user,intent_user
    if request.method=='POST':
        question =  request.form['question']
        question_user = question
        print question
        intents,entities = watson.return_intent_entity('0', question)
        print 'reply='+str(intents[0]['intent'])+str(entities)

        if(len(intents)>0):
            intent_watson = intents[0]['intent']
            if(len(entities)>0):
                entity_watson = entities[0]['entity']
                return render_template("intentEntityForm.html",question = question,intent=intents[0]['intent'],entity=entity_watson)
            else:
                return render_template("intentEntityForm.html",question = question,intent=intents[0]['intent'],entity="entity not found") 
        else:
            return render_template("intentEntityForm.html",question = question,intent="intent not found",entity="entity not found")
    else:
        return render_template("feedbackForm.html")

@app.route('/feedbackSubmit',methods=['POST'])
def feedbackSubmit():
    global entity_watson,intent_watson,question_user,entity_user,intent_user 
    entity_user = request.form['entity_user']
    intent_user = request.form['intent_user']
    print str(entity_watson)+" "+str(intent_watson)+" "+str(entity_user)+" "+str(intent_user)+" "+str(question_user)
    log(str(entity_watson)+" "+str(intent_watson)+" "+str(entity_user)+" "+str(intent_user)+" "+str(question_user))
    with open('dataCollected/dataCollected.csv','a') as csvFile:
        csvFileWriter = csv.writer(csvFile)
        csvFileWriter.writerow([str(question_user),str(entity_watson),str(intent_watson),str(entity_user),str(intent_user)])
    return render_template("thanks.html")

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
        reply = watson.message(sender_id, message_text)

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


    replies = []
    for reply in quick_replies:
        item = {}
        item["content_type"] = "text"
        item["title"] = reply
        item["payload"] = reply + " payload"
        replies.append(item)

    if len(replies):
        data["message"]["quick_replies"] = replies

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
