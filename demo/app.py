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

examples_crop = [
    {
        "image": "https://raw.githubusercontent.com/gradio-app/gradio/main/guides/assets/logo.png",
        "boxes": [
            {
                "xmin": 30,
                "ymin": 70,
                "xmax": 530,
                "ymax": 500,
                "color": (100, 200, 255),
            }
        ],
    },
    {
        "image": "https://gradio-builds.s3.amazonaws.com/demo-files/base.png",
        "boxes": [
            {
                "xmin": 636,
                "ymin": 575,
                "xmax": 801,
                "ymax": 697,
                "color": (255, 0, 0),
            },
        ],
    },
]


def crop(annotations):
    if annotations["boxes"]:
        box = annotations["boxes"][0]
        return annotations["image"][
            box["ymin"] : box["ymax"], box["xmin"] : box["xmax"]
        ]
    return None


def get_boxes_json(annotations):
    return annotations["boxes"]


with gr.Blocks(js=JS_LIGHT_THEME, theme=gr.themes.Soft(primary_hue="slate")) as demo:
    annotator = image_annotator(
        example_annotation,
        label_list=["Person", "Vehicle"],
        label_colors=[(0, 255, 0), (255, 0, 0)],
    )
    button_get = gr.Button("Get bounding boxes")
    json_boxes = gr.JSON()
    button_get.click(get_boxes_json, annotator, json_boxes)


if __name__ == "__main__":
    demo.launch()
