def prepare_annotate_data(image_data: dict):
    """
    Prepare `AnnotatedImageData` data structure for the image annotation block.
    """
    return {
        "image": image_data.get("file_path", ""),
        "boxes": image_data.get("boxes", []),
        "calibration_ratio": image_data.get("calibration_ratio", [0, 0]),
    }
