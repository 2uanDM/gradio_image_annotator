JS_SCRIPT = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.href = url.href;
    }
    
    document.addEventListener('wheel', (event) => {
    if (event.ctrlKey) {
        event.preventDefault();
    }
}, { passive: false });
}
"""

CSS = """
#gradio-upload-button {
    height: 2.5rem !important;
    border-radius: 0.5rem !important;
    margin-top: 1rem !important;
}

#show-hide-settings > label {  
    font-size: 1.1 rem !important;
}
"""

EXAMPLE_DATA = {
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
