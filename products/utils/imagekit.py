import os
from dotenv import load_dotenv
from imagekitio import ImageKit

# Load environment variables from .env file
load_dotenv()

imagekit = ImageKit(
    private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
    public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
    url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
)

def upload_image(file, file_name):
    """Upload image to ImageKit and return URL"""
    try:
        upload = imagekit.upload_file(
            file=file,
            file_name=file_name,
            options={}
        )
        
        # Handle different ImageKit SDK versions
        if hasattr(upload, 'url') and upload.url:
            return upload.url
        elif hasattr(upload, 'response') and upload.response:
            return upload.response.get('url', upload.response.get('url'))
        else:
            # Fallback for older versions
            return upload['response']['url']
    except Exception as e:
        print(f"ImageKit upload error: {e}")
        # Return a default image URL or raise the exception
        return "https://via.placeholder.com/300x300.png?text=Image+Error"