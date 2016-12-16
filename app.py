# -*- coding: utf-8 -*-

import os
import sys
import json
from core import watson as w, solr
import psycopg2
import csv
import urlparse
from core.engine import Engine
from autocorrect import spell

watson = w.ConversationAPI(w.graduate_affairs_2_config())
demo_watson = w.ConversationAPI(w.rohan_admissions_config())
engine = Engine('training/question-answers-2016-11-27.tsv', 'training/general-intents.csv')

import requests
import flask
from flask import Flask, request
from flask import render_template
from flask_bootstrap import Bootstrap


def create_app():
  app = Flask(__name__)
  Bootstrap(app)

  return app

app = create_app()


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "<iframe style='height:480px; width:402px' src='https://webchat.botframework.com/embed/columbia_gsa?s=IS8x4dnvEn0.cwA.nDo.jvSNX4-7WysnDMlYSVYIiVsnjjNyWHGjeZUZ396IVH8'></iframe>", 200

@app.route('/feedback', methods=['GET','POST'])
def displayQuestionForm():
    if request.method=='POST':
        question =  request.form['question']
        question = question.replace('\n', ' ').replace('\r', '')
        result = engine.process_message(1,
                                        question,
                                        self_contained=True)
        answer = result['response']
#        intents,entities = watson.return_intent_entity('0', question)
        # print 'reply='+str(intents[0]['intent'])+str(entities)
        solr_response = ''.join(solr.query(question, ['title'])[0]['title'])
        print result['entities']

        if result['intent']:
            intent_watson = result['intent']
        if len(result['entities']):
            entity_watson = result['entities']
        else:
          entity_watson = []
    else:
        return render_template("feedbackForm.html")
            
    return render_template("intentEntityForm.html",
                           question = question,
                           intent=intent_watson,
                           entities=list(entity_watson),
                           link=solr_response,
                           response=answer)

@app.route('/feedbackSubmit',methods=['POST'])
def feedbackSubmit():
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse("postgres://lgqekudqzhiqnc:Cvv7mAL-Ef6U2Pyfc2fHnVPAfm@ec2-54-225-211-218.compute-1.amazonaws.com:5432/d9gtf85ta0q1lv")
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS responses(question_user TEXT, entity_watson TEXT, intent_watson TEXT, solr_response TEXT, bestResponse TEXT);")
    conn.commit();
    bestResponse = request.form['selectBestResponse']
    question_user = request.form['question_user']
    entity_watson = request.form['watson_entity']
    intent_watson = request.form['watson_intent']
    solr_response = request.form['solr_response']
    answer = request.form['engine_response']
    print 'DATA to be inserted to SQL:'
    print 'question user:'+question_user
    print 'best response:'+bestResponse
    print 'entity_watson'+entity_watson
    print 'intent_watson'+intent_watson
    print 'solr_response'+solr_response
    print 'END.'

    log(str(entity_watson)+" "+str(intent_watson)+" "+str(solr_response)+" "+str(bestResponse)+" "+str(question_user))

    cur.execute("INSERT INTO responses(question_user, entity_watson, intent_watson, solr_response, bestResponse) VALUES ('%s','%s','%s','%s','%s');"%(question_user,entity_watson, intent_watson, solr_response, bestResponse))
    conn.commit();
    conn.close()
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

def build_chat_reply(result):
    reply = "Sorry, We cannot help you at this time! Please email SEAS_GSA@columbia.edu for further inquiries."  
    if result['intent'] and result['response']:
      reply = result['response']
    elif len(result['entities']) > 0:
      reply = "Gotcha. So how can I help?"
    return reply 

def build_email_reply(result):
  
  reply = "Sorry, We cannot help you at this time! Please email SEAS_GSA@columbia.edu for further inquiries."  
  if result['intent'] and result['response']:
    reply = result['response']
  return reply

  

@app.route('/test_microsoft', methods=['POST', 'GET'])
def basic_message():
    data = request.get_json()
    log(data)
    source = data['source']
    self_contained = True if source == "email" else False
    conv_id = data['address']['conversation']['id']
    message = data['text']
    message_text = message.replace('\n', ' ').replace('\r', '')

    solr_response = ''.join(solr.query(message_text, ['title'])[0]['title']).strip()
    result = engine.process_message(conv_id,
                                    message_text,
                                    clear_context=self_contained,
                                    self_contained=self_contained)
    response = {}

    reply = build_email_reply(result) if self_contained else build_chat_reply(result)
    if solr_response:
      reply += "We found this link for you: " + solr_response
   
    response['output'] = {'text':[reply]}
    log(response)
    return flask.jsonify(response)

def received_message(messaging_event):
    
    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
    reply = "Sorry, We cannot help you at this time! Please email SEAS_GSA@columbia.edu for further inquiries."
    if "text" in messaging_event["message"]:
        message_text = messaging_event["message"]["text"]
        result = engine.process_message(sender_id,
                                        message_text,
                                        clear_context=False,
                                        guess=True)
        print result
        reply = build_chat_reply(result)

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

def correct_sentence(sentence):
    words = sentence.split()
    for word in words:
        word = spell(word)
    return " ".join(words)

if __name__ == '__main__':
    app.run(debug=True) 
