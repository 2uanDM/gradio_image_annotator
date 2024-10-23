import gradio as gr
from gradio_image_annotation import image_annotator

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
.gradio-upload-button {
    height: 3rem !important;
    border-radius: 0.5rem !important;
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


def handle_folder_selection(folder):
    print(folder)


with gr.Blocks(
    js=JS_LIGHT_THEME,
    theme=gr.themes.Soft(primary_hue="slate"),
    css=CSS,
) as demo:
    gr.Markdown("# Image Annotation")
    gr.Markdown("---")

    gr.Markdown("#### Step 1: Upload an image")

    selected_folder = gr.Textbox(
        label="Selected folder",
        value="",
        lines=10,
        interactive=False,
    )

    folder_of_images = gr.UploadButton(
        elem_classes=["gradio-upload-button"],
        label="Choose a folder",
        file_count="directory",
    )

    gr.Markdown("---")

    annotator = image_annotator(
        example_annotation,
        label_list=["Person", "Vehicle"],
        label_colors=[(0, 255, 0), (255, 0, 0)],
    )

    button_get = gr.Button("Get bounding boxes")

    json_boxes = gr.JSON()
    button_get.click(get_boxes_json, annotator, json_boxes)

    # Register event handler for folder selection
    folder_of_images.click(
        handle_folder_selection,
        inputs=[folder_of_images],
    )


if __name__ == "__main__":
    demo.launch()
