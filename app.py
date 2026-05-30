import os
from datetime import datetime
from flask import Flask, render_template, send_from_directory, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# This endpoint handles the actual live message processing
@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get('message', '').strip().lower()
    
    # Real-time backend processing logic
    if 'date' in user_message or 'time' in user_message:
        now = datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        current_time = now.strftime("%I:%M %p")
        reply = f"Today's date is {current_date} and the current server time is {current_time}."
    elif 'hello' in user_message or 'hi' in user_message:
        reply = "Hello there! Your mobile app backend is fully linked up and communicating perfectly. What should we build into our core tool next?"
    else:
        reply = f"I received your message: '{user_data.get('message')}'. The live Python backend pipeline is working cleanly on Render!"

    return jsonify({"reply": reply})

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
