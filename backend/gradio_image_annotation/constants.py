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

#run-template-matching {
    color: #e0e0e0 !important; /* Slightly off-white for text */
    background: linear-gradient(135deg, #001f3f 0%, #2e0057 50%, #2a0a45 100%) !important; /* Darker gradient */
    border: 2px solid #3f00ff; /* Dark neon purple border */
    padding: 12px 24px;
    font-size: 16px;
    font-weight: bold;
    text-transform: uppercase;
    border-radius: 8px;
    cursor: pointer;
    box-shadow: 0px 0px 10px rgba(63, 0, 255, 0.6), /* Deep purple glow */
                0px 0px 20px rgba(0, 255, 255, 0.3); /* Teal glow */
    transition: all 0.3s ease;
}

#run-template-matching:hover {
    background: linear-gradient(135deg, #2a0a45 0%, #2e0057 50%, #001f3f 100%) !important; /* Reversed gradient on hover */
    box-shadow: 0px 0px 15px rgba(63, 0, 255, 0.8), 
                0px 0px 30px rgba(0, 255, 255, 0.5); /* Stronger glow on hover */
}

#run-template-matching:active {
    background: linear-gradient(135deg, #2e0057 0%, #001f3f 50%, #2a0a45 100%) !important; /* Slight color shift on active */
    transform: scale(0.98); /* Slightly pressed effect */
}

"""

EXAMPLE_DATA = {
    "image": "https://gradio-builds.s3.amazonaws.com/demo-files/base.png",
    "boxes": [],
    "calibration_ratio": [0, 0],
}
