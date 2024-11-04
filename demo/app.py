import json
import os
from typing import List

import gradio as gr
from gradio_image_annotation import ImageAnnotator
from gradio_image_annotation.constants import CSS, EXAMPLE_DATA, JS_SCRIPT
from gradio_image_annotation.utils import (
    format_boxes_output,
    format_template_matching_output,
    prepare_annotate_data,
    template_matching,
)

## GLOBALS VARIABLES ##
current_loaded_images = {}
calibration_options = {}
TEMPLATES_DIR = "templates"
RESULTS_DIR = "results"

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_boxes_json(annotations):
    return annotations["boxes"]


def _show_hide_setting_tab(setting_state):
    status = not setting_state
    btn_label = "Show Setting" if setting_state else "Hide Setting"

    return gr.update(visible=status), btn_label, status


def _handle_folder_selection(list_files: List[str] | None):
    global current_loaded_images

    if list_files is None:
        return []

    # Empty the current loaded images
    current_loaded_images = {}

    for file_path in list_files:
        if file_path.endswith(".png") or file_path.endswith(".jpg"):
            base_name = os.path.basename(file_path)
            current_loaded_images[base_name] = {
                "file_path": file_path,
                "calibration_ratio": [0, 0],  # [width, height]
                "boxes": [],
            }

    # print(f"🚀 Current loaded image: {current_loaded_images}")

    file_names = list(current_loaded_images.keys())

    return gr.update(choices=file_names, value=file_names[0]), gr.update(
        value=prepare_annotate_data(
            current_loaded_images[file_names[0]],
        )
    )


def handlePrevButtonClick(dropdown):
    if dropdown is None:
        gr.Info("Please select an folder first")
        return dropdown, gr.update(
            value=prepare_annotate_data(EXAMPLE_DATA)
        ) if current_loaded_images else EXAMPLE_DATA

    list_keys = list(current_loaded_images.keys())

    index = list_keys.index(dropdown)

    if index == 0:
        gr.Info("You are at the first image")

        print("Current loaded images: ", current_loaded_images)

        return dropdown, gr.update(
            value=prepare_annotate_data(current_loaded_images[dropdown])
        )
    else:
        dropdown = list_keys[index - 1]
        return dropdown, gr.update(
            value=prepare_annotate_data(current_loaded_images[list_keys[index - 1]])
        )


def handleNextButtonClick(dropdown):
    if dropdown is None:
        gr.Info("Please select an folder first")
        return dropdown, gr.update(
            value=prepare_annotate_data(EXAMPLE_DATA)
        ) if current_loaded_images else EXAMPLE_DATA

    list_keys = list(current_loaded_images.keys())

    index = list_keys.index(dropdown)

    if index == len(list_keys) - 1:
        gr.Info("You are at the last image")
        return dropdown, gr.update(
            value=prepare_annotate_data(current_loaded_images[list_keys[index]])
        )
    else:
        dropdown = list_keys[index + 1]
        return dropdown, gr.update(
            value=prepare_annotate_data(current_loaded_images[list_keys[index + 1]])
        )


def handleReloadButtonClick(dropdown):
    if dropdown is None:
        gr.Info("Please select an folder first")
        return gr.update(value=prepare_annotate_data(EXAMPLE_DATA))

    return gr.update(value=prepare_annotate_data(current_loaded_images[dropdown]))


def handleSelect(dropdown):
    print(f"==>> dropdown: {dropdown}")
    return gr.update(value=prepare_annotate_data(current_loaded_images[dropdown]))


def update_calibration_data(image_name: str, annotator: dict):
    if image_name is None:
        return
    print(
        f"🚀 Update calibration data of image {image_name} from {current_loaded_images[image_name].get('calibration_ratio')}"
        f"to {annotator['calibration_ratio']}"
    )

    current_loaded_images[image_name]["calibration_ratio"] = annotator[
        "calibration_ratio"
    ]


