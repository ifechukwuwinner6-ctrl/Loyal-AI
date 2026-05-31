import os
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(name)

# Initialize the GenAI client using your GEMINI_API_KEY environment variable
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
    
    # 1. DYNAMIC DATE FIX: Grab the exact live date from the server
    current_date_str = datetime.now().strftime("%B %d, %Y")
    
    # 2. CHATGPT BEHAVIORAL STYLE SYSTEM PROMPT
    CHATGPT_STYLE_PROMPT = (
        "You are LOYAL AI, an advanced, highly conversational AI assistant built by Ifechukwu Winner. "
        f"Today's current date is explicitly {current_date_str}. Always use this date if asked about time. "
        "Your responses must be beautifully formatted with clean spacing, clear, direct, and helpful. "
        "Crucial Rule: At the very end of every single response, you must ask the user a natural, "
        "engaging follow-up question related to what they just asked, prompting them to continue the conversation exactly like ChatGPT does."
    )
    
    # Check if the user is asking to modify an image background
    is_image_edit_request = any(keyword in user_message.lower() for keyword in ['change background', 'edit background', 'replace background', 'background to', 'plane black'])
    
    if image_base64 and is_image_edit_request:
        try:
            image_bytes = base64.b64decode(image_base64)
            
            # FIXED IMAGE MODEL: Using the correct capability model name for free tiers
            result = client.models.generate_images(
                model='imagen-3.0-capability-003',
                prompt=f"Modify this image: change the background to {user_message}. Keep the person or main subject completely unchanged.",
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
                "reply": "I have updated the background of your photo! How does this look? Would you like me to adjust anything else?",
                "image_data": generated_base64
            })
        except Exception as e:
            # Clean error handler for quota or connection updates
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return jsonify({"type": "text", "reply": "⚡ Free Tier Speed Limit: You've sent requests a bit too fast! Please pause for about 30 seconds and try again, I'll be completely ready."})
            return jsonify({"type": "text", "reply": "I ran into a temporary issue modifying that image background. Let's try adjusting the prompt text slightly!"})
            
    # Standard text research or photo analysis pathway
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
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return jsonify({"type": "text", "reply": "⚡ Free Tier Speed Limit: You've sent requests a bit too fast! Please pause for about 30 seconds and try again, I'll be completely ready."})
        return jsonify({
            "type": "text",
            "reply": f"LOYAL AI Engine Notification: {error_msg}"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
