from watson_developer_cloud import ConversationV1
import json

class ConversationAPI:
    def __init__(self,
                 config):
        self.workspace_id = config['workspace_id']
        self.conversation =  ConversationV1(
            username=config['username'],
            password=config['password'],
            version=config['version']
        )

        # user id to watson context
        self.context_map = dict()

    def lookup(self,user_id):
        if user_id not in self.context_map:
            self.context_map[user_id] = {}
        return self.context_map[user_id]

    def json_response(self,
                      user_id,
                      message):
        response = self.conversation.message(
            workspace_id=self.workspace_id,
            message_input={'text': message},
            context=self.lookup(user_id)
        )
        self.context_map[user_id] = response['context']
        return response

        
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

def akshay_config():
    config = {}
    config['password'] = 'mmRegjAWDWf6' 
    config['username'] = 'a369ed8c-85a9-44a2-9d39-33088ee711e0'
    config['workspace_id'] = '0a4faa68-f36a-4d78-85b9-107e4e94e300'
    config['version'] = '2016-10-28'
    return config

def rohan_graduate_affairs_config():
    config = {}
    config['workspace_id'] = '029946a8-9b63-4716-8a92-22b426627ba2'
    config['username'] = '351251b5-22a9-4f30-9d04-884aff0aae4a'
    config['password'] = 'zwgLdqOlcfYi'
    config['version'] = '2016-09-20'
    return config

def rohan_admissions_config():
    config = {}
    config['workspace_id'] = '08bf5014-cfaf-4b62-b6f6-6064517883f7'
    config['username'] = '351251b5-22a9-4f30-9d04-884aff0aae4a'
    config['password'] = 'zwgLdqOlcfYi'
    config['version'] = '2016-09-20'
    return config

def graduate_affairs_2_config():
    config = {}
    config['workspace_id'] = '2ee0f789-8257-4b46-b1f8-80d3e2242c51'
    config['username'] = '351251b5-22a9-4f30-9d04-884aff0aae4a'
    config['password'] = 'zwgLdqOlcfYi'
    config['version'] = '2016-09-20'
    return config
    

if __name__ == '__main__':
    
    
    watson = ConversationAPI(graduate_affairs_2_config())
    # print watson.message(1, "hi")
    # print watson.message(1, "deadline for phd compsci")
    print watson.json_response(1, "I submitted uah applications (including International House) a while ago. I was wondering when the results will come out? ")
    print watson.json_response(1, "How to transfer my I20 from another school?") 



        
