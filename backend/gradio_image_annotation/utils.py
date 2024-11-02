def prepare_annotate_data(image_path):
    """
    Prepare `AnnotatedImageData` data structure for the image annotation block.
    """
    return {
        "image": image_path,
        "boxes": [],
    }
