from flask import Flask, jsonify, request, render_template_string, redirect, session, render_template, send_from_directory, Blueprint, current_app
from flask_jwt_extended import jwt_required, create_access_token, verify_jwt_in_request
import flasgger
from flasgger.utils import swag_from
import os
from datetime import timedelta
import yaml
# connect with other files
from .gcloud_utils import make_quiz, prompt_external_links
from .parser import parse_quiz_text_external_links, parse_quiz_text_split_chapters
from .auth import auth, authenticate_request, CREDENTIALS


bp = Blueprint("routes", __name__)

def register_routes(app):
    app.register_blueprint(bp)
# end setup for connection

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}  # Allowed file extension

flasgger_static_path = os.path.join(os.path.dirname(flasgger.__file__), 'ui3/static')
current_path = os.path.dirname(__file__)

@bp.before_request
def authenticate():
    auth_error = authenticate_request()
    if auth_error:
        return auth_error  # Return error if authentication fails
    
@bp.route('/flasgger_static/<path:filename>')
def flasgger_static(filename):
    return send_from_directory(flasgger_static_path, filename)

@bp.route('/admin/login')
@auth.login_required
def admin_login():
    # Log in the admin
    session['admin_logged_in'] = True
    # Generate a JWT token and store it in the session
    expires = timedelta(days=1000)
    access_token = create_access_token(identity=auth.current_user(), expires_delta=expires)
    session['jwt_token'] = access_token
    # Redirect to Swagger UI
    return redirect('/apidocs')

@bp.route('/login', methods=['POST'])
@swag_from(current_path + '/swagger_docs/login.yaml', methods=['POST'])
def api_login():
    data = request.json  # Read JSON body
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Username and password are required"}), 400

    username = data['username']
    password = data['password']

    # Authenticate user
    if username in CREDENTIALS and CREDENTIALS[username] == password:
        expires = timedelta(days=1)
        access_token = create_access_token(identity=username, expires_delta=expires)
        return jsonify({"token": access_token})
    return jsonify({"message": "Invalid credentials"}), 401
     
@bp.route('/', methods=['GET'])
def index():
    return render_template('home.html')

@bp.route('/api/generate-quiz-external-links', methods =['POST'])
@swag_from(current_path + '/swagger_docs/generate_quiz_external_links.yaml', methods=['POST'])
def generate_QA_external():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded!'}), 400  # Return JSON with error message

    file = request.files['file']
    
    # Validate the uploaded file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400  # Return JSON with error message
    
    if file and allowed_file(file.filename):
        # Read the entire file in memory            
        response = make_quiz(file, prompt_external_links)
        return jsonify(parse_quiz_text_external_links(response)), 200
    else:
        return jsonify({'error': 'Invalid file type (only PDFs allowed)'}), 400     


    # let's try PDF document analysis

@bp.route('/api/generate-quiz-split-chapters', methods =['POST'])
@swag_from(current_path + '/swagger_docs/generate_quiz_split_chapters.yaml', methods=['POST'])
def generate_QA_split_chapters():
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded!'}), 400

        file = request.files['file']

        # Validate the uploaded file
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            # Retrieve the number of questions from the query parameters
            num_questions = request.args.get('num_questions', default=10, type=int)

            # Generate a dynamic prompt with the specified number of questions
            prompt_split_chapters = f"""
            You are a teacher preparing questions for a quiz. Given the following document, please generate {num_questions} multiple-choice questions (MCQs) with 4 options and a corresponding
            answer letter based on the document. Make the questions such that the answers aren't the same letter for every question.
            Make questions with longer answers, that does not include names. I want you to also use your best judgement to split the questions into chapters. At least 2 questions per chapter.
            As to the number of the chapters, use your best judgement. For a larger document, you can split the questions into more chapters.
            Example question, use only the structure below to give the response:
            Chapter: Name of chapter here
            Question: question here
            CHOICE_A: choice here
            CHOICE_B: choice here
            CHOICE_C: choice here
            CHOICE_D: choice here
            Answer: A or B or C or D (only one answer)
            Make sure to always have 4 choices and only one answer!
            Make sure to also begin your answer with Chapter immediately after the prompt.
            Make sure to have a normal distribution of answers. (For example if you have {num_questions} questions, don't have all the answers be A)
            After generating the questions, please provide a list of external links that the user can use to learn more about the topic in this format:
            External Links: [link1, link2, link3, etc.]
            """

            # Process the file and generate questions using the dynamic prompt
            response = make_quiz(file, prompt_split_chapters)

            # Parse the response into chapters and questions
            parsed_data = parse_quiz_text_split_chapters(response)
            return jsonify(parsed_data), 200
        else:
            return jsonify({'error': 'Invalid file type (only PDFs allowed)'}), 400
    except Exception as e:
        return jsonify({'error': f'Authentification error:: {str(e)}'}), 401


@bp.route('/apispec_1.json')
def swagger_spec():
    swagger_docs_path = os.path.join(os.path.dirname(__file__), 'swagger_docs')
    return send_from_directory(swagger_docs_path, 'swagger_config.yaml')

@bp.route('/apidocs')
def swagger_ui():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('swagger-ui.html',
                           title='PDF Quiz Generator API',
                           specs_url='/apispec_1.json',
                           jwt_token=session.get('jwt_token'),
                           css=[
                               '/flasgger_static/swagger-ui.css',
                           ],
                           js=[
                               '/flasgger_static/swagger-ui-bundle.js',
                               '/flasgger_static/swagger-ui-standalone-preset.js'
                           ])
