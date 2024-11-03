import type { FileData } from "@gradio/client";
import Box from "./box";

/**
 * Represents annotated image data.
 */
export default class AnnotatedImageData {
  image: FileData;
  boxes: Box[] = [];
  calibration_ratio: [number, number] = [0, 0];
}
