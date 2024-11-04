import colorsys
import json
import os
from datetime import datetime

import cv2
import numpy as np


def prepare_annotate_data(image_data: dict):
    """
    Prepare `AnnotatedImageData` data structure for the image annotation block.
    """
    return {
        "image": image_data.get("file_path", ""),
        "boxes": image_data.get("boxes", []),
        "calibration_ratio": image_data.get("calibration_ratio", [0, 0]),
    }


def format_boxes_output(boxes: list) -> list:
    """
    Convert current annotation format into Junaid's format

    Current format:
    ```python
        [
            {
                "label": "2",
                "color": [0, 106, 219],
                "xmin": 4062,
                "ymin": 1708,
                "xmax": 4380,
                "ymax": 2113
            },
            {
                "label": "2",
                "color": [0, 106, 219],
                "xmin": 3642,
                "ymin": 1720,
                "xmax": 3945,
                "ymax": 2101
            },
            {
                "label": "1",
                "color": [0, 255, 0],
                "xmin": 3214,
                "ymin": 1712,
                "xmax": 3517,
                "ymax": 2101
            },
            {
                "label": "1",
                "color": [0, 255, 0],
                "xmin": 2778,
                "ymin": 1712,
                "xmax": 3089,
                "ymax": 2109
            }
        ]
    ```
        into this format:
    ```python
        [
            {
                "label": "2",
                "rect": [4062, 1708, 318, 405]
            },
            {
                "label": "2",
                "rect": [3642, 1720, 303, 381]
            },
            {
                "label": "1",
                "rect": [3214, 1712, 303, 389]
            },
            {
                "label": "1",
                "rect": [2778, 1712, 311, 397]
            }
        ]
    ```
    """
    return [
        {
            "label": box["label"],
            "rect": [
                box["xmin"],
                box["ymin"],
                box["xmax"] - box["xmin"],
                box["ymax"] - box["ymin"],
            ],
        }
        for box in boxes
    ]


def format_template_matching_output(json_data: dict) -> list:
    """
    Convert from result json to list of dict to preview
    ```python
        {
            "1": {
                "color": [255, 0, 0],
                "rects": [
                [2774, 1708, 329, 380],
                [3205, 1708, 329, 380],
                [3634, 1708, 329, 380]
                ]
            }
        }
    ```
    into this format:
    ```python
        [
            {
                "label": "1",
                "color": [255, 0, 0],
                "xmin": 2774,
                "ymin": 1708,
                "xmax": 3103,
                "ymax": 2088
            }, ...
    """

    output = []

    print(json_data)

    for label in json_data:
        for rect in json_data[label]["rects"]:
            output.append(
                {
                    "label": label,
                    "color": json_data[label]["color"],
                    "xmin": rect[0],
                    "ymin": rect[1],
                    "xmax": rect[0] + rect[2],
                    "ymax": rect[1] + rect[3],
                }
            )

    return output


