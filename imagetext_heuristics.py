import fitz  # PyMuPDF
import math
import os
import json


# Ensure output folder exists
output_folder = "output_images"
os.makedirs(output_folder, exist_ok=True)


def merge_bboxes(existing_bbox, new_bbox):
    """
    Merge two bounding boxes to create a larger one that encompasses both.
    """
    x0_1, y0_1, x1_1, y1_1 = existing_bbox
    x0_2, y0_2, x1_2, y1_2 = new_bbox

    return (
        min(x0_1, x0_2),  # Top-left x
        min(y0_1, y0_2),  # Top-left y
        max(x1_1, x1_2),  # Bottom-right x
        max(y1_1, y1_2)   # Bottom-right y
    )

def extract_subsections_from_pdf(pdf_path, margin_threshold=50):
    """
    Extracts subsections from a PDF file, considering headings that:
      - Start with a capital letter (Title case).
      - End with a colon.
      - Start at the left margin.
      - Use the 'TwCenMT-Bold' font.
      - Are colored black (color == 0).
      - Are at least 10 characters long.
    Each subsection's bounding box will be calculated based on the lines it spans.
    """
    # Open the PDF document
    doc = fitz.open(pdf_path)

    # Placeholder for the extracted subsections
    subsections = []
    subsection = None
    subsection_bbox = None
    prev_content = None

    # Iterate over all the pages in the PDF
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Load the page
        blocks = page.get_text("dict")["blocks"]  # Get text as dictionary blocks

        # Iterate through the blocks and identify subsections
        for block in blocks:
            # Iterate through each line in the block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if (
                        span['font'] == 'TwCenMT-Bold' and  # Font condition
                        span['color'] == 0 and  # Color condition (black)
                        len(text) >= 10 and  # Text length condition
                        text[0].isalpha() and  # First character is an alphabet
                        text[0].istitle() and  # First character is title case (capitalized)
                        text.endswith(":")  # Text ends with a colon
                    ):
                        flag_subsection = 1
                    else:
                        flag_subsection = 0

                    text = span['text'].strip()
                    font_size = span['size']
                    flags = span['flags']
                    bbox = span['bbox']  # Use span's bbox for each line
                    font = span['font']
                    color = span['color']

                    # Check if the current span is likely a subsection heading
                    if flag_subsection:
                        # Save the previous subsection if any
                        if subsection:
                            subsections.append({
                                "subsection-name": subsection['subsection-name'],
                                "content": subsection['content'],
                                "bbox": subsection_bbox,  # Final bbox for the subsection
                                "page_num": subsection['page_num']
                            })

                        # Start a new subsection dictionary
                        pages = [page_num+1]
                        subsection = {
                            "subsection-name": text.split(":")[0],  # Subsection name
                            "content": "",
                            "page_num": pages
                        }
                        subsection_bbox = bbox  # Initialize bbox with the current span's bbox
                    elif subsection:
                        # Append the content to the current subsection and update bbox
                        subsection["content"] += text + " "
                        subsection_bbox = merge_bboxes(subsection_bbox, bbox)  # Merge bbox
                        if subsection['page_num'][-1]!=page_num+1:
                            subsection['page_num'].append(page_num+1)
        
        # Add the last subsection of the page
    if subsection:
        subsections.append({
            "subsection-name": subsection['subsection-name'],
            "content": subsection['content'],
            "bbox": subsection_bbox,
            "page_num": [page_num + 1]
        })
        subsection = None  # Reset for the next page

    # Closing the PDF file
    doc.close()

    # Print the results (or return them if you'd like)
    for section in subsections:
        print(f"Subsection: {section['subsection-name']}")
        print(f"Content: {section['content']}")
        print(f"BBox: {section['bbox']}\n")
        print(f"PageNum: {section['page_num']}\n")

    return subsections

# Function to modify the bbox based on the first and last subsections of each page
def modify_bboxes(subsections):
    pages_dict = {}

    # Group subsections by their page number(s)
    for subsection in subsections:
        print(subsection["page_num"])
        for page_num in subsection["page_num"]:
            if page_num not in pages_dict:
                pages_dict[page_num] = []
            pages_dict[page_num].append(subsection)
    
    # Iterate through each page and adjust bboxes
    for page_num, page_subsections in pages_dict.items():
        if len(page_subsections) > 0:
            # Modify the first subsection on the page
            page_subsections[0]["bbox"] = (0, 0, page_subsections[0]["bbox"][2], page_subsections[0]["bbox"][3])
            
            # Modify the last subsection on the page
            page_subsections[-1]["bbox"] = (page_subsections[-1]["bbox"][0], page_subsections[-1]["bbox"][1], math.inf, math.inf)

    return subsections


def extract_images_from_subsections(pdf_path, modified_subsections):
    doc = fitz.open(pdf_path)

    # Iterate through each subsection
    for subsection_idx, subsection in enumerate(modified_subsections):
        page_nums = subsection["page_num"]
        bbox = subsection["bbox"]
        img_count = 0  # Counter for image numbering

        # Add an 'images' key to store image paths for the subsection
        subsection["images"] = []

        # Iterate through the pages of the subsection
        for page_num in page_nums:
            print(subsection_idx + 1, page_num)
            page = doc[page_num - 1]  # Access page (0-indexed)

            # Get all images on the page
            images = page.get_images(full=True)
            print(len(images))
            
            # Iterate through the images on the page
            for img in images:
                xref = img[0]  # Reference for the image
                img_rects = page.get_image_rects(xref)
                if subsection_idx == 3:
                    print(bbox)
                    print(img_rects)

                # Check if image is within the subsection bbox
                for img_rect in img_rects:
                    if (
                        img_rect.x0 >= bbox[0] and img_rect.y0 >= bbox[1] and
                        img_rect.y1 <= bbox[3]
                    ):
                        # Extract the image
                        pix = fitz.Pixmap(doc, xref)

                        # Save the image as PNG if it's not already in a PNG format
                        if pix.n < 5:  # this is GRAY or RGB
                            img_path = os.path.join(output_folder, f"subsection_{subsection_idx + 1}_image{img_count + 1}.png")
                            pix.save(img_path)
                            img_count += 1
                        else:  # this is CMYK: convert to RGB first
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                            img_path = os.path.join(output_folder, f"subsection_{subsection_idx + 1}_image{img_count + 1}.png")
                            pix.save(img_path)
                            img_count += 1

                        # Add the saved image path to the subsection
                        subsection["images"].append(img_path)
                        
                        pix = None  # Free pixmap

# Usage
pdf_path = "POET_Everyday_Instructions.pdf"
subsections = extract_subsections_from_pdf(pdf_path, margin_threshold=50)

# Apply the modifications
modified_subsections = modify_bboxes(subsections)

extract_images_from_subsections(pdf_path, modified_subsections)

# Output the modified subsections
for subsection in modified_subsections:
    print(subsection)


# Save the modified subsections to a JSON file
with open("subsections_with_images.json", "w") as json_file:
    json.dump(modified_subsections, json_file, indent=4)
