import os
import openai
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
# CORS(app, origins=["https://structai.netlify.app/"])
CORS(app, resources={r"/*": {"origins": "*"}})


# Set upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not set in environment variables.")

client = OpenAI(api_key=api_key)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']  # Only one file is expected
    if not file:
        return jsonify({'error': 'No selected file'}), 400

    # Prepare message for OpenAI API
    msg = {
        'role': 'user',
        'content': [
            {'type': 'text', 'text': (
            "Extract a take-off from the engineering drawing for all the sections. "
            "Return ONLY a JSON object with the key 'takeoff', containing an array of objects. "
            "Each object MUST have 'Description', 'Quantity', 'Length', 'Width', 'Height', 'Volume'. "
            "Example response format:\n"
            "{ \"takeoff\": [ { \"Description\": \"Steel Beam\", \"Quantity\": 10, \"Length\": \"5m\" } ] }"
        )}
        ]
    }

    # Check file extension and process it
    file_extension = file.filename.split('.')[-1].lower()

    if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf']:
        return jsonify({'error': 'Only .jpg, .jpeg, .png, .gif, or .webp files are supported'}), 400

    # Read image as base64
    encoded_img = base64.b64encode(file.read()).decode('utf-8')
    
    # Add image to the message
    msg['content'].append({
        'type': 'image_url',
        'image_url': {
            'url': f'data:image/jpeg;base64,{encoded_img}',
            'detail': 'low'
        }
    })

    try:
        # Send the message to OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo", 
            temperature=0.0, 
            max_tokens=4090,
            messages=[msg]
        )

        response_msg = response.choices[0].message.content.strip()
        # Send response
        return jsonify({'message': 'File processed successfully', 'response': response_msg}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
