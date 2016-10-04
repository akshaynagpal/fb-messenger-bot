from watson_developer_cloud import ConversationV1

class ConversationAPI:
    def __init__(self,
                 workspace_id):
        self.workspace_id = workspace_id
        self.conversation =  ConversationV1(
            username='482fc754-cc90-4f98-9e15-11f3975338f3',
            password='p5oKDIsRJHUq',
            version='2016-09-20'
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
            message_input={'text': 'Turn on the lights'},
            context=self.lookup(user_id)
        )
        self.context_map[user_id] = response['context']
        return response['text']



if __name__ == '__main__':
    watson = ConversationAPI('b574127f-00aa-433e-b84b-ef92f4ec7aaa')
    print watson.message(1, "hello")
    print watson.message(1, "turn on the lights")    

        
