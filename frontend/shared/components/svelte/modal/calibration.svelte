<script lang="ts">
import {
  BaseButton
} from "@gradio/button";
import {
  BaseTextbox
} from "@gradio/textbox";
import {
  createEventDispatcher,
  onDestroy,
  onMount
} from "svelte";

export let calibration_ratio: [number, number] = [0, 0];

const dispatch = createEventDispatcher < {
    change: object
} > ();

let realWidthText: string = "";
let realHeightText: string = "";
let errorTimeout: NodeJS.Timeout;
$: parseError = false;

function dispatchChange(ret: number) {
    dispatch("change", {
        calibration_ratio: calibration_ratio,
        ret: ret, // 0: cancel, 1: change
    });
}

function handleKeyPress(event: KeyboardEvent) {
    if (event.key === "Enter") {
        saveCalibration();
    }
}

function saveCalibration() {
    const width = parseFloat(realWidthText);
    const height = parseFloat(realHeightText);

    if (isNaN(width) || isNaN(height)) {
        showError();
    } else {
        parseError = false;
        calibration_ratio = [width, height];
        dispatchChange(1);
    }
}

function showError() {
    parseError = true;
    if (errorTimeout) clearTimeout(errorTimeout); // Clear any existing timeout to reset the timer
    errorTimeout = setTimeout(() => {
        parseError = false;
    }, 4000); // Hide the error after 5 seconds
}

onMount(() => {
    document.addEventListener("keydown", handleKeyPress);
});

onDestroy(() => {
    document.removeEventListener("keydown", handleKeyPress);
    if (errorTimeout) clearTimeout(errorTimeout); // Cleanup timeout on component destroy
});
</script>

<div class="modal" id="modal-calibration-box">
    <div class="modal-container">
        <span>
            <div class="textbox-row">
                <BaseTextbox
                    bind:value={realWidthText}
                    label="Real Width"
                    max_lines={1}
                    root=""
                ></BaseTextbox>
                <p>mm</p>
            </div>
            <div class="textbox-row">
                <BaseTextbox
                    bind:value={realHeightText}
                    label="Real Height"
                    max_lines={1}
                    root=""
                ></BaseTextbox>
                <p>mm</p>
            </div>
            {#if parseError}
            <p style="color: red; margin-top: 1rem; margin-bottom: 1rem">Please enter valid numbers for width and height 🔥</p>
            {/if}
            <div style="display: flex; justify-content: center;">
                <div style="width: 100px; margin-right: 10px;">
                    <BaseButton variant="primary" on:click={saveCalibration}>Save</BaseButton>
                </div>
                <div style="width: 100px;">
                    <BaseButton variant="primary" on:click={() => {dispatchChange(0)}}>Cancel</BaseButton>
                </div>
            </div>
        </span>
    </div>
</div>

    
    <style>
.modal {
    position: fixed;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    z-index: var(--layer-top);
    -webkit-backdrop-filter: blur(4px);
    backdrop-filter: blur(4px);
}

.modal-container {
    border-style: solid;
    border-width: var(--block-border-width);
    border-color: var(--block-border-color);
    margin-top: 10%;
    padding: 20px;
    box-shadow: var(--block-shadow);
    border-color: var(--block-border-color);
    border-radius: var(--block-radius);
    background: var(--block-background-fill);
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    width: fit-content;
}

.textbox-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-right: 1rem;
    margin-bottom: 1rem;
}
</style>