def update_new_boxes_data(image_name: str, annotator: dict):
    if image_name is None or image_name not in current_loaded_images:
        return

    # print(f"🚀 Update new boxes data: {annotator['boxes']}")
    current_loaded_images.get(image_name, {})["boxes"] = annotator["boxes"]

    print(f"🚀 Current data: {current_loaded_images[image_name]}")


def exec_template_matching(
    dropdown,
    accuracy_threshold,
    bounding_rect_overlap_threshold,
    rotation_angle_step,
    use_template_checkbox,
    choose_folder_templates,
    annotator,
):
    # Check if an image is selected
    if dropdown is None:
        gr.Info("Please select an image first")
        return None, None  # Return empty outputs

    # Get the image data from the current_loaded_images dictionary
    image_data = current_loaded_images.get(dropdown)
    if image_data is None:
        gr.Info("Image data not found")
        return None, None

    # Get the image path and name
    image_path = image_data["file_path"]
    current_image_name = dropdown

    rectangles = format_boxes_output(annotator.get("boxes", []))

    if use_template_checkbox:
        job_type = "file"
        selected_folders = choose_folder_templates
    else:
        job_type = "annotate"
        selected_folders = []  # Not used when job_type is 'annotate'

    (
        processed_img_path,
        processed_img_json_path,
        processed_img_name,
        found_labels,
        rects_found_count,
    ) = template_matching(
        job_type=job_type,
        template_dir=TEMPLATES_DIR,
        result_dir=RESULTS_DIR,
        image_path=image_path,
        rectangles=rectangles,
        current_image_name=current_image_name.rsplit(".", 1)[0],
        accuracy_threshold=accuracy_threshold,
        rect_overlap_threshold=bounding_rect_overlap_threshold,
        selected_folders=selected_folders,
        selected_angle=int(rotation_angle_step),
    )

    print(f"🚀 Found labels: {found_labels}")
    print(f"🚀 Rectangles found count: {rects_found_count}")
    print(f"🚀 Processed image path: {processed_img_path}")

    # Load the JSON data for display
    if os.path.exists(processed_img_json_path):
        with open(processed_img_json_path, "r", encoding="utf8") as f:
            json_data = json.load(f)
    else:
        json_data = []

    # Convert the output to a format that can be displayed in the UI
    formatted_json_data = format_template_matching_output(json_data)

    # Update the current image data with the new bounding boxes
    current_loaded_images[current_image_name]["boxes"] = formatted_json_data

    return gr.update(
        value=prepare_annotate_data(current_loaded_images[current_image_name])
    ), gr.update(value=json_data)


