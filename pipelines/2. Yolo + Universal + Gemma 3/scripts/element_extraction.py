from unstructured.partition.pdf import partition_pdf
import markdownify
import re
import model_config as mc
from langchain.prompts import ChatPromptTemplate


# Function to extract elements from PDF
def element_extractor(pdf_path):
    # Partitioning file
    raw_pdf_elements = partition_pdf(
        filename=pdf_path,
        extract_images_in_pdf=True,
        infer_table_structure=True,
    )

    # split raw_pdf_elements per page_number
    element_pages = []

    for element in raw_pdf_elements:
        page_number = element.metadata.page_number
        if len(element_pages) < page_number:
            element_pages.append([])
        element_pages[page_number - 1].append(element)

    return element_pages

# Process the extracted string
def process_string(string):
    # lowercase the string
    string = string.lower()
    # remove punctuation
    string = re.sub(r'[^\w\s]', '', string)
    # remove extra whitespaces
    string = re.sub(r'\s+', '', string)
    return string

# Extract elements to text and replace figures with tables
def extract_elements_to_text(elements, figures):
    figures = figures.copy()
    string: list[str] = []

    for i, element in enumerate(elements):
        if "unstructured.documents.elements.Table" in str(type(element)):
            table = markdownify.markdownify(element.metadata.text_as_html)
            string.append(table)
        elif "unstructured.documents.elements.Image" in str(type(element)):
            name_dist = []
            # count the distance between the image and the figure
            for fig in figures:
                count = 0
                fig_name = fig['name']
                for j in range(i, len(elements)):
                    if process_string(fig_name) in process_string(str(elements[j])):
                        name_dist.append(count)
                        break
                    count += 1
            # get the closest figure
            if len(name_dist) > 0:
                min_dist = min(name_dist)
                if min_dist < 4:
                    fig = figures[name_dist.index(min_dist)]
                    string.append(fig["data"])
                    figures.remove(fig)
        else:
            string.append(markdownify.markdownify(str(element), heading_style="ATX"))

    if len(figures) > 0:
        for fig in figures:
            string.append(fig["name"])
            string.append(fig["data"])

    return "\n\n".join(string)

# Extract elements from PDF
def extract_elements(pdf_path, pages):
    # Extract elements from PDF
    elements = element_extractor(pdf_path)

    # Extract text from elements
    for i, page in enumerate(pages):
        page["text"] = extract_elements_to_text(elements[i], page["figures"])

    return pages

# Output formatting
def clean_md(result_text):
    md_text = result_text

    # check if the text contains ```markdown
    if "```markdown" not in md_text:
        return md_text

    # split the text by ```markdown
    md_text = md_text.split("```markdown")[1].strip()
    md_text = md_text.split("```")[0].strip()

    return md_text

# load llm model
model, tokenizer = mc.load_format_llm()

# Prompt template
SYSTEM_FORMAT_PROMPT = """You are a helpful assistant who helps users format the extracted data from a document page into Markdown format.
You are not allowed to change or summarize the given text; only correct any broken words and delete any unsuccessful OCR results, if any"""

FORMAT_PROMPT_TEMPLATE = """Transform this extracted text data from a page into Markdown format.
Look for the possible headings or stylings in the text and tailor it to resemble a page layout, preserve the original numbering and layout (it can be in the middle of the page).
Do not change or summarize the content; only correct any broken words and delete any unsuccessful OCR results, if any.

Extracted Text:
{extracted_text}
"""

def format_all_data(pages):
    formated_text = []

    for page in pages:
        
        extracted_text = page['text']

        prompt_template = ChatPromptTemplate.from_template(FORMAT_PROMPT_TEMPLATE)
        prompt = prompt_template.format(extracted_text=extracted_text)

        messages = [
            [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": SYSTEM_FORMAT_PROMPT},]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt},]
                },
            ],
        ]

        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt"
        ).to(model.device)

        input_len = inputs["input_ids"].shape[-1]

        generation = model.generate(**inputs, max_new_tokens=4096)
        generation = generation[0][input_len:]

        decoded = tokenizer.decode(generation, skip_special_tokens=True)
        formated_text.append(clean_md(decoded))

    return formated_text