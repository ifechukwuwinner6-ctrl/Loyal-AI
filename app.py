                import os
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
# Import the specific APIError to catch quota issues cleanly
from google.genai.errors import APIError

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
    
    current_date_str = datetime.now().strftime("%B %d, %Y")
    
    CHATGPT_STYLE_PROMPT = (
        "You are LOYAL AI, an advanced, highly conversational AI assistant built by Ifechukwu Winner. "
        f"Today's current date is explicitly {current_date_str}. Always use this date if asked about time. "
        "Your responses must be beautifully formatted with clean spacing, clear, direct, and helpful. "
        "Crucial Rule: At the very end of every single response, you must ask the user a natural, "
        "engaging follow-up question related to what they just asked, prompting them to continue the conversation."
    )
    
    is_image_edit_request = any(keyword in user_message.lower() for keyword in ['change background', 'edit background', 'replace background', 'background to', 'plane black'])
    
    # --- IMAGE MODIFICATION PIPELINE ---
    if image_base64 and is_image_edit_request:
        try:
            image_bytes = base64.b64decode(image_base64)
            result = client.models.generate_images(
                model='imagen-3.0-capability-003',
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
                "reply": "I've updated the background for you! How does it look? What adjustments would you like next?",
                "image_data": generated_base64
            })
        except APIError as e:
            if e.code == 429:
                return jsonify({"type": "text", "reply": "⏱️ LOYAL AI is resting: The free tier speed limit was reached. Please wait a short moment and try your request again!"})
            return jsonify({"type": "text", "reply": "The image model is currently unavailable on the free tier. Let's try a text question instead!"})
        except Exception:
            return jsonify({"type": "text", "reply": "I couldn't complete the image edit. Let's try rephrasing your prompt text!"})
            
    # --- TEXT & ANALYSIS PIPELINE ---
    contents_payload = []
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        contents_payload.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
        
    contents_payload.append(user_message if user_message else "Analyze this image.")
    
    try:
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
    except APIError as e:
        # Intercepting specific status codes cleanly
        if e.code == 429:
            return jsonify({
                "type": "text", 
                "reply": "⏱️ Speed Limit Reached: Conversations are moving a bit fast for the free tier! Give it about 30 seconds to refresh, and ask me again. What topic should we explore next?"
            })
        return jsonify({"type": "text", "reply": f"LOYAL AI Error Status ({e.code}): Request could not be processed."})
    except Exception as e:
        return jsonify({"type": "text", "reply": "An unexpected connection error occurred. Let's try again!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
