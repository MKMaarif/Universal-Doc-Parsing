import os
import json
print("Pipeline 2 started!")

import scripts.model_config as mc
print("Model config imported")
import scripts.file_handler as fh
print("File handler imported")
import scripts.image_extraction as ie
print("Image extraction imported")
import scripts.element_extraction as ee
print("Element extraction imported")


# Folder structure setup
DIRECTORIES = ["img/pages", "img/figures", "result"]
for dir in DIRECTORIES:
    os.makedirs(os.path.join(dir), exist_ok=True)

# Read the PDF file
pdf_path = "dummy_scanned.pdf"
pages = []
pages = fh.split_pdf(pdf_path, pages)
print("PDF split into images")

# Extract image metadata
pages = ie.extract_images(pages)
print("Images extracted")

# Extract elements from PDF
element_pages = ee.extract_elements(pdf_path, pages)
print("Elements extracted")

# format the extracted elements
formated_text = ee.format_all_data(element_pages)
print("Data formatted")

# Save the extracted text to a md file
md_text = ""
for text in formated_text:
    md_text += text
    md_text += "\n\n---\n\n"

with open("result/pipeline_2_res.md", "w") as f:
    f.write(md_text)
print("Markdown file created")

# Save the extracted text to a json file
pipeline_2 ={
    "source": os.path.basename(pdf_path),
    "pages": []
}

for i, page in enumerate(pages):
    pipeline_2["pages"].append({
        "index": i,
        "markdown": formated_text[i],
        "text": page["text"],
        "images": []
    })

    for fig in page["figures"]:
        # with open(fig["file_path"], "rb") as img_file:
        #     img = base64.b64encode(img_file.read()).decode("utf-8")

        pipeline_2["pages"][i]["images"].append({
            "index": os.path.basename(fig["file_path"]),
            "bbox": fig["bbox"],
            "name": fig["name"],
            "type": fig["type"],
            "data": fig["data"],
            "description": fig["description"],
            # "image_base64": "data:image/png;base64," + img
        })

# save the pipeline output to a json file
with open("result/pipeline_2_res.jsonl", "w") as f:
    json.dump(pipeline_2, f, indent=4)
print("JSON file created")

print("Pipeline 2 completed!")