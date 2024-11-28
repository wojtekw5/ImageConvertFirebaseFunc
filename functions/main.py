import functions_framework
from flask import request, jsonify, send_file
from PIL import Image
from io import BytesIO

import firebase_admin
from firebase_admin import credentials, storage

# Inicjalizacja Firebase Admin SDK
cred = credentials.Certificate("C:/Users/wojte/Desktop/cloudspark-42ed1-firebase-adminsdk-8ks4v-51268fcc0a.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'cloudspark-42ed1.firebasestorage.app/images'
})

@functions_framework.http
def resize_image(request):
    try:
        # Sprawdź, czy metoda HTTP to POST
        if request.method != 'POST':
            return jsonify({"error": "Only POST requests are allowed"}), 405

        # Odbierz parametry z żądania
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        bucket_name = data.get('bucket')  # Nazwa bucketa
        file_name = data.get('file_name')  # Nazwa pliku
        target_width = data.get('width')  # Docelowa szerokość
        target_height = data.get('height')  # Docelowa wysokość

        if not all([bucket_name, file_name, target_width, target_height]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Konwersja szerokości i wysokości na liczby całkowite
        target_width = int(target_width)
        target_height = int(target_height)

        # Pobierz obraz z Firebase Storage
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_name)
        if not blob.exists():
            return jsonify({"error": f"File '{file_name}' not found in bucket '{bucket_name}'"}), 404

        image_data = blob.download_as_bytes()

        # Otwórz obraz za pomocą Pillow
        image = Image.open(BytesIO(image_data))

        # Zmień rozdzielczość obrazu
        resized_image = image.resize((target_width, target_height))

        # Zapisz zmodyfikowany obraz w pamięci
        output = BytesIO()
        resized_image.save(output, format=image.format)
        output.seek(0)

        # Wysyłanie zmodyfikowanego obrazu jako odpowiedź HTTP
        return send_file(output, mimetype=f'image/{image.format.lower()}')

    except Exception as e:
        return jsonify({"error": str(e)}), 500
