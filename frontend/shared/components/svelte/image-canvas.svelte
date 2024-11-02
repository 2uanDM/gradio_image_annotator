<script lang="ts">
	import {
	  resolve_wasm_src
	} from "@gradio/wasm/svelte";
	import {
	  createEventDispatcher
	} from "svelte";
	import type {
	  HTMLImgAttributes
	} from "svelte/elements";
	import {
	  AnnotatedImageData
	} from "../ts";
	import Canvas from "./canvas.svelte";

interface Props extends HTMLImgAttributes {
    "data-testid" ? : string;
}

export let value: AnnotatedImageData | null | undefined;
export let src: HTMLImgAttributes["src"] = undefined;
export let interactive: boolean;

export let calibration_ratio: [number, number] = [0, 0];

export let boxAlpha: number;
export let labelList: string[];
export let labelColors: string[];
export let boxMinSize: number;
export let handleSize: number;
export let boxThickness: number;
export let boxSelectedThickness: number;
export let disableEditBoxes: boolean;
export let handlesCursor: boolean;

let resolved_src: typeof src;

// The `src` prop can be updated before the Promise from `resolve_wasm_src` is resolved.
// In such a case, the resolved value for the old `src` has to be discarded,
// This variable `latest_src` is used to pick up only the value resolved for the latest `src` prop.
let latest_src: typeof src;
$: {
    // In normal (non-Wasm) Gradio, the `<img>` element should be rendered with the passed `src` props immediately
    // without waiting for `resolve_wasm_src()` to resolve.
    // If it waits, a blank image is displayed until the async task finishes
    // and it leads to undesirable flickering.
    // So set `src` to `resolved_src` here.
    resolved_src = src;

    latest_src = src;
    const resolving_src = src;
    resolve_wasm_src(resolving_src).then((s) => {
        if (latest_src === resolving_src) {
            resolved_src = s;
        }
    });
}

const dispatch = createEventDispatcher < {
    change: undefined;
    calibrated: [number, number];
} > ();
</script>

<Canvas
    bind:value={value}
    calibration_ratio={calibration_ratio}
    imageUrl={resolved_src}
    {interactive}
    {boxAlpha}
    choices={labelList}
    choicesColors={labelColors}
    {boxMinSize}
    {handleSize}
    {boxThickness}
    {boxSelectedThickness}
    {disableEditBoxes}
    {handlesCursor}
    on:change={() => dispatch("change")}
    on:calibrated={(event) => dispatch("calibrated", event.detail)}
    />
