<script lang="ts">
    import { BaseButton } from "@gradio/button";
    import { BaseColorPicker } from "@gradio/colorpicker";
    import { BaseTextbox } from "@gradio/textbox";
    import { createEventDispatcher, onDestroy, onMount } from "svelte";
    import { BaseDropdown } from "../../../patched_dropdown/Index.svelte";
    import { DefaultColor } from "../../../utils/constants";

    export let label = "";
    export let choices: [string, string | number][] = [];
    export let choicesColors: string[] = [];
    export let color = "";

    let currentLabel: string = choices.length > 0 ? choices[0][0] : "";
    let currentColor: string = choicesColors.length > 0 ? choicesColors[0] : "";

    const dispatch = createEventDispatcher<{
        change: object;
    }>();

    function dispatchChange(ret: number) {
        // if currentLabel is not in choices, then it is a new label
        if (currentLabel !== "") {
            if (choices.filter((c) => c[0] === currentLabel).length === 0) {
                choices.push([currentLabel, currentLabel]);
                choicesColors.push(currentColor);
            }
        }


        dispatch("change", {
            label: currentLabel,
            color: currentColor,
            ret: ret, // -1: remove, 0: cancel, 1: change
        });
    }

    function onDropDownChange(event) {
        const { detail } = event;
        let choice = detail;
        
        currentLabel = choice;
        const currentColorIndex = choices.findIndex((c) => c[0] === choice); 
        if (currentColorIndex === -1) {
            currentColor = DefaultColor;
        } else {
            currentColor = choicesColors[currentColorIndex];
        }

        console.log(currentLabel, currentColor);
    }

    function onColorChange(event) {
        currentColor = event.detail;
    }

    function onDropDownEnter(event) {
        onDropDownChange(event);
        dispatchChange(1);
    }

    function handleKeyPress(event: KeyboardEvent) {
        switch (event.key) {
            case "Enter":
                dispatchChange(1);
                break;
        }
    }

    onMount(() => {
        document.addEventListener("keydown", handleKeyPress);
        currentLabel = label;
        currentColor = color;
    });

    onDestroy(() => {
        document.removeEventListener("keydown", handleKeyPress);
    });
</script>

<div class="modal" id="model-box-edit">
    <div class="modal-container">
        <span class="modal-content">
            <div>
                <BaseTextbox
                    bind:value={currentLabel}
                    label="New Label"
                    max_lines={1}
                    root=""
                ></BaseTextbox>
            </div>
            <div style="margin-right: 40px; margin-bottom: 8px;">
                <BaseColorPicker
                    bind:value={currentColor}
                    label="Color"
                    show_label={false}
                    on:change={onColorChange}
                />
            </div>
        </span>
        <span>
            <p style="margin-left: 0.3rem;">Or choose from exists</p>
            <div style="margin-right: 10px; margin-bottom: 2rem;">
                <BaseDropdown
                    bind:value={currentLabel}
                    label="Label"
                    {choices}
                    show_label={false}
                    allow_custom_value={true}
                    on:change={onDropDownChange}
                    on:enter={onDropDownEnter}
                />
            </div>
            <span style="display: flex; align-items: flex-end; gap: 10px; justify-content: flex-end;">
                <div>
                    <BaseButton variant="primary" on:click={() => dispatchChange(1)}>
                        OK
                    </BaseButton>
                </div>
                <div style="margin-right: 8px;">
                    <BaseButton on:click={() => dispatchChange(0)}>
                        Cancel
                    </BaseButton>
                </div>
            </span>
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

    .modal-content {
        display: flex;
        align-items: flex-end;
        gap: 2rem;
        margin-bottom: 1rem;
    }
</style>
