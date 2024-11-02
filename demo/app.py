import os
from typing import List

import gradio as gr
from gradio_image_annotation import image_annotator
from gradio_image_annotation.constants import CSS, EXAMPLE_DATA, JS_SCRIPT
from gradio_image_annotation.utils import prepare_annotate_data

## GLOBALS VARIABLES ##
current_loaded_images = {}
calibration_options = {}


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
                "calibration": [0, 0],  # [width, height]
                "annotations": {},
            }

    print(f"🚀 Current loaded image: {current_loaded_images}")

    file_names = list(current_loaded_images.keys())

    return gr.update(choices=file_names, value=file_names[0]), gr.update(
        value=prepare_annotate_data(
            current_loaded_images[file_names[0]].get("file_path", ""),
        )
    )


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
            gr.Markdown("#### Output JSON")

            json_boxes = gr.JSON()

        with gr.Column(scale=70, variant="panel") as annotatate_col:
            gr.Markdown("#### Step 2: Annotate the image")

            annotator = image_annotator(
                value=prepare_annotate_data(current_loaded_images[dropdown.value])
                if current_loaded_images
                else EXAMPLE_DATA,
                boxes_alpha=0.1,
                label_list=["Person", "Vehicle"],
                label_colors=[(0, 255, 0), (255, 0, 0)],
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

            # Register event handler for folder selection

            folder_of_images_btn.upload(
                _handle_folder_selection,
                inputs=[folder_of_images_btn],
                outputs=[dropdown, annotator],
            )

            get_coor_btn.click(
                get_boxes_json,
                annotator,
                json_boxes,
            )

            show_hide_setting_btn.click(
                fn=_show_hide_setting_tab,
                inputs=[setting_state],
                outputs=[setting_col, show_hide_setting_btn, setting_state],
            )


if __name__ == "__main__":
    demo.launch()
