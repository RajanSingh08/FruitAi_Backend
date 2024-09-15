# //fruit.ai backend

from flask import Flask, request, jsonify, abort
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from googletrans import Translator
app = Flask(__name__)
translator = Translator()
CORS(app)

app.config["MONGO_URI"] = "mongodb+srv://rajansingh2003rs:pr8KgaXLnFhItpC3@cluster0.7lxly.mongodb.net/<dbname>?retryWrites=true&w=majority"
mongo = PyMongo(app)


try:
    mongo.db.command("ping")
    print("Connected to MongoDB successfully!")
except ConnectionFailure:
    print("Failed to connect to MongoDB")

faqs_collection = mongo.db.faqs

cloudinary.config( 
    cloud_name = "dvxerazfh", 
    api_key = "298156755513339", 
    api_secret = "2jR2Nts2La0FZMubkin4GEVHgyM",  
   
)
optimize_url, _ = cloudinary_url("shoes", fetch_format="auto", quality="auto")
print(optimize_url)

# Transform the image: auto-crop to square aspect_ratio
auto_crop_url, _ = cloudinary_url("shoes", width=500, height=500, crop="auto", gravity="auto")
print(auto_crop_url)
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/faqs', methods=['GET'])
def get_faqs():
    faqs = faqs_collection.find()
    faq_list = []
    for faq in faqs:
        faq_list.append({
            'id': str(faq['_id']),
            'question': faq['question'],
            'answer': faq['answer'],
            'image_url': faq.get('image_url', None)  # Include image_url if it exists
        })
    return jsonify(faq_list), 200
@app.route('/faqs/<id>', methods=['GET'])
def get_faq(id):
    try:
        faq = faqs_collection.find_one({'_id': ObjectId(id)})
        if not faq:
            abort(404)
        return jsonify({
            'id': str(faq['_id']),
            'question': faq['question'],
            'answer': faq['answer'],
            'image_url': faq.get('image_url', None)  # Include image URL if it exists
        })
    except:
        abort(400, description="Invalid FAQ ID format")

@app.route('/faqs', methods=['POST'])
def create_faq():
    if 'question' not in request.form or 'answer' not in request.form:
        abort(400, description="Missing 'question' or 'answer' field")
    
    question = request.form['question']
    answer = request.form['answer']

    image_url = None
    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get('secure_url')

    new_faq = {'question': question, 'answer': answer, 'image_url': image_url}
    
    result = faqs_collection.insert_one(new_faq)
    
    return jsonify({
        'id': str(result.inserted_id), 
        'question': question, 
        'answer': answer,
        'image_url': image_url
    }), 201


@app.route('/faqs/<id>', methods=['PUT'])
def update_faq(id):
    try:
        faq = faqs_collection.find_one({'_id': ObjectId(id)})
        if not faq:
            abort(404)

        if not request.json:
            abort(400, description="Invalid request body")
        
        question = request.json.get('question', faq['question'])
        answer = request.json.get('answer', faq['answer'])

        faqs_collection.update_one({'_id': ObjectId(id)}, {"$set": {'question': question, 'answer': answer}})
        
        return jsonify({'id': str(faq['_id']), 'question': question, 'answer': answer})
    except:
        abort(400, description="Invalid FAQ ID format")

@app.route('/faqs/<id>', methods=['DELETE'])
def delete_faq(id):
    try:
        faq = faqs_collection.find_one({'_id': ObjectId(id)})
        if not faq:
            abort(404)

        faqs_collection.delete_one({'_id': ObjectId(id)})
        
        return jsonify({'message': 'FAQ deleted successfully'}), 200
    except:
        abort(400, description="Invalid FAQ ID format")
@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.json

    text = data.get('text')
    source_lang = data.get('source_lang')
    target_lang = data.get('target_lang')

    if not text:
        return jsonify({'error': 'No text provided'}), 400
    if not source_lang or not target_lang:
        return jsonify({'error': 'Invalid source or target language'}), 400

    try:
        translated = translator.translate(text, src=source_lang, dest=target_lang)

        if not translated or not hasattr(translated, 'text'):
            return jsonify({'error': 'Translation failed'}), 500

        return jsonify({'translated_text': translated.text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,port=8080)