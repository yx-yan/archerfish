// Draw the menu bar template icons: the logo's waveform, one variant per state.
// Usage: swift macos/make_menubar_icons.swift src/quoth/icons

import AppKit

let size = 40  // 20 pt at 2x.
let heights: [CGFloat] = [10, 20, 28, 15]
let cursorHeight: CGFloat = 32
let width: CGFloat = 4
let step: CGFloat = 7
let left: CGFloat = 20 - (step * 4 + width) / 2

func bar(_ context: CGContext, x: CGFloat, y: CGFloat, height: CGFloat) {
    let rect = CGRect(x: x, y: y, width: width, height: height)
    context.addPath(CGPath(roundedRect: rect, cornerWidth: width / 2, cornerHeight: width / 2, transform: nil))
    context.fillPath()
}

func fill(_ context: CGContext, alpha: CGFloat) {
    context.setFillColor(CGColor(gray: 0, alpha: alpha))
}

func waveform(_ context: CGContext, alpha: CGFloat, heights: [CGFloat]) {
    fill(context, alpha: alpha)
    for (index, height) in heights.enumerated() {
        bar(context, x: left + step * CGFloat(index), y: 20 - height / 2, height: height)
    }
}

func cursor(_ context: CGContext) {
    fill(context, alpha: 1)
    bar(context, x: left + step * 4, y: 20 - cursorHeight / 2, height: cursorHeight)
}

let icons: [String: (CGContext) -> Void] = [
    "ready": { context in
        waveform(context, alpha: 1, heights: heights)
        cursor(context)
    },
    "loading": { context in
        waveform(context, alpha: 0.35, heights: heights)
        cursor(context)
    },
    "recording": { context in
        // A solid tile with the waveform cut out, so it reads at a glance.
        fill(context, alpha: 1)
        let tile = CGRect(x: 0, y: 0, width: 40, height: 40).insetBy(dx: 1, dy: 1)
        context.addPath(CGPath(roundedRect: tile, cornerWidth: 9, cornerHeight: 9, transform: nil))
        context.fillPath()
        context.setBlendMode(.clear)
        waveform(context, alpha: 1, heights: heights.map { $0 * 0.85 })
        fill(context, alpha: 1)
        bar(context, x: left + step * 4, y: 20 - 13, height: 26)
    },
    "working": { context in
        waveform(context, alpha: 0.35, heights: [4, 4, 4, 4])
        cursor(context)
    },
    "warning": { context in
        // The cursor splits into an exclamation mark.
        waveform(context, alpha: 0.35, heights: heights)
        fill(context, alpha: 1)
        bar(context, x: left + step * 4, y: 12, height: 24)
        bar(context, x: left + step * 4, y: 4, height: 4)
    },
]

let directory = URL(fileURLWithPath: CommandLine.arguments[1])
try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
for (name, draw) in icons {
    let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size, bitsPerSample: 8,
        samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0
    )!
    draw(NSGraphicsContext(bitmapImageRep: rep)!.cgContext)
    try rep.representation(using: .png, properties: [:])!
        .write(to: directory.appendingPathComponent("\(name).png"))
}
