import os
from dotenv import load_dotenv
from imagekitio import ImageKit

# Load environment variables from .env file
load_dotenv()

imagekit = ImageKit(
    private_key=os.environ['IMAGEKIT_PRIVATE_KEY'],
    public_key=os.environ['IMAGEKIT_PUBLIC_KEY'],
    url_endpoint=os.environ['IMAGEKIT_URL_ENDPOINT']
)

def upload_image(file, file_name):
    upload = imagekit.upload_file(
        file=file,
        file_name=file_name,
        options={}
    )
    return upload['response']['url']