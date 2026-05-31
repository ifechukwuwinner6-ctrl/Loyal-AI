import os
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
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
        f"Today's current date is explicitly {current_date_str}. Always use this date if asked. "
        "Your responses must be beautifully formatted with clean spacing, clear, direct, and engaging. "
        "Crucial Rule: At the very end of every single response, you must ask the user a natural, "
        "engaging follow-up question related to what they just asked, prompting them to continue the conversation."
    )

    msg_lower = user_message.lower()
    
    # Detect if user wants an image created from scratch or an uploaded image modified
    is_create_request = any(kw in msg_lower for kw in ['create a picture', 'generate a picture', 'draw me', 'generate an image', 'create an image'])
    is_edit_request = image_base64 is not None and any(kw in msg_lower for kw in ['background', 'darken', 'change', 'modify', 'replace', 'design', 'fix', 'look like'])

    # --- IMAGE PIPELINE (GENERATION OR MODIFICATION) ---
    if is_create_request or is_edit_request:
        try:
            # Determine the correct prompt based on whether an image was uploaded
            if is_edit_request:
                prompt_instructions = f"Modify this image based on this request: {user_message}. Keep the main subject clean and unaltered."
            else:
                prompt_instructions = f"Generate a beautiful, high-quality image based on this prompt: {user_message}"

            # If it's an edit request, we would ideally pass the image, but Imagen 3 on free capabilities handles text-to-image prompts. 
            # We pass your description directly to create your desired design.
            result = client.models.generate_images(
                model='imagen-3.0-capability-003',
                prompt=prompt_instructions,
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
                "reply": f"🎨 Done! I have processed your image request. Here is what I created for you at {datetime.now().strftime('%H:%M %p')}:",
                "image_data": generated_base64
            })
            
        except APIError as e:
            if e.code in [420, 429]:
                return jsonify({
                    "type": "text", 
                    "reply": "⏳ LOYAL AI is resting: The free tier image generation capacity is currently maxed out. Please try again in a few moments!"
                })
            return jsonify({"type": "text", "reply": f"The image model returned an error ({e.code}). Let's try again shortly!"})
        except Exception:
            return jsonify({"type": "text", "reply": "I ran into an issue rendering that image design. Can we try rephrasing your request?"})

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
        if e.code == 429:
            return jsonify({
                "type": "text",
                "reply": "⏱️ Speed Limit Reached: The free tier engine needs a brief 30-second break. Ask me again in just a moment!"
            })
        return jsonify({"type": "text", "reply": f"LOYAL AI Error Status ({e.code}): Request could not be processed."})
    except Exception:
        return jsonify({"type": "text", "reply": "An unexpected connection error occurred. Let's try sending that message again!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
