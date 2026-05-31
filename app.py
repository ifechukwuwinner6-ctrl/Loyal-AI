import os
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from google.genai.errors import APIError

app = Flask(__name__)

# Initialize the Google GenAI client
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

    # Dynamic time and date handling
    current_time_str = datetime.now().strftime("%I:%M %p")
    current_date_str = datetime.now().strftime("%B %d, %Y")

    # The Core Identity & Brain System Instructions
    CHATGPT_STYLE_PROMPT = (
        "You are LOYAL AI, an advanced, highly conversational AI assistant built by Ifechukwu Winner. "
        f"Today's current date is explicitly {current_date_str}. Always use this date if asked. "
        "Your responses must be beautifully formatted with clean spacing, clear, direct, and engaging. "
        "Crucial Rule: At the very end of every single response, you must ask the user a natural, "
        "engaging follow-up question related to what they just asked, prompting them to continue the conversation."
    )

    msg_lower = user_message.lower()
    
    # --- SMART INTENT DETECTION ---
    # Smart check for brand new image creation requests
    is_create_request = any(phrase in msg_lower for phrase in [
        'create a picture', 'generate a picture', 'draw me', 'generate an image', 
        'create an image', 'make a picture', 'draw a picture', 'generate a photo'
    ])
    
    # Smart check for uploaded image modification requests
    is_edit_request = image_base64 is not None and any(word in msg_lower for word in [
        'background', 'darken', 'change', 'modify', 'replace', 'design', 'fix', 
        'look like', 'edit', 'add', 'remove', 'make the', 'turn this'
    ])

    # --- ULTRASMART IMAGE GENERATION PIPELINE ---
    if is_create_request or is_edit_request:
        try:
            # Crafting context-aware prompts depending on whether an image was sent
            if is_edit_request:
                prompt_instructions = (
                    f"Modify the provided image concept based on this user instruction: '{user_message}'. "
                    "Ensure the visual theme matches perfectly while maintaining the primary context elements."
                )
            else:
                prompt_instructions = f"A professional, high-quality rendering of: {user_message}. Clean composition, crisp details."

            # Crucial Fix: Swapped out 'imagen-3.0-capability-003' (404) with production 'imagen-3.0-generate-002'
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt_instructions,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1"
                )
            )
            
            # Extract the raw binary image data and convert it back to Base64 safely
            generated_image_bytes = result.generated_images[0].image.image_bytes
            generated_base64 = base64.b64encode(generated_image_bytes).decode('utf-8')
            
            return jsonify({
                "type": "image",
                "reply": f"🎨 Processed successfully at {current_time_str}! Here is your custom generation:",
                "image_data": generated_base64
            })
            
        except APIError as e:
            # Smart handler for free tier rate limits (Status Code 429/420)
            if e.code in [420, 429]:
                return jsonify({
                    "type": "text", 
                    "reply": "⏳ LOYAL AI is resting: The free tier image generation capacity is temporarily maxed out. Let's give it 60 seconds and try again!"
                })
            return jsonify({
                "type": "text", 
                "reply": f"🔧 API Model Error Link ({e.code}). Let's verify our credentials or try another query!"
            })
        except Exception as ex:
            return jsonify({
                "type": "text", 
                "reply": "I ran into a structural canvas issue compiling the pixels. Could you describe your image request differently?"
            })

    # --- TEXT CONVERSATION & COMPUTER VISION PIPELINE ---
    contents_payload = []
    
    # If a picture is attached but the user is ASKING about it instead of trying to EDIT it
    if image_base64:
        image_bytes = base64.b64decode(image_base64)
        contents_payload.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
    
    # Fallback to standard request text if input bar is sent empty with a picture
    contents_payload.append(user_message if user_message else "Analyze the details of this image comprehensively.")

    try:
        # Utilizing ultra-fast multimodal Flash engine for chat and image interpretation
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
                "reply": "⏱️ Speed Limit: Chat data requests are moving a bit too fast for the free server. Give me just a few seconds to breathe!"
            })
        return jsonify({"type": "text", "reply": f"LOYAL AI Routing Error ({e.code}): Request could not be resolved."})
    except Exception:
        return jsonify({"type": "text", "reply": "An unexpected server pipeline disconnect occurred. Let's send that message again!"})

if __name__ == '__main__':
    # Binds to the required dynamic port environment variable provided by Render
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
