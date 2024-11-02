<script lang="ts">
import {
  createEventDispatcher,
  onDestroy,
  onMount
} from "svelte";
import {
  BoundingBox,
  Hand
} from "../../assets/icons/index";
import {
  colorHexToRGB,
  colorRGBAToHex
} from "../../utils/colors";
import {
  BoxProperty,
  Colors
} from "../../utils/constants";
import {
  AnnotatedImageData,
  Box
} from "../ts";
import Calibrate from './../../assets/icons/calibrate.svelte';
import {
  Mode
} from './../../utils/enums';
import CalibrationModalbox from "./modal/calibration.svelte";
import CreationModalBox from "./modal/creation.svelte";

export let value: AnnotatedImageData | null;
export let imageUrl: string | null = null;

export let calibration_ratio: [number, number];

export let interactive: boolean;

export let boxAlpha: number = BoxProperty.Alpha; // Transparency of boxes
export let boxMinSize: number = BoxProperty.MinSize;
export let handleSize: number;
export let boxThickness: number;
export let boxSelectedThickness: number;
export let choices: string[] = [];
export let choicesColors: string[] = [];
export let disableEditBoxes: boolean = false;
export let handlesCursor: boolean = true;

let canvas: HTMLCanvasElement;
let ctx: CanvasRenderingContext2D | null; // to draw on the canvas
let image: HTMLImageElement | null = null; // Image to be displayed on the canvas
let selectedBox = -1; // Index of the selected box
let mode: Mode | null = null;

// If current image has no boxes, set mode to creation
if (value !== null && value.boxes.length == 0) {
    mode = Mode.Creation;
}

let canvasXmin = 0; // Min x coordinate of the canvas, starting from the left
let canvasYmin = 0; // Min y coordinate of the canvas, starting from the top
let canvasXmax = 0;
let canvasYmax = 0;
let scaleFactor = 1.0;

let imageWidth = 0;
let imageHeight = 0;

// Modals
let editModalVisible = false;
let newModalVisible = false;
let showCalibrateModal = false;

let showPanel = false; // Information panel
let mouseX = 0;
let mouseY = 0;

const dispatch = createEventDispatcher < {
    change: undefined;
    calibrated: [number, number];
} > ();

function handleMouseMove(event: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    mouseX = event.clientX - rect.left;
    mouseY = event.clientY - rect.top;
    showPanel = true
}

function handleMouseLeave(event: MouseEvent) {
    // showPanel = false;
}

