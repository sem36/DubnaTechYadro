import requests

FASTAPI_URL = "http://127.0.0.1:8000/process_image/"

def get_breed_from_image(photo_path):
    with open(photo_path, 'rb') as photo:
        response = requests.post(FASTAPI_URL, files={"file": ("photo.jpg", photo)})
    
    if response.status_code == 200:
        result = response.json()
        return result.get("prediction")
    else:
        return None