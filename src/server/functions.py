import json
from .auth.verifier import Verifier
import re
import socket
import os
import threading

from .camera_connections.camera_radar import CameraRadar


ROUTING_DICT = {}

verifier = Verifier()

radar = CameraRadar()
radar.start()



class Functions:

    @staticmethod
    def role(required_role):
        def decorator(func):
            def check_cookie(*args, **kwargs):
                try:
                    headers = kwargs['headers']

                    cookies = headers['Cookie'].split('; ')
                    cookies = {key : value for key, value in [item.split('=', 1) for item in cookies]}

                    session_id = cookies['session_id']

                    if verifier.check_role(session_id, required_role) and verifier.check_session(session_id):
                        return func(*args, **kwargs)
                except Exception as e:
                    print(e)

                return (lambda: {
                    'code' : 401,
                    'content_type' : 'application/json',
                    'data' : json.dumps({'message': 'Unauthorized to access resource'}),
                })()
                
            return check_cookie
        return decorator
                
    @staticmethod
    def route(route):
        def router(func):
            ROUTING_DICT[route] = func

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            return wrapper
        return router
    
    @staticmethod
    def verify_credentials(*args, **kwargs):
        try:
            body = kwargs['body']
            data_dict = json.loads(body)

            username = data_dict['username']
            password = data_dict['password']

            return verifier.check_password(username, password)
        except Exception as e:
            print(e)
        
        return False, "unverified"



    @staticmethod
    @route("/login")
    def login(*args, **kwargs):

        is_verified, username = Functions.verify_credentials(*args, **kwargs)

        if is_verified:
            return {
                'code' : 302,
                'content_type' : 'text/javascript',
                'data' : """<html><body>Login successful. Redirecting...</body></html>""",
                'additional_headers' : {
                    'Set-Cookie': f'session_id={verifier.generate_session(username)}; Path=/', 'Location': '/home.html'
                    }
            }
        else:
            return {
                'code' : 401,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'Unauthorized'}),
            }
    

    @staticmethod
    @route("/signup")
    @role(0)
    def signup(*args, **kwargs):
        
        body = kwargs['body']
        data_dict = json.loads(body)

        username = data_dict['username']
        password = data_dict['password']

        is_success, msg = verifier.add_user(username, password)

        if is_success:
            return {
                'code' : 302,
                'content_type' : 'text/javascript',
                'data' : """<html><body>User creation successful. Redirecting...</body></html>""",
                'additional_headers' : {
                    'Location': '/login.html'
                    }
            }
        else:
            return {
                'code' : 401,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': f'{msg}'}),
            }
    
    # @staticmethod
    # @route("/create_camera_connection")
    # # @role(0)
    # def create_camera_connection(*args, **kwargs):
    #     try:

    #         is_verified, username = Functions.verify_credentials(*args, **kwargs)

    #         if is_verified:
    #             session_id = verifier.generate_session(username)
                
    #             if verifier.check_role(session_id, 0):

    #                 return {
    #                     'code' : 200,
    #                     'content_type' : 'application/json',
    #                     'data' : json.dumps({'ip': IP, 'port': PORT, 'session_id': session_id})
    #                 }
    #             else:
    #                 return {
    #                     'code' : 401,
    #                     'content_type' : 'application/json',
    #                     'data' : json.dumps({'message': 'Requires admin privileges'})
    #                 }
    #     except Exception as e:
    #         print(e)

    #     return {
    #         'code' : 500,
    #         'content_type' : 'application/json',
    #         'data' : json.dumps({'message': 'could not establish connection'}),
    #     }
    
    @staticmethod
    @route("/get_updated_camera_radar")
    @role(1)
    def get_updated_camera_radar(*args, **kwargs):
        cameras = radar.get_available_cameras()

        return {
            'code' : 200,
            'content_type' : 'application/json',
            'data' : json.dumps(cameras)
        }