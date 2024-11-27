import functions_framework
from google.cloud import storage
from flask import request, jsonify, send_file
from PIL import Image
from io import BytesIO

# Inicjalizacja klienta Cloud Storage
storage_client = storage.Client()

@functions_framework.http
def resize_image(request):
    try:
        # Sprawdź, czy metoda HTTP to POST
        if request.method != 'POST':
            return jsonify({"error": "Only POST requests are allowed"}), 405

        # Odbierz parametry z żądania
        data = request.get_json()
        bucket_name = data.get('bucket')  # Nazwa bucketa
        file_name = data.get('file_name')  # Nazwa pliku
        target_width = int(data.get('width'))  # Docelowa szerokość
        target_height = int(data.get('height'))  # Docelowa wysokość

        if not all([bucket_name, file_name, target_width, target_height]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Pobierz obraz z Firebase Storage
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
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
