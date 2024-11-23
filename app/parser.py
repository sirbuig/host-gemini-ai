import re

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
    
def parse_quiz_text_split_chapters(text):
    """
    Parses quiz text into a JSON object with chapters containing questions.
    Returns a dictionary representing the quiz structure.
    """
    quiz_data = {"chapters": [], "external-links": []}

    # Split the text into sections by chapters
    chapter_blocks = re.split(r"\nChapter:\s*", text.strip())

    for block in chapter_blocks:
        lines = block.splitlines()

        if len(lines) == 0:
            continue

        # Extract chapter name (first line if not the first block)
        chapter_name = lines[0].strip()
        
        # Initialize chapter data
        chapter_data = {"chapter": chapter_name, "questions": []}

        # Parse the questions in the block
        question_blocks = re.split(r"\n\n", "\n".join(lines[1:]))
        for question_block in question_blocks:
            question_lines = question_block.strip().splitlines()
            if not question_lines:
                continue

            # Extract question text
            question_match = re.match(r"Question: (.+)", question_lines[0])
            if not question_match:
                continue
            question_text = question_match.group(1).strip()

            # Extract choices
            choices = {}
            for choice_line in question_lines[1:5]:  # Process 4 choice lines
                choice_match = re.match(r"CHOICE_([A-D]): (.+)", choice_line.strip())
                if choice_match:
                    choice_letter = choice_match.group(1)
                    choice_text = choice_match.group(2).strip()
                    choices[choice_letter] = choice_text

            # Extract answer
            answer_match = None
            for line in question_lines:
                if line.startswith("Answer:"):
                    answer_match = line.split(":")[1].strip()
                    break

            if not answer_match:
                answer_match = None

            # Add question to the chapter
            chapter_data["questions"].append({
                "question": question_text,
                "choices": choices,
                "answer": answer_match,
            })

        # Add the chapter to the quiz data
        quiz_data["chapters"].append(chapter_data)

    # Extract external links at the end of the response
    external_links_match = re.search(r"External Links: \[(.+)\]", text)
    if external_links_match:
        links = external_links_match.group(1).split(",")
        quiz_data["external-links"] = [link.strip() for link in links]

    return quiz_data
