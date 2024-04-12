import json
from src.server.auth.verifier import Verifier


verifier = Verifier()

class Functions:
        
    @staticmethod
    def login(*args, **kwargs):

        body = kwargs['body']
        data_dict = json.loads(body)

        username = data_dict['username']
        password = data_dict['password']

        if verifier.check_password(username, password):
            return {
                'code' : 302,
                'content_type' : 'text/javascript',
                'data' : """<html><body>Login successful. Redirecting...</body></html>""",
                'additional_headers' : {
                    'Set-Cookie': f'session_id={verifier.generate_session()}; Path=/', 'Location': '/home.html'
                    }
            }
        else:
            return {
                'code' : 401,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'Unauthorized'}),
            }