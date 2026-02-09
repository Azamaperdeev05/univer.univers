/**
 * @typedef IconParams
 * @type {object}
 * @property {string | ((size: number) => string)} [path]
 * @property {string} [type]
 * @property {"maskable" | "badge" | "any"} [purpose]
 */

import { routes } from "./pages"

/**
 *
 * @param {number} size
 * @param {IconParams} params
 * @returns
 */
const icon = (
    size,
    {
        path = (size) => `images/icons/${size}.png`,
        type = "image/png",
        purpose,
    } = {}
) => ({
    src: typeof path === "string" ? path : path(size),
    sizes: `${size}x${size}`,
    type,
    purpose,
})

/** @param {string} name */
const mobileScreenshot = (name) => ({
    src: `images/screens/mobile/${name}.JPG`,
    type: "image/jpeg",
    sizes: "1080x1920",
    form_factor: "narrow",
})
/** @param {string} name */
const desktopScreenshot = (name) => ({
    src: `images/screens/desktop/${name}.png`,
    type: "image/png",
    sizes: "1920x1080",
    form_factor: "wide",
})

export default {
    theme_color: "#4f46e5",
    background_color: "#fff",
    display: "standalone",
    scope: "/",
    start_url: routes.home,
    lang: "kk",
    name: "Univer",
    short_name: "Univer",
    description:
        "Бағаларды, сабақ кестесін, емтихандарды және студент туралы басқа да ақпаратты көруге арналған қосымша.",
    icons: [
        icon(64),
        icon(128),
        icon(192),
        icon(512),
        icon(512, {
            purpose: "maskable",
            path: "images/icons/maskable.png",
        }),
    ],
    screenshots: [
        mobileScreenshot("schedule"),
        mobileScreenshot("calculator"),
        mobileScreenshot("marks"),
        mobileScreenshot("UMKD"),
        mobileScreenshot("menu"),
        mobileScreenshot("setting"),
        desktopScreenshot("schedule"),
        desktopScreenshot("attendance"),
        desktopScreenshot("profile"),
    ],
}
