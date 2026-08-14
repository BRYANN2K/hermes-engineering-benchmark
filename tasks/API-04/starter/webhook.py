class WebhookReceiver:
    def __init__(self,secret,tolerance,clock):pass
    def handle(self,headers,body):raise NotImplementedError
    def accepted_ids(self):return ()
