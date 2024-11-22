from flask import Flask, jsonify, request
from PyPDF2 import PdfReader  # Example using PyPDF2 library
import re
from google.cloud import storage
from flasgger import Swagger


import os
"""
LIBRARIES
"""

# import base64
# import vertexai

# import IPython.display
from IPython.core.interactiveshell import InteractiveShell

# InteractiveShell.ast_node_interactivity = "all"
# import vertexai.preview.generative_models as generative_models

from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)
"""
#####################################
"""


MODEL_ID = "gemini-1.5-flash-002"
model = GenerativeModel(MODEL_ID)

# model with system instructions
teaching_model = GenerativeModel(
    MODEL_ID,
)

# model parameters
generation_config = GenerationConfig(
    temperature=1,
    top_p=1.0,
    top_k=32,
    candidate_count=1,
    max_output_tokens=8192,
)

# safety settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
}


prompt = """
    You are a teacher preparing questions for a quiz. Given the following document, please generate 10 multiple-choice questions (MCQs) with 4 options and a corresponding
answer letter based on the document. Make the questions such that the answers aren't the same letter for every question. Make at least 3 questions multiple choice.
Make questions with longer answers, that does not include names.
Example question, use only the structure below to give the response:
Question: question here
CHOICE_A: choice here
CHOICE_B: choice here
CHOICE_C: choice here
CHOICE_D: choice here
Answer: A or B or C or D or combined (if it is multiple choice)
"""


app = Flask(__name__)
swagger = Swagger(app, template_file='swagger_config.yaml')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}  # Allowed file extension

@app.route('/', methods =['GET','POST'])
def generate_QA():
  
  """
    Generate Questions and Answers from a PDF.
    ---
    tags:
      - PDF Processing
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: The PDF file to process.
    responses:
      200:
        description: Successfully processed the PDF.
        examples:
          application/json: 
            {
              "questions": [
                {
                  "question": "Example Question",
                  "choices": {
                    "A": "Choice A",
                    "B": "Choice B",
                    "C": "Choice C",
                    "D": "Choice D"
                  },
                  "answer": "A"
                }
              ]
            }
      400:
        description: Invalid request or error processing the file.
  """

  if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded!'}), 400  # Return JSON with error message

        file = request.files['file']
        
        # Validate the uploaded file
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400  # Return JSON with error message
        
        if file and allowed_file(file.filename):
            # Read the entire file in memory
            
            # Process the PDF bytes (e.g., use PyPDF2 or other libraries)
            #response = process_pdf(file)  # Replace with your processing function
                
              response = make_quiz(file)
              return jsonify(parse_quiz_text(response)), 200
        else:
            return jsonify({'error': 'Invalid file type (only PDFs allowed)'}), 400
        
  return "Hello, this is the API for FMInatorul"     
	# let's try PDF document analysis


# Function to process the uploaded PDF (replace with your actual logic)
def process_pdf(pdf_bytes):
    try:
      reader = PdfReader(pdf_bytes)
      num_pages = len(reader.pages)
      response = f"Processing PDF: {num_pages} pages (in-memory)" # Placeholder for processing
      return response
    except Exception as e:
        return e
    

def upload_to_gcs(bucket_name, pdf_bytes, destination_blob_name):
    # Initialize the Google Cloud Storage client with the credentials
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(pdf_bytes, content_type="application/pdf")
    

def delete_from_gcs(bucket_name, blob_name):
    """Deletes a blob from the specified bucket in GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
  
def make_quiz(pdf_bytes):
    try:
      name = pdf_bytes.filename
      pdf_bytes = pdf_bytes.read()
      # reader = PdfReader(pdf_bytes)
      BUCKET_NAME = "unchiipecos"
      DESTINATION_BLOB_NAME = name
      current_dir = os.path.dirname(os.path.abspath(__file__))
      
      upload_to_gcs(BUCKET_NAME, pdf_bytes, DESTINATION_BLOB_NAME)
      pdf_file_uri = "gs://unchiipecos/" + name

      pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
      contents = [pdf_file, prompt]

      response = model.generate_content(contents)
      delete_from_gcs(BUCKET_NAME, DESTINATION_BLOB_NAME)

      return response.text
    
    except FileNotFoundError as e:
        print(f"FileNotFoundError in make_quiz: {e}")
        return str(e)  # Return the error message as a string
    except Exception as e:
        print(f"Unexpected error in make_quiz: {e}")
        return e  # Return the raw exception
        
def parse_quiz_text(text):
  """
  Parses quiz text into a JSON object.
  Returns a dictionary representing the quiz structure.
  """
  quiz_data = {"questions": []}

  # Split text by empty lines to separate questions and answer sections
  question_answer_blocks = text.strip().split("\n\n")

  for block in question_answer_blocks:
    lines = block.splitlines()  # Split block into lines

    # Extract question text (first line)
    question_text = lines[0]

    current_question_data = {"question": question_text.strip(), "choices": {}, "answer": None}

    # Capture choices (assuming first 4 lines after question are choices)
    for choice_line in lines[1:5]:  # Process first 4 lines after question
      choice_match = re.match(r"CHOICE_([A-Z]): (.*?)$", choice_line)
      if choice_match:
        choice_letter = choice_match.group(1)
        choice_text = choice_match.group(2).strip()
        current_question_data["choices"][choice_letter] = choice_text

    # Extract answer (assuming answer line starts with "Answer:")
    answer_line = None
    for line in lines:
      if line.lower().startswith("answer:"):  # Check for answer line (case-insensitive)
        answer_line = line.strip()
        break  # Stop processing lines after finding answer line

    # Process answer line if found
    if answer_line:
      answer = answer_line.split(":")[1].strip()  # Extract answer after colon
      if "," in answer:  # Check for multiple answer format (comma-separated)
        answer = answer.split(",")
      current_question_data["answer"] = answer

    quiz_data["questions"].append(current_question_data)

  return quiz_data
   
# main driver function
if __name__ == '__main__':
	app.run(host='0.0.0.0',port='8888')
