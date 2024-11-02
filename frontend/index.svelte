<svelte:options accessors={true} />

<script context="module" lang="ts">
    export { default as BaseExample } from "./Example.svelte";
</script>

<script lang="ts">
    import type { Gradio, SelectData } from "@gradio/utils";
    import { Block } from "@gradio/atoms";
    import { StatusTracker } from "@gradio/statustracker";
    import type { LoadingStatus } from "@gradio/statustracker";
    import { AnnotatedImageData } from "./shared/components/ts";
    import ImageAnnotator from "./shared/components/svelte/image-annotator.svelte";
    // import { ListAnnotatedImageData } from "./shared/components/ts";

    // Required props of Gradio
    export let elem_id = "";
    export let elem_classes: string[] = [];
    export let visible = true;
    export let value: null | AnnotatedImageData = null;
    export let label: string;
    export let show_label: boolean;
    export let height: number | undefined;
    export let width: number | undefined;
    export let _selectable = false;
    export let container = true;
    export let scale: number | null = null;
    export let min_width: number | undefined = undefined;
    export let loading_status: LoadingStatus;
    export let interactive: boolean;

    export let calibration_ratio: number;

    export let label_list: string[];
    export let label_colors: string[];
    export let showDownloadButton: boolean;

    // Box properties
    export let boxAlpha: number; // Opacity of boxes
    export let box_min_size: number;
    export let handleSize: number;
    export let boxThickness: number;
    export let boxSelectedThickness: number;
    export let disableEditBoxes: boolean;
    export let singleBox: boolean;
    export let handlesCursor: boolean;

    export let gradio: Gradio<{
        change: never;
        error: string;
        edit: never;
        drag: never;
        upload: never;
        clear: never;
        select: SelectData;
        share: ShareData;
    }>;

    let dragging: boolean;
</script>

<Block
    {visible}
    variant={"solid"}
    border_mode={dragging ? "focus" : "base"}
    padding={true}
    {elem_id}
    {elem_classes}
    height={height || undefined}
    {width}
    allow_overflow={false}
    {container}
    {scale}
    {min_width}
>
    <StatusTracker
        autoscroll={gradio.autoscroll}
        i18n={gradio.i18n}
        {...loading_status}
    />

    <ImageAnnotator
        bind:value={value}
        bind:calibration_ratio
        on:change={() => gradio.dispatch("change")}
        selectable={_selectable}
        {interactive}
        i18n={gradio.i18n}
        {boxAlpha}
        labelList={label_list}
        labelColors={label_colors}
        boxMinSize={box_min_size}
        on:edit={() => gradio.dispatch("edit")}
        on:error={({ detail }) => {
            loading_status = loading_status || {};
            loading_status.status = "error";
            gradio.dispatch("error", detail);
        }}
        {label}
        {show_label}
        {handleSize}
        {boxThickness}
        {boxSelectedThickness}
        {disableEditBoxes}
        {singleBox}
        {showDownloadButton}
        {handlesCursor}
    ></ImageAnnotator>
</Block>
