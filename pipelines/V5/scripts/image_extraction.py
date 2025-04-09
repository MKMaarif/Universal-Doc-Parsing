import cv2
import numpy as np
import supervision as sv
import os
import scripts.model_config as mc
import re

# Extract figures from the pages
def extract_figures(pages):
    # Load YOLOv11 model
    yolo_model = mc.load_yolo()

    # Extract figures from the pages
    for j, page in enumerate(pages):
        image = cv2.imread(page['image'])
        results = yolo_model(image, conf=0.35, iou=0.7)[0]
        detections = sv.Detections.from_ultralytics(results)

        # save figure class_name
        for i, class_name in enumerate(detections.data['class_name']):

            if class_name == 'figure':
                x1, y1, x2, y2 = map(int, detections.xyxy[i])
                section = image[y1:y2, x1:x2]
                output_filename = f"./img/figures/page_{j}_figure_{i}.png"
                cv2.imwrite(output_filename, section)
                # save metadata
                metadata = {
                    "file_path": output_filename,
                    "bbox": [x1, y1, x2, y2],
                    "name": "",
                    "type": "",
                    "data": "",
                    "description": ""
                }
                page["figures"].append(metadata)
    
    # check duplicate figures by bounding box
    for i, page in enumerate(pages):
        figures = page['figures']
        for j in range(len(figures)):
            for k in range(j + 1, len(figures)):
                if figures[j]['bbox'] == figures[k]['bbox']:
                    # remove duplicate figure
                    del figures[k]
                    break

    return pages

# Figure to Table VLM
SYSTEM_FIGURE_PROMPT = """You are a helpful assistant who helps users convert images into understandable formats. 
First, provide the name of the image that you will receive. Then, determine if the image is a graph/chart or simply another type of image. 
If it is a graph/chart, state the chart type and convert it to structured table data in Markdown format with a short explanation or context analysis. 
If it is not a graph/chart, briefly describe the image's content in natural language using short sentences."""

PROMPT_FIGURE_TEMPLATE = """Convert the provided figure image into an understandable format.
Output format:
1.	Chart/graph:
- Figure Name: …
- Chart Type: …
```data
| Structured Table Data |
```
- Short Description: …

2.	If the image is not a chart:
- Figure Name: …
- Short Description: …
"""

# Metadata Extraction
def take_data(result_text):
    data_text = result_text
    # check if the text contains ```data
    if "```data" not in data_text:
        return take_desc(result_text)

    # split the text by ```data
    data_text = data_text.split("```data")[1].strip()
    data_text = data_text.split("```")[0].strip()

    return data_text

def take_desc(result_text):
    desc_text = result_text

    # check if the text contains - Short Description:
    if "Short Description:" not in desc_text:
        return ""

    # split the text by Short Description:
    desc_text = desc_text.split("Short Description:")[1].strip()
    return desc_text

def take_name(result_text):
    name_text = result_text
    # check if the text contains Figure Name:
    if "Figure Name:" not in name_text:
        return ""
    # split the text by Figure Name:
    name_text = name_text.split("Figure Name:")[1].strip()
    name_text = name_text.split("\n")[0].strip()
    return name_text

def take_type(result_text):
    type_text = result_text
    # check if the text contains Chart Type:
    if "Chart Type:" not in type_text:
        return "image"
    # split the text by Chart Type:
    type_text = type_text.split("Chart Type:")[1].strip()
    type_text = type_text.split("\n")[0].strip()
    return type_text

def post_process_figures(result):
    name = take_name(result)
    type = take_type(result) 
    tab = take_data(result)
    desc = take_desc(result)

    return name, type, tab, desc

# Extract metadata from figures
def extract_images(pages):
    vlm_processor = mc.VLMProcessor()

    # Extract figures from the pages
    pages = extract_figures(pages)

    # Extract metadata from figures
    for page in pages:
        for figure in page['figures']:
            result = vlm_processor.generate(
                figure['file_path'], 
                SYSTEM_FIGURE_PROMPT, 
                PROMPT_FIGURE_TEMPLATE
            )
            name, type, tab, desc = post_process_figures(result)
            figure['name'] = name
            figure['type'] = type
            figure['data'] = tab
            figure['description'] = desc

    return pages