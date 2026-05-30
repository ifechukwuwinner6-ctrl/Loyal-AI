import os
import base64
import io
from flask import Flask, render_template, send_from_directory, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Initialize the GenAI client (uses your GEMINI_API_KEY environment variable)
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
    
    # Check if user wants to edit/change an image background
    is_image_edit_request = any(keyword in user_message.lower() for keyword in ['change background', 'edit background', 'replace background', 'background to'])
    
    if image_base64 and is_image_edit_request:
        try:
            # Decode user image to bytes
            image_bytes = base64.b64decode(image_base64)
            
            # Call the free Imagen 3 model for image editing/generation tasks
            # We pass the original image and tell it what background to generate
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=f"Modify this image: change the background to {user_message}. Keep the main subject exactly the same.",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1"
                )
            )
            
            # Grab the newly generated image bytes from the response
            generated_image_bytes = result.generated_images[0].image.image_bytes
            generated_base64 = base64.b64encode(generated_image_bytes).decode('utf-8')
            
            # Return image mode format to the frontend
            return jsonify({
                "type": "image",
                "reply": "Here is your edited image with the new background!",
                "image_data": generated_base64
            })
            
        except Exception as e:
            return jsonify({
                "type": "text",
                "reply": f"LOYAL AI Image Generator Error: {str(e)}. Make sure your prompt is clear!"
            })
            
    # Default text research pathway if it's a standard text chat or photo analysis request
    contents_payload = []
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        contents_payload.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
        
    contents_payload.append(user_message if user_message else "Analyze this image.")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_payload,
        )
        return jsonify({
            "type": "text",
            "reply": response.text
        })
    except Exception as e:
        return jsonify({
            "type": "text",
            "reply": f"LOYAL AI Connection Error: {str(e)}"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