def template_matching(
    job_type,
    template_dir,
    result_dir,
    image_path,
    rectangles,
    current_image_name,
    accuracy_threshold,
    rect_overlap_threshold,
    selected_folders,
    selected_angle,
):
    """
    Finds similar objects in an image based on provided rectangles.
    :param image_path: Path to the image file.
    :param rectangles: List of QRectF objects representing annotated areas.
    :param threshold: Threshold for template matching. Value between 0 and 1.
    :return: List of found rectangles.
    """

    def rotate_image(image, angle):
        # Grab the dimensions of the image and then determine the center
        (h, w) = image.shape[:2]
        (cX, cY) = (w // 2, h // 2)
        # Grab the rotation matrix, then grab the sine and cosine
        # (i.e., the rotation components of the matrix)
        M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        # Compute the new bounding dimensions of the image
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
        # Adjust the rotation matrix to take into account translation
        M[0, 2] += (nW / 2) - cX
        M[1, 2] += (nH / 2) - cY
        # Perform the actual rotation and return the image
        return cv2.warpAffine(image, M, (nW, nH))

    # filter rectangles
    def is_overlapping(rect1, rect2):
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # Calculate overlap
        dx = min(x1 + w1, x2 + w2) - max(x1, x2)
        dy = min(y1 + h1, y2 + h2) - max(y1, y2)
        if (dx >= 0) and (dy >= 0):
            overlap_area = dx * dy
            area1 = w1 * h1
            area2 = w2 * h2
            if (overlap_area / min(area1, area2)) > rect_overlap_threshold:
                return True
        return False

    def preprocess_image(image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to enhance contrast
        clahe = cv2.createCLAHE(clipLimit=0.5, tileGridSize=(3, 3))
        contrast_enhanced = clahe.apply(gray_image)

        # If needed, apply morphological operations to clean up the noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        morph_image = cv2.morphologyEx(contrast_enhanced, cv2.MORPH_OPEN, kernel)

        return morph_image

    # random but unique color gen for each unique label
    def HSVToRGB(h, s, v):
        (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
        return (int(255 * r), int(255 * g), int(255 * b))

    def getDistinctColors(n):
        huePartition = 1.0 / (n + 1)
        return [HSVToRGB(huePartition * value, 1.0, 1.0) for value in range(0, n)]

    # Load the image
    image = cv2.imread(image_path)
    image_processed = preprocess_image(image)

    # rectangles without the ones with ignore labels
    filtered_rectangles = []
    for item in rectangles:
        if item["label"] == "ignore":
            x, y, w, h = item["rect"]
            image_processed[y : y + h, x : x + w] = 255  # white out the ignore area
        else:
            filtered_rectangles.append(item)

    # sort filtered_rectangles largest to smallest
    filtered_rectangles.sort(
        key=lambda x: x["rect"][2] * x["rect"][3], reverse=True
    )  # sort by area (w * h) in descending order

    templates_items = []
    unique_labels = []

    # first save annotations as templates
    if job_type == "annotate":
        for item in filtered_rectangles:
            print(f"==>> item: {item}")
            x, y, w, h = item["rect"]
            crop_tmpl = image[y : y + h, x : x + w]
            label_dir = os.path.join(template_dir, current_image_name, item["label"])
            os.makedirs(label_dir, exist_ok=True)

            if item["label"] not in unique_labels:
                unique_labels.append(item["label"])

            cropped_tmpl_name = str(x) + str(y) + str(w) + str(h)
            cropped_tmpl_path = f"{label_dir}/{cropped_tmpl_name}.png"
            templates_items.append({"label": item["label"], "path": cropped_tmpl_path})
            cv2.imwrite(cropped_tmpl_path, crop_tmpl)

    elif job_type == "file":
        for folder in selected_folders:
            folder_path = os.path.join(template_dir, folder)
            for label_folder in os.listdir(folder_path):
                if os.path.isdir(f"{folder_path}/{label_folder}"):
                    if label_folder not in unique_labels:
                        unique_labels.append(label_folder)
                    for filename in os.listdir(f"{folder_path}/{label_folder}"):
                        extensions = (".jpg", ".png", ".jpeg")
                        if filename.lower().endswith(extensions):
                            templates_items.append(
                                {
                                    "label": label_folder,
                                    "path": f"{folder_path}/{label_folder}/{filename}",
                                }
                            )

    unique_colors = getDistinctColors(len(unique_labels))
    unique_labels_with_color = {}
    for label, color in zip(unique_labels, unique_colors):
        unique_labels_with_color[label] = color

    found_labels = {}
    rects_found_count = {}

    for template_item in templates_items:
        template = cv2.imread(template_item["path"])
        template_color = unique_labels_with_color[template_item["label"]]

        def match_template(temp):
            global found_rects_count
            temp_processed = preprocess_image(temp)
            temp_w, temp_h = temp_processed.shape[::-1]

            res = cv2.matchTemplate(
                image_processed, temp_processed, cv2.TM_CCOEFF_NORMED
            )
            loc = np.where(res >= accuracy_threshold)
            for pt in zip(*loc[::-1]):
                # Filter overlaps
                if not any(
                    is_overlapping((pt[0], pt[1], temp_w, temp_h), existing_rect)
                    for label in found_labels
                    for existing_rect in found_labels[label]["rects"]
                ):
                    # draw rectangle around found rect
                    cv2.rectangle(
                        image,
                        pt,
                        (pt[0] + temp_w, pt[1] + temp_h),
                        template_color[::-1],
                        2,
                    )

                    found_rect = (int(pt[0]), int(pt[1]), int(temp_w), int(temp_h))
                    if template_item["label"] not in found_labels:
                        found_labels[template_item["label"]] = {
                            "color": template_color,
                            "rects": [found_rect],
                        }
                    else:
                        found_labels[template_item["label"]]["rects"].append(found_rect)

                    if "found_rects_count" not in rects_found_count:
                        rects_found_count["found_rects_count"] = 1
                    else:
                        rects_found_count["found_rects_count"] += 1

                    # if template_item['label'] not in label_found_count:
                    #     label_found_count[template_item['label']] = {'color': template_color, 'count': 1}
                    # else:
                    #     label_found_count[template_item['label']]['count'] += 1

        if int(selected_angle) != 0:
            angles = np.arange(0, 360, int(selected_angle))
            for angle in angles:
                template_rotated = rotate_image(template, angle)
                match_template(template_rotated)
        else:
            match_template(template)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(result_dir, current_image_name)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    processed_img_name = f"{current_image_name}_{timestamp}.png"
    processed_img_path = f"{save_dir}/{processed_img_name}"
    processed_img_json_path = f"{save_dir}/{current_image_name}_{timestamp}.json"

    # Save the result image
    cv2.imwrite(processed_img_path, image)
    # Save the result json
    with open(processed_img_json_path, "w", encoding="utf8") as f:
        json.dump(found_labels, f)

    return (
        processed_img_path,
        processed_img_json_path,
        processed_img_name,
        found_labels,
        rects_found_count["found_rects_count"],
    )
