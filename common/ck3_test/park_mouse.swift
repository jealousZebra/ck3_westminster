// Moves the mouse pointer over open sea right of the windows, so no tooltip shows in a screenshot.
// A real mouse-moved event, so the game notices (a plain warp doesn't clear its hover).
import CoreGraphics
let b = CGDisplayBounds(CGMainDisplayID())
let p = CGPoint(x: b.width * 0.88, y: b.height * 0.28)
CGWarpMouseCursorPosition(p)
CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left)?.post(tap: .cghidEventTap)
