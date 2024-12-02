import functions_framework
from flask import request, jsonify, send_file
from PIL import Image
from io import BytesIO
import firebase_admin
from firebase_admin import storage, auth
import logging

# Inicjalizacja Firebase Admin SDK
firebase_admin.initialize_app()

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)

@functions_framework.http
def resize_image(request):
    try:
        # Weryfikacja tokenu uwierzytelniania
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        id_token = auth_header.split('Bearer ')[1]

        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token.get('uid')  # Możesz użyć user_id do dalszych celów
            logging.info(f"Authenticated user ID: {user_id}")
        except Exception as e:
            logging.error(f"Invalid token: {e}")
            return jsonify({"error": "Invalid or expired token"}), 401

        # Sprawdź, czy metoda HTTP to POST
        if request.method != 'POST':
            return jsonify({"error": "Only POST requests are allowed"}), 405

        # Odbierz parametry z żądania
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        file_name = data.get('file_name')  # Nazwa pliku
        target_width = data.get('width')  # Docelowa szerokość
        target_height = data.get('height')  # Docelowa wysokość

        if not all([file_name, target_width, target_height]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Konwersja szerokości i wysokości na liczby całkowite
        target_width = int(target_width)
        target_height = int(target_height)

        # Pobierz obraz z domyślnego Firebase Storage bucket
        bucket = storage.bucket()
        blob = bucket.blob(file_name)
        if not blob.exists():
            return jsonify({"error": f"File '{file_name}' not found in bucket"}), 404

        image_data = blob.download_as_bytes()

        # Otwórz obraz za pomocą Pillow
        image = Image.open(BytesIO(image_data))

        # Pobierz oryginalne wymiary obrazu
        original_width, original_height = image.size

        # Logowanie wymiarów obrazu
        logging.info(f"Original image dimensions: {original_width}x{original_height}")
        logging.info(f"Target dimensions: {target_width}x{target_height}")

        # Sprawdź, czy nowe wymiary nie przekraczają oryginalnych wymiarów
        if target_width > original_width or target_height > original_height:
            return jsonify({
                "error": "Target dimensions exceed original image dimensions",
                "original_dimensions": {"width": original_width, "height": original_height}
            }), 400

        # Zmień rozdzielczość obrazu
        resized_image = image.resize((target_width, target_height))

        # Zapisz zmodyfikowany obraz w pamięci
        output = BytesIO()
        output_format = image.format or "JPEG"
        resized_image.save(output, format=output_format)
        output.seek(0)

        # Wysyłanie zmodyfikowanego obrazu jako odpowiedź HTTP
        return send_file(output, mimetype=f'image/{output_format.lower()}')

    except Exception as e:
        logging.error(f"Error processing the image: {e}")
        return jsonify({"error": str(e)}), 500
