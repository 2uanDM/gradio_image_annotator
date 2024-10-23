<script lang="ts">
    import { onMount, onDestroy, createEventDispatcher } from "svelte";
    import { BoundingBox, Hand, Calibrate } from "../../assets/icons/index";
    import ModalBox from "./modal-box.svelte";
    import Box from "../ts/box.js";
    import AnnotatedImageData from "../ts/annotated-image-data.js";
    import { Mode } from "../../utils/enums.js";
    import { Previous, Next } from "../../assets/icons/index.js";
    import { BoxProperty, Colors } from "../../utils/constants.js";
    import { colorHexToRGB, colorRGBAToHex } from "../../utils/colors.js";

    export let value: null | AnnotatedImageData[];
    export let currentImageIndex: number;
    export let imageUrl: string | null = null;
    export let interactive: boolean;
    export let boxAlpha = BoxProperty.Alpha;
    export let boxMinSize = BoxProperty.MinSize;
    export let handleSize: number;
    export let boxThickness: number;
    export let boxSelectedThickness: number;
    export let choices: string[] = [];
    export let choicesColors: string[] = [];
    export let disableEditBoxes: boolean = false;
    export let singleBox: boolean = false;
    export let handlesCursor: boolean = true;

    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D | null;
    let image: HTMLImageElement | null = null;
    let selectedBox = -1; // Index of the selected box
    let mode: Mode = Mode.Drag; // Default mode for the canvas

    // If current image has no boxes, set mode to creation
    if (value !== null && value[currentImageIndex].boxes.length == 0) {
        mode = Mode.Creation;
    }

    let canvasXmin = 0;
    let canvasYmin = 0;
    let canvasXmax = 0;
    let canvasYmax = 0;
    let scaleFactor = 1.0;

    let imageWidth = 0;
    let imageHeight = 0;

    let editModalVisible = false;
    let newModalVisible = false;

    const dispatch = createEventDispatcher<{
        change: undefined;
    }>();

    /**
     * Draw the image and the boxes on the canvas
     */
    function draw() {
        if (ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
            if (image !== null) {
                ctx.drawImage(
                    image,
                    canvasXmin,
                    canvasYmin,
                    imageWidth,
                    imageHeight,
                );
            }
            if (value !== null) {
                for (const box of value[currentImageIndex].boxes
                    .slice()
                    .reverse()) {
                    box.render(ctx);
                }
            }
        }
    }

    function selectBox(index: number) {
        if (value === null) {
            return;
        }

        selectedBox = index;
        value[currentImageIndex].boxes.forEach((box) => {
            box.setSelected(false);
        });
        if (index >= 0 && index < value[currentImageIndex].boxes.length) {
            value[currentImageIndex].boxes[index].setSelected(true);
        }
        draw();
    }

    function clickBox(event: PointerEvent) {
        if (value === null) {
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        // Check if the mouse is over any of the resizing handles
        for (const [i, box] of value[currentImageIndex].boxes.entries()) {
            const handleIndex = box.indexOfPointInsideHandle(mouseX, mouseY);
            if (handleIndex >= 0) {
                selectBox(i);
                box.startResize(handleIndex, event);
                return;
            }
        }

        // Check if the mouse is inside a box
        for (const [i, box] of value[currentImageIndex].boxes.entries()) {
            if (box.isPointInsideBox(mouseX, mouseY)) {
                selectBox(i);
                box.startDrag(event);
                return;
            }
        }

        if (!singleBox) {
            selectBox(-1);
        }
    }

    function handlePointerDown(event: PointerEvent) {
        if (!interactive) {
            return;
        }

        if (
            event.target instanceof Element &&
            event.target.hasPointerCapture(event.pointerId)
        ) {
            event.target.releasePointerCapture(event.pointerId);
        }

        if (mode === Mode.Creation) {
            createBox(event);
        } else if (mode === Mode.Drag) {
            clickBox(event);
        }
    }

    function handlePointerUp(event: PointerEvent) {
        dispatch("change");
    }

    function handlePointerMove(event: PointerEvent) {
        if (value === null) {
            return;
        }

        if (mode !== Mode.Drag) {
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        for (const [_, box] of value[currentImageIndex].boxes.entries()) {
            const handleIndex = box.indexOfPointInsideHandle(mouseX, mouseY);
            if (handleIndex >= 0) {
                canvas.style.cursor = box.resizeHandles[handleIndex].cursor;
                return;
            }
        }

        canvas.style.cursor = "default";
    }

    function handleKeyPress(event: KeyboardEvent) {
        if (!interactive) {
            return;
        }

        switch (event.key) {
            case "Delete":
                onDeleteBox();
                break;
        }
    }

    function createBox(event: PointerEvent) {
        if (value === null) {
            return;
        }

        let color: string;

        const rect = canvas.getBoundingClientRect();
        const x = (event.clientX - rect.left - canvasXmin) / scaleFactor;
        const y = (event.clientY - rect.top - canvasYmin) / scaleFactor;

        if (choicesColors.length > 0) {
            color = colorHexToRGB(choicesColors[0]);
        } else if (singleBox) {
            if (value[currentImageIndex].boxes.length > 0) {
                color = value[currentImageIndex].boxes[0].color;
            } else {
                color = Colors[0];
            }
        } else {
            color =
                Colors[value[currentImageIndex].boxes.length % Colors.length];
        }

        let box = new Box(
            draw,
            onBoxFinishCreation,
            canvasXmin,
            canvasYmin,
            canvasXmax,
            canvasYmax,
            "",
            x,
            y,
            x,
            y,
            color,
            boxAlpha,
            boxMinSize,
            handleSize,
            boxThickness,
            boxSelectedThickness,
        );

        // If the box is too small, don't create it
        box.startCreating(event, rect.left, rect.top);

        if (singleBox) {
            value[currentImageIndex].boxes = [box];
            setDragMode();
        } else {
            value[currentImageIndex].boxes = [
                box,
                ...value[currentImageIndex].boxes,
            ];
        }
        selectBox(0);
        draw();
        dispatch("change");
    }

    function setCalibrateMode() {
        mode = Mode.Calibrate;
        canvas.style.cursor = "crosshair";
    }

    function setCreateMode() {
        mode = Mode.Creation;
        canvas.style.cursor = "crosshair";
    }

    function setDragMode() {
        mode = Mode.Drag;
        canvas.style.cursor = "default";
    }

    function onBoxFinishCreation() {
        if (!value) {
            return;
        }

        if (
            selectedBox >= 0 &&
            selectedBox < value[currentImageIndex].boxes.length
        ) {
            if (value[currentImageIndex].boxes[selectedBox].getArea() < 1) {
                onDeleteBox();
            } else if (!disableEditBoxes) {
                newModalVisible = true;
            }
        }
    }

    function onEditBox() {
        if (!value) {
            return;
        }

        if (
            selectedBox >= 0 &&
            selectedBox < value[currentImageIndex].boxes.length &&
            !disableEditBoxes
        ) {
            editModalVisible = true;
        }
    }

    function handleDoubleClick(event: MouseEvent) {
        if (!interactive) {
            return;
        }

        onEditBox();
    }

    function onModalEditChange(event) {
        if (!value) {
            return;
        }

        editModalVisible = false;

        const { detail } = event;
        let label = detail.label;
        let color = detail.color;
        let ret = detail.ret;

        if (
            selectedBox >= 0 &&
            selectedBox < value[currentImageIndex].boxes.length
        ) {
            let box = value[currentImageIndex].boxes[selectedBox];
            if (ret == 1) {
                box.label = label;
                box.color = colorHexToRGB(color);
                draw();
                dispatch("change");
            } else if (ret == -1) {
                onDeleteBox();
            }
        }
    }

    function onModalNewChange(event) {
        if (!value) {
            return;
        }

        newModalVisible = false;

        const { detail } = event;
        let label = detail.label;
        let color = detail.color;
        let ret = detail.ret;

        if (
            selectedBox >= 0 &&
            selectedBox < value[currentImageIndex].boxes.length
        ) {
            let box = value[currentImageIndex].boxes[selectedBox];
            if (ret == 1) {
                box.label = label;
                box.color = colorHexToRGB(color);
                draw();
                dispatch("change");
            } else {
                onDeleteBox();
            }
        }
    }

    function onDeleteBox() {
        if (!value) {
            return;
        }

        if (
            selectedBox >= 0 &&
            selectedBox < value[currentImageIndex].boxes.length
        ) {
            value[currentImageIndex].boxes.splice(selectedBox, 1);
            selectBox(-1);
            if (singleBox) {
                setCreateMode();
            }
            dispatch("change");
        }
    }

    function resize() {
        if (value === null) {
            return;
        }

        if (canvas) {
            scaleFactor = 1;
            canvas.width = canvas.clientWidth;
            if (image !== null) {
                if (image.width > canvas.width) {
                    scaleFactor = canvas.width / image.width;
                    imageWidth = image.width * scaleFactor;
                    imageHeight = image.height * scaleFactor;
                    canvasXmin = 0;
                    canvasYmin = 0;
                    canvasXmax = imageWidth;
                    canvasYmax = imageHeight;
                    canvas.height = imageHeight;
                } else {
                    imageWidth = image.width;
                    imageHeight = image.height;
                    var x = (canvas.width - imageWidth) / 2;
                    canvasXmin = x;
                    canvasYmin = 0;
                    canvasXmax = x + imageWidth;
                    canvasYmax = image.height;
                    canvas.height = imageHeight;
                }
            } else {
                canvasXmin = 0;
                canvasYmin = 0;
                canvasXmax = canvas.width;
                canvasYmax = canvas.height;
                canvas.height = canvas.clientHeight;
            }
            if (canvasXmax > 0 && canvasYmax > 0) {
                for (const box of value[currentImageIndex].boxes) {
                    box.canvasXmin = canvasXmin;
                    box.canvasYmin = canvasYmin;
                    box.canvasXmax = canvasXmax;
                    box.canvasYmax = canvasYmax;
                    box.setScaleFactor(scaleFactor);
                }
            }
            draw();
            dispatch("change");
        }
    }
    const observer = new ResizeObserver(resize);

    function parseInputBoxes() {
        if (value === null) {
            return;
        }

        for (let i = 0; i < value[currentImageIndex].boxes.length; i++) {
            let box = value[currentImageIndex].boxes[i];
            if (!(box instanceof Box)) {
                let color = "";
                let label = "";
                if ((box as any).hasOwnProperty("color")) {
                    color = box["color"];
                    if (Array.isArray(color) && color.length === 3) {
                        color = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
                    }
                } else {
                    color = Colors[i % Colors.length];
                }
                if ((box as any).hasOwnProperty("label")) {
                    label = box["label"];
                }
                box = new Box(
                    draw,
                    onBoxFinishCreation,
                    canvasXmin,
                    canvasYmin,
                    canvasXmax,
                    canvasYmax,
                    label,
                    box["xmin"],
                    box["ymin"],
                    box["xmax"],
                    box["ymax"],
                    color,
                    boxAlpha,
                    boxMinSize,
                    handleSize,
                    boxThickness,
                    boxSelectedThickness,
                );
                value[currentImageIndex].boxes[i] = box;
            }
        }
    }

    $: {
        value;
        setImage();
        parseInputBoxes();
        resize();
        draw();
    }

    function setImage() {
        if (imageUrl !== null) {
            if (image === null || image.src != imageUrl) {
                image = new Image();
                image.src = imageUrl;
                image.onload = function () {
                    resize();
                    draw();
                };
            }
        }
    }

    onMount(() => {
        if (Array.isArray(choices) && choices.length > 0) {
            if (!Array.isArray(choicesColors) || choicesColors.length == 0) {
                for (let i = 0; i < choices.length; i++) {
                    let color = Colors[i % Colors.length];
                    choicesColors.push(colorRGBAToHex(color));
                }
            }
        }

        ctx = canvas.getContext("2d");
        observer.observe(canvas);

        if (
            selectedBox < 0 &&
            value !== null &&
            value[currentImageIndex].boxes.length > 0
        ) {
            selectBox(0);
        }
        setImage();
        resize();
        draw();
    });

    function handleCanvasFocus() {
        document.addEventListener("keydown", handleKeyPress);
    }

    function handleCanvasBlur() {
        document.removeEventListener("keydown", handleKeyPress);
    }

    onDestroy(() => {
        document.removeEventListener("keydown", handleKeyPress);
    });

    // Handle previous image
    function handlePreviousImage() {
        if (!value) {
            return;
        }

        if (currentImageIndex > 0) {
            currentImageIndex -= 1;
            if (value !== null && value[currentImageIndex].boxes.length == 0) {
                setCreateMode();
            }
            selectBox(-1);
            setImage();
            resize();
            draw();
        }
    }

    // Handle next image
    function handleNextImage() {
        if (!value) {
            return;
        }

        if (currentImageIndex < value.length - 1) {
            currentImageIndex += 1;
            if (value !== null && value[currentImageIndex].boxes.length == 0) {
                setCreateMode();
            }
            selectBox(-1);
            setImage();
            resize();
            draw();
        }
    }
</script>

<div
    class="canvas-container"
    tabindex="-1"
    on:focusin={handleCanvasFocus}
    on:focusout={handleCanvasBlur}
>
    <canvas
        bind:this={canvas}
        on:pointerdown={handlePointerDown}
        on:pointerup={handlePointerUp}
        on:pointermove={handlesCursor ? handlePointerMove : null}
        on:dblclick={handleDoubleClick}
        class="canvas-annotator"
    ></canvas>
</div>

{#if interactive}
    <span>
        <button
            class="icon"
            aria-label="Back to previous image"
            on:click={() => handlePreviousImage()}
        >
            <Previous />
        </button>
    </span>
    <span class="canvas-control">
        <button
            class="icon"
            class:selected={mode === Mode.Calibrate}
            aria-label="Calibrate"
            on:click={() => setCalibrateMode()}><Calibrate /></button
        >
        <button
            class="icon"
            class:selected={mode === Mode.Creation}
            aria-label="Create box"
            on:click={() => setCreateMode()}><BoundingBox /></button
        >
        <button
            class="icon"
            class:selected={mode === Mode.Drag}
            aria-label="Edit boxes"
            on:click={() => setDragMode()}><Hand /></button
        >
    </span>
{/if}

{#if editModalVisible && value !== null}
    <ModalBox
        on:change={onModalEditChange}
        on:enter{onModalEditChange}
        {choices}
        {choicesColors}
        label={selectedBox >= 0 &&
        selectedBox < value[currentImageIndex].boxes.length
            ? value[currentImageIndex].boxes[selectedBox].label
            : ""}
        color={selectedBox >= 0 &&
        selectedBox < value[currentImageIndex].boxes.length
            ? colorRGBAToHex(value[currentImageIndex].boxes[selectedBox].color)
            : ""}
    />
{/if}

{#if newModalVisible && value !== null}
    <ModalBox
        on:change={onModalNewChange}
        on:enter{onModalNewChange}
        {choices}
        showRemove={false}
        {choicesColors}
        label={selectedBox >= 0 &&
        selectedBox < value[currentImageIndex].boxes.length
            ? value[currentImageIndex].boxes[selectedBox].label
            : ""}
        color={selectedBox >= 0 &&
        selectedBox < value[currentImageIndex].boxes.length
            ? colorRGBAToHex(value[currentImageIndex].boxes[selectedBox].color)
            : ""}
    />
{/if}

<style>
    .canvas-annotator {
        border-color: var(--block-border-color);
        width: 100%;
        height: 100%;
        display: block;
        touch-action: none;
    }

    .canvas-control {
        display: flex;
        align-items: center;
        justify-content: center;
        border-top: 1px solid var(--border-color-primary);
        width: 100%;
        bottom: 0;
        left: 0;
        right: 0;
        margin-left: auto;
        margin-right: auto;
        margin-top: var(--size-2);
    }

    .icon {
        width: 30px;
        height: 30px;
        margin: var(--spacing-lg) var(--spacing-xs);
        padding: var(--spacing-xs);
        color: var(--neutral-400);
        border-radius: var(--radius-md);
    }

    .icon:hover,
    .icon:focus {
        color: var(--color-accent);
    }

    .selected {
        color: var(--color-accent);
    }

    .canvas-container:focus {
        outline: none;
    }
</style>
