"""
LIBRARIES
"""
# import base64
# import vertexai

# import IPython.display
from IPython.core.interactiveshell import InteractiveShell
import re
InteractiveShell.ast_node_interactivity = "all"
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
# let's try PDF document analysis
pdf_file_uri = "gs://unchiipecos/Curs_6-1.pdf"

# You are a very professional document summarization specialist.
# Please create flashcards of the given document in Triviador style.
prompt = """
    You are a teacher preparing questions for a quiz. Given the following document, please generate 10 multiple-choice questions (MCQs) with 4 options and a corresponding
answer letter based on the document. Make the questions such that the answers aren't the same letter for every question. Make at least 3 questions multiple choice.
Make questions with longer answers, that does not include names.
Example question, use only the structure below:
Question: question here
CHOICE_A: choice here
CHOICE_B: choice here
CHOICE_C: choice here
CHOICE_D: choice here
Answer: A or B or C or D or combined (if it is multiple choice)
"""

pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
contents = [pdf_file, prompt]

response = model.generate_content(contents)
print(response.text)
print("-------------------------------")
response = parse_quiz_text(response.text)
print(response)

