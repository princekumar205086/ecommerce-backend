import os
import uuid
import base64
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from imagekitio import ImageKit

# Load environment variables from .env file
load_dotenv()

imagekit = ImageKit(
    private_key=os.environ.get('IMAGEKIT_PRIVATE_KEY'),
    public_key=os.environ.get('IMAGEKIT_PUBLIC_KEY'),
    url_endpoint=os.environ.get('IMAGEKIT_URL_ENDPOINT')
)

def upload_image(file, file_name, folder="products"):
    """
    Upload image to ImageKit and return URL
    Fixed to use base64 encoding for proper image uploads
    """
    try:
        # Handle different input types properly
        if isinstance(file, bytes):
            file_bytes = file
        elif hasattr(file, 'read'):
            # If file is file object, read it
            file.seek(0)  # Ensure we're at the beginning
            file_bytes = file.read()
        else:
            # Handle string paths or other types
            with open(file, 'rb') as f:
                file_bytes = f.read()
        
        # Validate image using PIL
        try:
            img = Image.open(BytesIO(file_bytes))
            img.verify()
            print(f"✅ Image validation successful: {img.format} {img.size}")
        except Exception as e:
            print(f"❌ Image validation failed: {e}")
            raise ValueError(f"Invalid image file: {str(e)}")
        
        # Generate unique filename if needed
        if not file_name or file_name == "":
            ext = ".jpg"  # default extension
            file_name = f"image_{uuid.uuid4()}{ext}"
        elif not os.path.splitext(file_name)[1]:
            file_name += ".jpg"
        
        # Ensure proper file extension
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            base_name = os.path.splitext(file_name)[0]
            file_name = f"{base_name}.jpg"
            ext = ".jpg"
        
        # Create folder path
        if folder:
            full_path = f"{folder}/{file_name}"
        else:
            full_path = file_name
        
        print(f"🔄 Uploading to ImageKit: {full_path}")
        
        # Determine MIME type based on extension
        if ext in ['.png']:
            mime_type = "image/png"
        elif ext in ['.gif']:
            mime_type = "image/gif"
        elif ext in ['.webp']:
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"
        
        # Convert to base64 data URL (this is what works!)
        img_b64 = base64.b64encode(file_bytes).decode('utf-8')
        data_url = f"data:{mime_type};base64,{img_b64}"
        
        # Upload to ImageKit using base64 data URL
        upload_response = imagekit.upload_file(
            file=data_url,
            file_name=full_path
        )
        
        # Extract URL from response
        image_url = None
        if hasattr(upload_response, 'url') and upload_response.url:
            image_url = upload_response.url
        elif hasattr(upload_response, 'response') and upload_response.response:
            if isinstance(upload_response.response, dict):
                image_url = upload_response.response.get('url')
            else:
                # Handle case where response is an object
                image_url = getattr(upload_response.response, 'url', None)
        
        if image_url and isinstance(image_url, str) and image_url.startswith('http'):
            print(f"✅ ImageKit upload successful: {image_url}")
            return image_url
        else:
            print(f"❌ ImageKit upload failed - invalid URL: {upload_response}")
            return None
        
    except Exception as e:
        print(f"❌ ImageKit upload error: {e}")
        import traceback
        traceback.print_exc()
        return None