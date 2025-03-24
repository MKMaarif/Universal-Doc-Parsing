import os
import json

import scripts.file_handler as fh
import scripts.image_extraction as ie
import scripts.element_extraction as ee

# Read the PDF file
pdf_path = "dummy_scanned.pdf"
pages = []
pages = fh.split_pdf(pdf_path, pages)

# Extract image metadata
pages = ie.extract_images(pages)

# Extract elements from PDF
element_pages = ee.extract_elements(pdf_path, pages)

# Save the extracted elements
pipeline_2 ={
    "source": os.path.basename(pdf_path),
    "pages": []
}

for i, page in enumerate(pages):
    pipeline_2["pages"].append({
        "index": i,
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
with open("pipeline_2_res.jsonl", "w") as f:
    json.dump(pipeline_2, f, indent=4)

# save extracted text to markdown file
with open("pipeline_2_res.md", "w") as f:
    for page in pipeline_2["pages"]:
        f.write(page["text"])
        f.write("\n\n---\n\n")