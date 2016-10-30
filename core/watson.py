from watson_developer_cloud import ConversationV1
import json

class ConversationAPI:
    def __init__(self,
                 workspace_id):
        self.workspace_id = workspace_id
        self.conversation =  ConversationV1(
            username='a369ed8c-85a9-44a2-9d39-33088ee711e0',
            password='mmRegjAWDWf6',
            version='2016-10-28'
        )

        # user id to watson context
        self.context_map = dict()

    def lookup(self,user_id):
        if user_id not in self.context_map:
            self.context_map[user_id] = {}
        return self.context_map[user_id]
    # Send message to watson conversation agent
    def message(self,
                user_id,
                message):
        response = self.conversation.message(
            workspace_id=self.workspace_id,
            message_input={'text': message},
            context=self.lookup(user_id)
        )
        self.context_map[user_id] = response['context']

        print json.dumps(response)
        return ''.join(response['output']['text'])

    def return_intent_entity(self,
                user_id,
                message):
        response = self.conversation.message(
            workspace_id=self.workspace_id,
            message_input={'text': message},
            context=self.lookup(user_id)
        )
        self.context_map[user_id] = response['context']

        print json.dumps(response)
        return response['intents'],response['entities']

    
if __name__ == '__main__':
    workspace_id = '0a4faa68-f36a-4d78-85b9-107e4e94e300'
    watson = ConversationAPI(workspace_id)
    # print watson.message(1, "hi")
    # print watson.message(1, "deadline for phd compsci")
    print watson.message(1, "I have a problem with my crd")
    print watson.message(1, "I have an issue with my UNI") 


        
