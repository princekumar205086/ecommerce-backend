
def upload_image(file, file_name):
    """Upload image to ImageKit and return URL - Fixed for object response"""
    try:
        # Handle different input types
        if isinstance(file, bytes):
            file_data = file
        else:
            # If file is file object, read it
            file_data = file.read()
        
        upload = imagekit.upload_file(
            file=file_data,
            file_name=file_name,
            options={
                "folder": "/medixmall/products/",
                "use_unique_file_name": True
            }
        )
        
        # Handle object response
        if hasattr(upload, 'url') and upload.url:
            return upload.url
        elif hasattr(upload, 'response') and upload.response:
            return upload.response.get('url', '')
        else:
            print(f"Unexpected upload result: {upload}")
            return "https://via.placeholder.com/300x300.png?text=Image+Error"
            
    except Exception as e:
        print(f"ImageKit upload error: {e}")
        return "https://via.placeholder.com/300x300.png?text=Image+Error"
