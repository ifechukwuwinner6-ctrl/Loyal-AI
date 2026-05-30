import os
from flask import Flask, render_template, send_from_directory, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize the free Google GenAI client
# It automatically reads your GEMINI_API_KEY environment variable on Render
client = genai.Client()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"reply": "Please enter a valid prompt."})
    
    try:
        # This sends your message to the AI engine to research and reply instantly
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
        )
        reply = response.text
    except Exception as e:
        # Fallback if your API key is missing or configured incorrectly
        reply = f"LOYAL AI Engine Connection Error: Make sure your GEMINI_API_KEY is added to your Render environment variables."

    return jsonify({"reply": reply})

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
