import os
import base64
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

client = genai.Client()

# System rule to make LOYAL AI talk and behave exactly like ChatGPT
CHATGPT_STYLE_PROMPT = (
    "You are LOYAL AI, an advanced, highly conversational AI assistant. "
    "Your responses must be beautifully formatted, extremely clear, direct, and helpful. "
    "Crucial Rule: At the very end of every single response, you must ask the user a natural, "
    "engaging follow-up question related to what they just asked, prompting them to continue the conversation."
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get('message', '').strip()
    image_base64 = user_data.get('image_data')
    image_mime = user_data.get('image_mime', 'image/jpeg')
    
    is_image_edit_request = any(keyword in user_message.lower() for keyword in ['change background', 'edit background', 'replace background', 'background to'])
    
    if image_base64 and is_image_edit_request:
        try:
            image_bytes = base64.b64decode(image_base64)
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=f"Modify this image: change the background to {user_message}. Keep the main subject exactly the same.",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1"
                )
            )
            generated_image_bytes = result.generated_images[0].image.image_bytes
            generated_base64 = base64.b64encode(generated_image_bytes).decode('utf-8')
            
            return jsonify({
                "type": "image",
                "reply": "Here is your edited image with the new background! What do you think of this variation?",
                "image_data": generated_base64
            })
        except Exception as e:
            return jsonify({
                "type": "text",
                "reply": f"LOYAL AI Image Generator Error: {str(e)}."
            })
            
    # Standard text/photo processing pipeline
    contents_payload = []
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        contents_payload.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
        
    contents_payload.append(user_message if user_message else "Analyze this image.")
    
    try:
        # Applying the ChatGPT behavioral style rules using GenerateContentConfig
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents_payload,
            config=types.GenerateContentConfig(
                system_instruction=CHATGPT_STYLE_PROMPT
            )
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
