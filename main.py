"""
LIBRARIES
"""

import base64
import vertexai

import IPython.display
from IPython.core.interactiveshell import InteractiveShell

InteractiveShell.ast_node_interactivity = "all"
import vertexai.preview.generative_models as generative_models

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


MODEL_ID = "gemini-1.5-pro-preview-0409"
model = GenerativeModel(MODEL_ID)

# model with system instructions
teaching_model = GenerativeModel(
    MODEL_ID,
    system_instruction=[
        "You are helping in processing large documents.",
        "Your mission is to create flashcards from the given materials.",
        "Your purpose is to create flashcards in triviador style.",
    ],
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

# let's try PDF document analysis
pdf_file_uri = "gs://mds-project/Curs 02.pdf"

prompt = """
    You are a very professional document summarization specialist.
    Please create flashcards of the given document in Triviador style.
"""

pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
contents = [pdf_file, prompt]

response = model.generate_content(contents)
print(response.text)
