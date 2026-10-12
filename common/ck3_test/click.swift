// Clicks the left mouse button at a point given as fractions of the main screen (0-1), so coordinates read
// off a resized screenshot work at any resolution:  click 0.234 0.419
// With a third argument, scrolls the wheel there instead (negative zooms the game's map out):  click 0.5 0.5 -10
// Used to drive the game's menus (for example starting a new game) when there is no save to load.
import CoreGraphics
import Foundation
let args = CommandLine.arguments
guard args.count >= 3, let fx = Double(args[1]), let fy = Double(args[2]) else {
	print("usage: click <x fraction> <y fraction> [scroll lines]"); exit(1)
}
let b = CGDisplayBounds(CGMainDisplayID())
let p = CGPoint(x: b.width * fx, y: b.height * fy)
func post(_ t: CGEventType) { CGEvent(mouseEventSource: nil, mouseType: t, mouseCursorPosition: p, mouseButton: .left)?.post(tap: .cghidEventTap) }
post(.mouseMoved); usleep(150_000)
if args.count >= 4, let lines = Int32(args[3]) {
	let step: Int32 = lines < 0 ? -1 : 1
	for _ in 0..<abs(lines) {
		CGEvent(scrollWheelEvent2Source: nil, units: .line, wheelCount: 1, wheel1: step, wheel2: 0, wheel3: 0)?.post(tap: .cghidEventTap)
		usleep(60_000)
	}
} else {
	post(.leftMouseDown); usleep(80_000)
	post(.leftMouseUp)
}
