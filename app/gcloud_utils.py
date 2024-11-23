from google.cloud import storage
from PyPDF2 import PdfReader 
import uuid
from IPython.core.interactiveshell import InteractiveShell
import os
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)

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
      name = f"{uuid.uuid4()}.pdf"
      pdf_bytes = pdf_bytes.read()
      # reader = PdfReader(pdf_bytes)
      BUCKET_NAME = "unchiipecos"
      DESTINATION_BLOB_NAME = name
      
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
        delete_from_gcs(BUCKET_NAME, DESTINATION_BLOB_NAME)
        print(f"Unexpected error in make_quiz: {e}")
        return e  # Return the raw exception
        