class ProfileService:
    def __init__(self):self.profiles={}
    def seed(self,ident,profile):raise NotImplementedError
    def request(self,method,path,headers,body):raise NotImplementedError