with gr.Blocks(
    js=JS_SCRIPT,
    theme=gr.themes.Soft(primary_hue="slate"),
    css=CSS,
    fill_height=True,
    fill_width=True,
) as demo:
    gr.Markdown("# Image Annotation")
    gr.Markdown(
        "**Note**: Zoom by `Ctrl + Mouse Wheel` is locked, please do that with `Ctrl + =` or `Ctrl + -`"
    )
    gr.Markdown("---")

    with gr.Row(equal_height=True) as row:
        setting_state = gr.State(value=True)
        with gr.Column(scale=30, variant="panel", visible=setting_state) as setting_col:
            gr.Markdown("#### Step 1: Upload an image")
            dropdown = gr.Dropdown(
                label="Choose an image",
                allow_custom_value=True,
                interactive=True,
            )

            folder_of_images_btn = gr.UploadButton(
                elem_id="gradio-upload-button",
                variant="primary",
                label="Choose a folder",
                file_count="directory",
            )

            gr.Markdown("---")
            gr.Markdown("#### Template Matching Setting")

            with gr.Row(variant="panel"):
                accuracy_threshold = gr.Slider(
                    label="Accuracy Threshold",
                    minimum=0.1,
                    maximum=1.0,
                    step=0.01,
                    value=0.8,
                    interactive=True,
                )

                bounding_rect_overlap_threshold = gr.Slider(
                    label="Bounding Rect Overlap",
                    minimum=0.1,
                    maximum=1.0,
                    step=0.01,
                    value=0.2,
                    interactive=True,
                )

            rotation_angle_step = gr.Dropdown(
                label="Rotation Angle Step",
                choices=[0, 30, 45, 90, 180],
                value=90,
                interactive=True,
            )

            gr.Markdown("---")

            with gr.Row(variant="panel"):
                use_template_checkbox = gr.Checkbox(
                    label="Use Template Matching",
                    value=False,
                    interactive=True,
                )

                choose_folder_templates = gr.Dropdown(
                    choices=os.listdir(TEMPLATES_DIR),
                    label="Choose at least one template",
                    interactive=False,
                    multiselect=True,
                )

            gr.Markdown("#### Output JSON")

            with gr.Accordion():
                json_boxes = gr.JSON()

        with gr.Column(scale=70, variant="panel") as annotatate_col:
            gr.Markdown("#### Step 2: Annotate the image")

            if current_loaded_images:
                annotator = ImageAnnotator(
                    value=prepare_annotate_data(current_loaded_images[dropdown.value]),
                    boxes_alpha=0,
                    box_thickness=0.1,
                )
            else:
                annotator = ImageAnnotator(
                    value=EXAMPLE_DATA,
                    boxes_alpha=0,
                    box_thickness=0.1,
                )

            with gr.Row(variant="panel"):
                prev_button = gr.Button(
                    value="< Prev",
                    variant="primary",
                    scale=20,
                )

                reload_image = gr.Button(
                    value="Reload image",
                    variant="stop",
                    scale=60,
                )

                next_button = gr.Button(
                    value="Next >",
                    variant="primary",
                    scale=20,
                )

            with gr.Row(variant="panel"):
                show_hide_setting_btn = gr.Button(
                    value="Show Setting" if not setting_state else "Hide Setting",
                    variant="stop",
                )

                get_coor_btn = gr.Button(
                    "Get bounding boxes",
                    variant="primary",
                )

                run_template_matching = gr.Button(
                    "Run Template Matching",
                    elem_id="run-template-matching",
                )

            # Setting event
            folder_of_images_btn.upload(
                _handle_folder_selection,
                inputs=[folder_of_images_btn],
                outputs=[dropdown, annotator],
            )

            show_hide_setting_btn.click(
                fn=_show_hide_setting_tab,
                inputs=[setting_state],
                outputs=[setting_col, show_hide_setting_btn, setting_state],
            )

            use_template_checkbox.change(
                fn=lambda x: gr.update(
                    interactive=x, choices=os.listdir(TEMPLATES_DIR)
                ),
                inputs=[use_template_checkbox],
                outputs=[choose_folder_templates],
            )

            # Navigation
            prev_button.click(
                fn=handlePrevButtonClick,
                inputs=[dropdown],
                outputs=[dropdown, annotator],
            )

            next_button.click(
                fn=handleNextButtonClick,
                inputs=[dropdown],
                outputs=[dropdown, annotator],
            )

            reload_image.click(
                fn=handleReloadButtonClick,
                inputs=[dropdown],
                outputs=[annotator],
            )

            dropdown.change(
                fn=handleSelect,
                inputs=[dropdown],
                outputs=[annotator],
            )

            # Annotator event
            annotator.calibrated(
                fn=update_calibration_data, inputs=[dropdown, annotator]
            )

            annotator.change(fn=update_new_boxes_data, inputs=[dropdown, annotator])

            get_coor_btn.click(
                get_boxes_json,
                annotator,
                json_boxes,
            )

            # Run template matching
            run_template_matching.click(
                fn=exec_template_matching,
                inputs=[
                    dropdown,
                    accuracy_threshold,
                    bounding_rect_overlap_threshold,
                    rotation_angle_step,
                    use_template_checkbox,
                    choose_folder_templates,
                    annotator,
                ],
                outputs=[annotator, json_boxes],
            )


if __name__ == "__main__":
    demo.launch()
