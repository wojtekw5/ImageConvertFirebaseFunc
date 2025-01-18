import functions_framework
from flask import request, jsonify, send_file
from PIL import Image
from io import BytesIO
import firebase_admin
from firebase_admin import storage, auth
import logging

# Firebase Admin SDK initialization
firebase_admin.initialize_app()

# set loggining (logs/debugging) configuration
logging.basicConfig(level=logging.INFO)

@functions_framework.http
def resize_image(request):
    try:
        auth_header = request.headers.get('Authorization') #get authorization header
        if not auth_header or not auth_header.startswith('Bearer '): #is header starts with Bearer
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        id_token = auth_header.split('Bearer ')[1] #get token from authorization header

        try:
            decoded_token = auth.verify_id_token(id_token) #verify token from Firebase Admin SDK
            user_id = decoded_token.get('uid')
            logging.info(f"Authenticated user ID: {user_id}")
        except Exception as e:
            logging.error(f"Invalid token: {e}")
            return jsonify({"error": "Invalid or expired token"}), 401

        # is method POST
        if request.method != 'POST':
            return jsonify({"error": "Only POST requests are allowed"}), 405

        # get parameters from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        file_name = data.get('file_name')  
        target_width = data.get('width')
        target_height = data.get('height')

        if not all([file_name, target_width, target_height]):
            return jsonify({"error": "Missing required parameters"}), 400

        target_width = int(target_width)
        target_height = int(target_height)

        # download image from bucket
        bucket = storage.bucket()
        blob = bucket.blob(file_name)
        if not blob.exists():
            return jsonify({"error": f"File '{file_name}' not found in bucket"}), 404

        # get image from storage as bytes
        image_data = blob.download_as_bytes()

        # save image bytes as Pillow format
        image = Image.open(BytesIO(image_data))

        # get original image size
        original_width, original_height = image.size

        logging.info(f"Original image dimensions: {original_width}x{original_height}")
        logging.info(f"Target dimensions: {target_width}x{target_height}")

        # check: are the target dimensions higher than original
        if target_width > original_width or target_height > original_height:
            return jsonify({
                "error": "Target dimensions exceed original image dimensions",
                "original_dimensions": {"width": original_width, "height": original_height}
            }), 400

        # resize image
        resized_image = image.resize((target_width, target_height))

        # save new image as bytes stream
        output = BytesIO()
        output_format = image.format or "JPEG"
        resized_image.save(output, format=output_format)
        output.seek(0)   # set the file pointer to the beginning (its at the end after saving)

        # Wysyłanie zmodyfikowanego obrazu jako odpowiedź HTTP
        return send_file(output, mimetype=f'image/{output_format.lower()}')  #mimetype = 'image/jpeg'

    except Exception as e:
        logging.error(f"Error processing the image: {e}")
        return jsonify({"error": str(e)}), 500
