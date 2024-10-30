import os
from typing import List

import gradio as gr
from gradio_image_annotation import image_annotator

## GLOBALS VARIABLES ##
current_loaded_images = {}
calibration_options = {}

JS_LIGHT_THEME = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.href = url.href;
    }
}
"""

CSS = """
#gradio-upload-button {
    height: 2.5rem !important;
    border-radius: 0.5rem !important;
    margin-top: 1rem !important;
}
"""


example_annotation = {
    "image": "https://gradio-builds.s3.amazonaws.com/demo-files/base.png",
    "boxes": [
        {
            "xmin": 636,
            "ymin": 575,
            "xmax": 801,
            "ymax": 697,
            "label": "Vehicle",
            "color": (255, 0, 0),
        },
        {
            "xmin": 360,
            "ymin": 615,
            "xmax": 386,
            "ymax": 702,
            "label": "Person",
            "color": (0, 255, 0),
        },
    ],
}


def crop(annotations):
    if annotations["boxes"]:
        box = annotations["boxes"][0]
        return annotations["image"][
            box["ymin"] : box["ymax"], box["xmin"] : box["xmax"]
        ]
    return None


def get_boxes_json(annotations):
    return annotations["boxes"]


def handle_folder_selection(list_files: List[str] | None):
    global current_loaded_images

    if list_files is None:
        return []

    # Empty the current loaded images
    current_loaded_images = {}

    for file_path in list_files:
        if file_path.endswith(".png") or file_path.endswith(".jpg"):
            base_name = os.path.basename(file_path)
            current_loaded_images[base_name] = file_path

    file_names = list(current_loaded_images.keys())

    return gr.update(choices=file_names, value=file_names[0])


with gr.Blocks(
    js=JS_LIGHT_THEME,
    theme=gr.themes.Soft(primary_hue="slate"),
    css=CSS,
) as demo:
    gr.Markdown("# Image Annotation")
    gr.Markdown("---")

    gr.Markdown("#### Step 1: Upload an image")

    with gr.Row(equal_height=True) as row:
        with gr.Column(scale=30, variant="panel") as row:
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

        with gr.Column(scale=70, variant="panel") as row:
            gr.Markdown("#### Step 2: Annotate the image")

            annotator = image_annotator(
                example_annotation,
                label_list=["Person", "Vehicle"],
                label_colors=[(0, 255, 0), (255, 0, 0)],
            )

            button_get = gr.Button("Get bounding boxes")

            json_boxes = gr.JSON()
            button_get.click(get_boxes_json, annotator, json_boxes)

            # Register event handler for folder selection
            folder_of_images_btn.upload(
                handle_folder_selection,
                inputs=[folder_of_images_btn],
                outputs=[dropdown],
            )


if __name__ == "__main__":
    demo.launch()
