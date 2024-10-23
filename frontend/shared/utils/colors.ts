/**
     * Convert hex color to rgb
     * @param hex string
     * @returns string
     */
export function colorHexToRGB(hex: string): string {
    var r = parseInt(hex.slice(1, 3), 16),
        g = parseInt(hex.slice(3, 5), 16),
        b = parseInt(hex.slice(5, 7), 16);
    return "rgb(" + r + ", " + g + ", " + b + ")";
}

/**
 * Convert hex color to rgba
 * @param rgba string
 * @returns string
 */
export function colorRGBAToHex(rgba: string): string {
    const rgbaValues = rgba.match(/(\d+(\.\d+)?)/g);

    if (!rgbaValues) {
        throw new Error("Invalid rgba value");
    }

    const r = parseInt(rgbaValues[0]);
    const g = parseInt(rgbaValues[1]);
    const b = parseInt(rgbaValues[2]);
    const hex =
        "#" + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
    return hex;
}