/**
 * Update the UI
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
            for (const box of value.boxes
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
    value.boxes.forEach((box) => {
        box.setSelected(false);
    });
    if (index >= 0 && index < value.boxes.length) {
        value.boxes[index].setSelected(true);
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
    for (const [i, box] of value.boxes.entries()) {
        const handleIndex = box.indexOfPointInsideHandle(mouseX, mouseY);
        if (handleIndex >= 0) {
            selectBox(i);
            box.startResize(handleIndex, event);
            return;
        }
    }

    // Check if the mouse is inside a box
    for (const [i, box] of value.boxes.entries()) {
        if (box.isPointInsideBox(mouseX, mouseY)) {
            selectBox(i);
            box.startDrag(event);
            return;
        }
    }

    // If the mouse is not inside any box, unselect the current box
    selectBox(-1);
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
    } else if (mode === Mode.Calibrate) {
        calibrateBox(event);
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
    const mouseX = (event.clientX - rect.left) / scaleFactor;
    const mouseY = (event.clientY - rect.top) / scaleFactor;

    for (const [_, box] of value.boxes.entries()) {
        const handleIndex = box.indexOfPointInsideHandle(mouseX, mouseY); // Check if the mouse is over any of the resizing handles
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

function calibrateBox(event: PointerEvent) {
    if (value === null) {
        return;
    }

    let color: string;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left - canvasXmin;
    const y = event.clientY - rect.top - canvasYmin;

    if (choicesColors.length > 0) {
        color = colorHexToRGB(choicesColors[0]);
    } else {
        color =
            Colors[value.boxes.length % Colors.length];
    }

    let box = new Box(
        draw,
        onFinishCalibration,
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
        0, // No alpha for calibration
        boxMinSize,
        0, // No handles for calibration
        boxThickness,
        boxSelectedThickness,
        scaleFactor,
    );

    box.startCreating(event, rect.left, rect.top);

    value.boxes = [
        box,
        ...value.boxes,
    ];

    selectBox(0);
    // draw(); // Box is render from here
    dispatch("change");
}

function onFinishCalibration() {
    if (!value) {
        return;
    }

    if (
        selectedBox >= 0 &&
        selectedBox < value.boxes.length
    ) {
        // Handle case when user just click on the canvas without drawing a box
        if (value.boxes[selectedBox].getArea() < 1) {
            onDeleteBox();
        } else if (!disableEditBoxes) {
            showCalibrateModal = true;
        }
    }
}

function onCalibrationModalChange(event) {
    showCalibrateModal = false;

    const lastBox = value.boxes.shift();

    if (!lastBox) {
        return;
    }

    console.log(event);

    if (event.detail.ret == 1) {
        calibration_ratio = [
            event.detail.calibration_ratio[0] / lastBox.getWidth(),
            event.detail.calibration_ratio[1] / lastBox.getHeight()
        ]; // 1 pixel in the current canvas is equal to how many milimeters in the real world
        dispatch("calibrated", calibration_ratio);
    }

    draw(); // Update the UI
    dispatch("change");
}

function createBox(event: PointerEvent) {
    if (value === null) {
        return;
    }

    let color: string;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left - canvasXmin;
    const y = event.clientY - rect.top - canvasYmin;

    if (choicesColors.length > 0) {
        color = colorHexToRGB(choicesColors[0]);
    } else {
        color =
            Colors[value.boxes.length % Colors.length];
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
        scaleFactor,
    );

    // If the box is too small, don't create it
    box.startCreating(event, rect.left, rect.top);

    value.boxes = [
        box,
        ...value.boxes,
    ];

    selectBox(0);
    draw(); // Box is render from here
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
        selectedBox < value.boxes.length
    ) {
        if (value.boxes[selectedBox].getArea() < 1) {
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
        selectedBox < value.boxes.length &&
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

    const {
        detail
    } = event;
    let label = detail.label;
    let color = detail.color;
    let ret = detail.ret;

    if (
        selectedBox >= 0 &&
        selectedBox < value.boxes.length
    ) {
        let box = value.boxes[selectedBox];
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

    const {
        detail
    } = event;
    let label = detail.label;
    let color = detail.color;
    let ret = detail.ret;

    if (
        selectedBox >= 0 &&
        selectedBox < value.boxes.length
    ) {
        let box = value.boxes[selectedBox];
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
        selectedBox < value.boxes.length
    ) {
        value.boxes.splice(selectedBox, 1);
        selectBox(-1);
        dispatch("change");
    }
}

const observer = new ResizeObserver(resize);

function parseInputBoxes() {
    if (value === null) {
        return;
    }

    for (let i = 0; i < value.boxes.length; i++) {
        let box = value.boxes[i];
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
            value.boxes[i] = box;
        }
    }
}

// When the value changes, setImage, parseInputBoxes, resize and draw are called
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
            image.onload = function() {
                resize();
                draw();
            };
        }
    }
}

function resize() {
    if (value === null) {
        return;
    }
    if (canvas) {
        scaleFactor = 1.0;

        if (image !== null) {
            // console.log("Image size", image.width, image.height)

            // Set canvas drawing resolution to the original image size
            canvas.width = image.width;
            canvas.height = image.height;

            // Fixed pixel value to make it fit within the parent container or the viewport.
            canvas.style.width = '100%'; // Makes the canvas responsive
            canvas.style.height = 'auto'; // Maintains the aspect ratio

            // No need to scale the image; it matches the canvas size
            imageWidth = image.width;
            imageHeight = image.height;
            canvasXmin = 0;
            canvasYmin = 0;
            canvasXmax = imageWidth;
            canvasYmax = imageHeight;

            // But need to calculate the scale factor base on the client width
            scaleFactor = canvas.clientWidth / image.width;
        } else {
            // Handle the case when there's no image
            canvas.width = canvas.clientWidth;
            canvas.height = canvas.clientHeight;
            canvasXmin = 0;
            canvasYmin = 0;
            canvasXmax = canvas.width;
            canvasYmax = canvas.height;
        }

        // Update boxes if any
        if (canvasXmax > 0 && canvasYmax > 0) {
            for (const box of value.boxes) {
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
        value.boxes.length > 0
    ) {
        selectBox(0);
    }
    setImage();
    resize();
    draw();

    // Add event listeners
    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    return () => {
        canvas.removeEventListener('mousemove', handleMouseMove);
        canvas.removeEventListener('mouseleave', handleMouseLeave);
    };
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

{#if showPanel}
<div style="display: flex;">
    <div style="flex: 1;">
        <div class="panel">
            Mouse Position: X: {parseInt(mouseX.toString())}, Y: {parseInt(mouseY.toString())}
        </div>
        <div class="panel">
            Image Position: X: {parseInt((mouseX / scaleFactor).toString())}, Y: {parseInt((mouseY / scaleFactor).toString())}
        </div>
    </div>
    <div style="flex: 1;">
        <div class="panel">
            Canvas client width: <b>{canvas.clientWidth}</b>, height: <b>{canvas.clientHeight}</b>
        </div>
        <div class="panel">
            Image width : <b>{canvas.width}</b>, height : <b>{canvas.height}</b>
        </div>
    </div>
    <div style="flex: 1;">
        <div>
            <div class="panel">
                Current scale factor: <b>{scaleFactor.toFixed(2)}</b>
            </div>
            <div class="panel">
                Calibration ratio: <b>{calibration_ratio[0].toFixed(4)} x {calibration_ratio[1].toFixed(4)} (mm)</b> per pixel
            </div>
        </div>

    </div>
    <div><div class="panel">
        Mode: <b style="color: red">{mode === 0 ? "Creation" : mode === 1 ? "Drag" : "Calibrate"}</b>
    </div></div>
</div>
{/if}

{#if interactive}
<span class="canvas-control">
    {#if (calibration_ratio[0] === 0 && calibration_ratio[1] === 0)}
    <p style="font-weight: bold; color: red">Please calibrate first => </p>
    {/if}

    <button
        class="icon"
        style="margin-right: 40px;"
        class:selected={mode === Mode.Calibrate}
        aria-label="Calibrate"
        on:click={() => setCalibrateMode()}><Calibrate /></button
        >

        {#if (calibration_ratio[0] !== 0 && calibration_ratio[1] !== 0)}
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
                {/if}
                </span>
                {/if}

                {#if editModalVisible && value !== null}
                <CreationModalBox
                    on:change={onModalEditChange}
                    on:enter{onModalEditChange}
                    {choices}
                    {choicesColors}
                    label={selectedBox >= 0 &&
                    selectedBox < value.boxes.length
                    ? value.boxes[selectedBox].label
                    : ""}
                    color={selectedBox >= 0 &&
                    selectedBox < value.boxes.length
                    ? colorRGBAToHex(value.boxes[selectedBox].color)
                    : ""}
                    />
                    {/if}

                    {#if newModalVisible && value !== null}
                    <CreationModalBox
                        on:change={onModalNewChange}
                        on:enter{onModalNewChange}
                        {choices}
                        showRemove={false}
                        {choicesColors}
                        label={selectedBox >= 0 &&
                        selectedBox < value.boxes.length
                        ? value.boxes[selectedBox].label
                        : ""}
                        color={selectedBox >= 0 &&
                        selectedBox < value.boxes.length
                        ? colorRGBAToHex(value.boxes[selectedBox].color)
                        : ""}
                        />
                        {/if}
                        {#if showCalibrateModal && value !== null}
                        <CalibrationModalbox
                            on:change={onCalibrationModalChange}
                            />
                            {/if}

<style>
.panel {
    margin-top: 10px;
}

.canvas-annotator {
    /* border-color: var(--block-border-color); */
    width: 100%;
    height: 100%;
    display: block;
    touch-action: none;
    border: 2px solid var(--border-color-primary);
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

.canvas-container {
    width: 100%;
    max-width: none;
}
</style>
