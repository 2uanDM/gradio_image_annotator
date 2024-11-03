<script lang="ts">
import {
  Download
} from "@gradio/icons";
import {
  DownloadLink
} from "@gradio/wasm/svelte";
import {
  createEventDispatcher
} from "svelte";

import {
  IconButton
} from "@gradio/atoms";
import type {
  I18nFormatter,
  SelectData
} from "@gradio/utils";

import {
  AnnotatedImageData
} from "../ts";
import ImageCanvas from "./image-canvas.svelte";

export let value: null | AnnotatedImageData = null;
export let label: string | undefined = "";
export let show_label: boolean;
export let selectable = false;
export let interactive: boolean;
export let i18n: I18nFormatter;
``
export let showDownloadButton: boolean;

export let calibration_ratio: [number, number] = [0, 0];

// Box properties
export let boxAlpha;
export let labelList: string[];
export let labelColors: string[];
export let boxMinSize: number;
export let handleSize: number;
export let boxThickness: number;
export let disableEditBoxes: boolean;
export let boxSelectedThickness: number;

// Cursor for each mode
export let handlesCursor: boolean;

/**
 * ================================= Functions =================================
 */

console.log(value)

// Create a dispatcher to dispatch events
const dispatch = createEventDispatcher < {
    change: undefined;
    clear: undefined;
    drag: boolean;
    upload ? : never;
    select: SelectData;
    calibrated: [number, number];
} > ();
</script>

<!-- <BlockLabel {show_label} Icon={ImageIcon} label={label || "Junaid"} /> -->

<div class="icon-buttons">
    {#if showDownloadButton && value !== null}
    <DownloadLink
        href={value.image.url}
        download={value.image.orig_name || "image"}
        >
        <IconButton Icon={Download} label={i18n("common.download")} />
    </DownloadLink>
    {/if}
</div>

<div data-testid="image" class="image-container">
    <div class="upload-container">
        <div class:selectable class="image-frame">
            {#if value}
            <ImageCanvas
                bind:value={value}
                bind:calibration_ratio={calibration_ratio}
                on:change={() => dispatch("change")}
                on:calibrated={(e) => {dispatch("calibrated", e.detail); console.log("dispatch in image-annotator")}}
                {boxAlpha}
                {labelList}
                {labelColors}
                {boxMinSize}
                {interactive}
                {handleSize}
                {boxThickness}
                {disableEditBoxes}
                {handlesCursor}
                {boxSelectedThickness}
                src={value.image.url}
                />
                {/if}
                </div>
                </div>
                </div>

<style>
.image-frame :global(img) {
    width: var(--size-full);
    height: var(--size-full);
    object-fit: cover;
}

.image-frame {
    object-fit: cover;
    width: 100%;
}

.image-container {
    display: flex;
    height: 100%;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    max-height: 100%;
}

.selectable {
    cursor: crosshair;
}

.icon-buttons {
    display: flex;
    position: absolute;
    top: 6px;
    right: 6px;
    gap: var(--size-1);
}
</style>
