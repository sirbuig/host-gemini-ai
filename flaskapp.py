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


prompt_external_links = """
    You are a teacher preparing questions for a quiz. Given the following document, please generate 10 multiple-choice questions (MCQs) with 4 options and a corresponding
answer letter based on the document. Make the questions such that the answers aren't the same letter for every question. Make at least 3 questions multiple choice.
Make questions with longer answers, that does not include names.
Example question, use only the structure below to give the response:
Question: question here
CHOICE_A: choice here
CHOICE_B: choice here
CHOICE_C: choice here
CHOICE_D: choice here
Answer: A or B or C or D (only one answer)
Make sure to always have 4 choices and only one answer!
Make sure to also begin your answer with Question 1 immediately after the prompt.
Make sure to have a normal distribution of answers. (For example if you have 10 questions, don't have all the answers be A)
After generating the questions, please provide a list of external links that the user can use to learn more about the topic in this format:
External Links: [link1, link2, link3, etc.]
"""

app = Flask(__name__)
swagger = Swagger(app, template_file='swagger_config.yaml')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}  # Allowed file extension

@app.route('/', methods =['GET'])
def index():
  return "Hello, this is the API for FMInatorul"

@app.route('/generate-quiz-external-links', methods =['POST'])
def generate_QA_external():
    
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
                ],
                "external-links":["examplelink.com", "examplelink2.com", "etc.com"]
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
                  
                response = make_quiz(file, prompt_external_links)
                print(response)
                return jsonify(parse_quiz_text_external_links(response)), 200
          else:
              return jsonify({'error': 'Invalid file type (only PDFs allowed)'}), 400
          
    return jsonify({'error': 'Invalid request method'}), 400
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
  
def make_quiz(pdf_bytes, prompt):
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
        

def parse_quiz_text_external_links(text):
    """
    Parses quiz text into a JSON object with questions and external links.
    Returns a dictionary representing the quiz structure.
    """
    quiz_data = {"questions": [], "external-links": []}

    # Find the starting point for questions
    startIndex = text.lower().find("question 1")
    if startIndex != -1:
        text = text[startIndex:]
    else:
        return {"error": "No questions found in text."}
    
    # Split text into blocks for each question
    question_blocks = re.split(r"(?:\*\*)?Question \d+:(?:\*\*)?", text)

    for block in question_blocks:
        block = block.strip()
        if not block:  # Skip empty blocks
            continue

        lines = block.splitlines()
        question_text = None
        choices = {}
        answer = None

        for line in lines:
            line = line.strip()

            # Extract question (first line that is not a choice or answer)
            if not question_text and not line.startswith("CHOICE_") and not line.startswith("Answer:"):
                question_text = line
                continue

            # Extract choices
            match = re.match(r"CHOICE_([A-Z]):\s*(.*)", line)
            if match:
                choice_letter = match.group(1)
                choice_text = match.group(2).strip()
                choices[choice_letter] = choice_text
                continue

            # Extract answer
            if line.startswith("Answer:"):
                answer = line.split(":", 1)[1].strip()

        # Add the question to the quiz data
        if question_text and choices and answer:
            question_data = {
                "question": question_text,
                "choices": {**choices},  # Ensure all choices are captured
                "answer": answer,
            }
            quiz_data["questions"].append(question_data)

    external_links_section_start = text.lower().find("external links")
    if external_links_section_start != -1:
        # Extract the part after "external links"
        links_text = text[external_links_section_start:]
        
        # Use a regex to extract the content inside the brackets
        match = re.search(r"External Links:\s*\[(.*?)\]", links_text, re.IGNORECASE)
        if match:
            links_string = match.group(1)  # Extract the string inside the brackets
            links = links_string.split(",")  # Split the links by commas
            quiz_data["external-links"] = [link.strip() for link in links]  # Strip whitespace and add to JSON

    return quiz_data
    
   
# main driver function
if __name__ == '__main__':
	app.run(host='0.0.0.0',port='8888')
