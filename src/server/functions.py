import json
import threading
import traceback
import base64
import numpy as np
import cv2
from bson import json_util
import uuid
import os

from .auth.verifier import Verifier
from .camera_connections.camera_radar import CameraRadar
from .camera_connections.camera_client import CameraClient
from .image_process.process_images import ImageProcessor


PRIVATE_FILES_PATH = "src/server/files/private"

ROUTING_DICT = {}
services = []

verifier = Verifier()

radar = CameraRadar()
radar.start()
services.append(radar)

camera_clients = {}

image_processor = ImageProcessor()
image_processor.start()
services.append(image_processor)


os.makedirs(f'{PRIVATE_FILES_PATH}/blacklist/profile_photos/', exist_ok=True)
blacklist = {}

BLACKLIST_PATH = f'{PRIVATE_FILES_PATH}/blacklist/blacklist.json'
if not blacklist:
    if os.path.isfile(BLACKLIST_PATH):
        with open(BLACKLIST_PATH, 'r') as f:
            blacklist = json.load(f)

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
                    
                    elif required_role == 0 and verifier.check_role(session_id, 1):
                        return {
                            'code' : 401,
                            'content_type' : 'application/json',
                            'data' : json.dumps({'message': 'Unauthorized to access resource'}),
                        }
                except Exception as e:
                    print(e)


                return {
                    'code' : 302,
                    'content_type' : 'application/json',
                    'data' : json.dumps({'message': 'Unauthorized to access resource'}),
                    'additional_headers': {
                        'Location': '/index.html'
                    }
                }
                
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
    
    @staticmethod
    @route("/connect_camera")
    @role(0)
    def create_camera_connection(*args, **kwargs):
        try:
            body = kwargs['body']
            data_dict = json.loads(body)

            camera_ip = data_dict['IP']

            if camera_ip in (camera_details := radar.get_available_cameras()):
                camera_details = camera_details[camera_ip]
                camera_client = CameraClient(camera_ip, camera_details['port'], camera_details['location'])
                threading.Thread(target=camera_client.start).start()
                camera_clients[camera_ip] = camera_client   

                return {
                    'code': 200,
                    'content_type': 'application/json',
                    'data': json.dumps({'message': f'Connected to {camera_ip}'})
                }             

        except Exception as e:
            print(e)
            return {
                'code' : 500,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'could not establish connection', 'error' : str(e)}),
            }

        return {
            'code' : 500,
            'content_type' : 'application/json',
            'data' : json.dumps({'message': 'could not establish connection'}),
        }
    
    @staticmethod
    @route("/disconnect_camera")
    @role(0)
    def disconnect_camera(*args, **kwargs):
        try:
            body = kwargs['body']
            data_dict = json.loads(body)

            camera_ip = data_dict['IP']

            if camera_ip in camera_clients:
                camera_clients[camera_ip].stop()
                del camera_clients[camera_ip]             

        except Exception as e:
            print(e)
            traceback.print_exc()

        return {
            'code' : 500,
            'content_type' : 'application/json',
            'data' : json.dumps({'message': 'could not destroy connection'}),
        }


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
    
    @staticmethod
    @route("/get_connected_cameras")
    @role(1)
    def get_connected_cameras(*args, **kwargs):

        cameras = {}

        try:

            for camera_ip in camera_clients:
                camera = camera_clients[camera_ip]
                cameras[camera_ip] = {
                    'host': camera.host,
                    'port': camera.port,
                    'location': camera.camera_location
                }
        except Exception as e:
            print(e)
            traceback.print_exc()

            return {
                'code' : 500,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'could not fetch connected cameras'}),
            }

        return {
            'code' : 200,
            'content_type' : 'application/json',
            'data' : json.dumps(cameras)
        }
    
    @staticmethod
    def parseSuspectFormData(*args, **kwargs):
        
        body = kwargs['body']
        data_dict = json.loads(body)

        suspect_name = data_dict['fullName']

        images = data_dict['images']

        for idx, image in enumerate(images):
            image_data = base64.b64decode(image.split(',')[1])  # Remove the base64 prefix and decode
            image = np.frombuffer(image_data, dtype=np.uint8)  # Convert to a matrix-like object
            frame = cv2.imdecode(image, cv2.IMREAD_COLOR)
            
            images[idx] = frame

        return suspect_name, images


    @staticmethod
    @route("/searchSuspect")
    @role(1)
    def searchSuspect(*args, **kwargs):
        try:
            suspect_name, images = Functions.parseSuspectFormData(*args, **kwargs)

            person = image_processor.match_suspect_to_person(suspect_name, images)

            if person:
                data = json_util.dumps(person)
                
            else:
                data = json.dumps({'message' : 'Suspect not found!'})

            return {
                'code': 200,
                'content_type': 'application/json',
                'data': data
            }
            
        except Exception as e:
            print(e)
            traceback.print_exc()

            return {
                'code' : 500,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'Failed while searching suspect'}),
            }
        


    @staticmethod
    @route('/addSuspectToBlacklist')
    @role(1)
    def addSuspectToBlacklist(*args, **kwargs):
        try:
            suspect_name, images = Functions.parseSuspectFormData(*args, **kwargs)
            
            embeddings = list(image_processor.get_embeddings(images))

            _id = str(uuid.uuid4())
            
            global blacklist
            
            blacklist[_id] = {
                'suspectName': suspect_name,
                'embeddings': embeddings,
                'profilePhotoUrl': f'/blacklist/profile_photos/{suspect_name.replace(' ', '')}-{_id}.jpg'
            }

            cv2.imwrite(PRIVATE_FILES_PATH + blacklist[_id]['profilePhotoUrl'], image_processor.get_face_from_image(images[0]))

            with open(BLACKLIST_PATH, 'w') as f:
                json.dump(blacklist, f)

            return {
                'code': 200,
                'content_type' : 'application/json',
                'data': json.dumps({'id': _id, 'name': suspect_name,
                                    'embeddingsCount': len(blacklist[_id]['embeddings']),
                                    'profilePhotoUrl': blacklist[_id]['profilePhotoUrl'],
                                    'success': True})
            }

        except Exception as e:
            print(e)
            traceback.print_exc()

            return {
                'code' : 500,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'Failed while adding suspect to blacklist'}),
            }
        

    @staticmethod
    @route('/checkBlacklist')
    @role(1)
    def checkBlackList(*args, **kwargs):
        try:
            criminalsFound = []
            
            for _id in blacklist:
                suspect = blacklist[_id]

                for embedding in suspect['embeddings']:
                    if person := image_processor.match_embedding_to_person(embedding=embedding, suspect_name=suspect['suspectName']):
                        criminalsFound.append(person)
            
            return {
                'code' : 200,
                'content_type': 'application/json',
                'data': json_util.dumps(person)
            }
        except Exception as e:
            print(e)
            traceback.print_exc()
            
            return {
                'code' : 500,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'Failed while searching blacklist'}),
            }
        
    @staticmethod
    def image_to_base64(image_path):
        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            print("Failed to load image. Please check the path and file format.")
            return None
        
        # Convert the image to a format suitable for encoding
        _, buffer = cv2.imencode('.jpg', image)
        
        # Convert the buffer to a byte string
        jpg_as_text = base64.b64encode(buffer)
        
        # Convert byte string to a standard string
        jpg_as_text = jpg_as_text.decode('utf-8')
        
        return jpg_as_text


    @staticmethod
    @route('/getBlacklist')
    @role(1)
    def getBlacklist(*args, **kwargs):
        try:
            global blacklist
               
            data = [{'suspectId': _id, 'fullName': blacklist[_id]['suspectName'], 'embeddingsCount': len(blacklist[_id]['embeddings']), 'profilePhotoUrl': blacklist[_id]['profilePhotoUrl']} for _id in blacklist]

            return {
                'code' : 200,
                'content_type': 'application/json',
                'data': json.dumps(data)
            }

        except Exception as e:
            print(e)
            traceback.print_exc()

            return {
                'code' : 500,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'Failed while retrieving blacklist'}),
            }
        
    @staticmethod
    @route('/removeBlacklistSuspect')
    @role(1)
    def removeBlacklistSuspect(*args, **kwargs):
        try:
            body = kwargs['body']
            data_dict = json.loads(body)

            suspectId = data_dict['id']

            global blacklist

            if suspectId:
                os.remove(PRIVATE_FILES_PATH + blacklist[suspectId]['profilePhotoUrl'])

                del blacklist[suspectId]

                with open(BLACKLIST_PATH, 'w') as f:
                    json.dump(blacklist, f)
            
                return {
                    'code' : 200,
                    'content_type': 'application/json',
                    'data': json.dumps({
                        'message': 'Deleted suspect from blacklist',
                        'success' : True
                    })
                }

        except Exception as e:
            print(e)
            traceback.print_exc()

            return {
                'code' : 500,
                'content_type' : 'application/json',
                'data' : json.dumps({'message': 'Failed while deleting suspect from blacklist',
                                     'success' : False}),
            }
        
        return {
            'code' : 500,
            'content_type' : 'application/json',
            'data' : json.dumps({
                'message': 'Could not delete suspect from blacklist',
                'success' : False
                }),
        }