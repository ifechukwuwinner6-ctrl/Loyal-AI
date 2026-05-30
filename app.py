import os
import base64
from flask import Flask, render_template, send_from_directory, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

client = genai.Client()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get('message', '').strip()
    image_base64 = user_data.get('image_data')
    image_mime = user_data.get('image_mime', 'image/jpeg')
    
    # Build content list dynamically
    contents_payload = []
    
    # If the user uploaded an image file via the plus button, decode and attach it
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        contents_payload.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=image_mime,
            )
        )
    
    # Always append the user's text description or request
    contents_payload.append(user_message)
    
    try:
        # Pass both image part and text part together seamlessly
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_payload,
        )
        reply = response.text
    except Exception as e:
        reply = f"LOYAL AI Vision Error: Make sure your configuration parameters are correct. Details: {str(e)}"

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
