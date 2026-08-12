"""test-editor-e2e.py — E2E tests for HTML Deck WYSIWYG Editor via Playwright.

Usage: python test-editor-e2e.py [--target-dir <path>] [--port 8080]
"""

import argparse, json, os, subprocess, sys, time
from pathlib import Path

CONTAINER = Path(__file__).resolve().parent.parent


def start_server(target_dir, port):
    """Start serve.py and return the process."""
    proc = subprocess.Popen(
        [sys.executable, str(CONTAINER / "serve.py"), str(target_dir),
         "--port", str(port), "--no-browser"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(1.5)
    # Verify server is up
    for _ in range(10):
        try:
            import urllib.request
            urllib.request.urlopen(f"http://localhost:{port}/", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Server failed to start")
    return proc


def main():
    parser = argparse.ArgumentParser(description="E2E tests for HTML Deck Editor")
    parser.add_argument("--target-dir", default=None,
                        help="Target directory with slides-config.json")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    # Auto-detect target directory
    if args.target_dir:
        target_dir = Path(args.target_dir)
    else:
        # Look for common target dirs
        candidates = sorted(CONTAINER.parent.parent.glob("2*信息*/20-html/v-*"))
        if candidates:
            target_dir = candidates[-1]
        else:
            target_dir_tests = CONTAINER.parent.parent / "28-信息压缩效率思考" / "20-html" / "v-01"
            if target_dir_tests.exists():
                target_dir = target_dir_tests
            else:
                print("Error: No target directory found. Use --target-dir.")
                sys.exit(1)

    print(f"Target: {target_dir}")
    print(f"Port: {args.port}")

    # Start server
    print("Starting server...")
    server_proc = start_server(target_dir, args.port)
    base_url = f"http://localhost:{args.port}"

    passed = 0
    failed = 0
    errors = []

    def test(name, fn):
        nonlocal passed, failed
        try:
            fn()
            passed += 1
            print(f"  PASS  {name}")
        except Exception as e:
            failed += 1
            msg = f"{name}: {e}"
            errors.append(msg)
            print(f"  FAIL  {name}: {e}")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(f"{base_url}/#ch01/01-cover", wait_until="networkidle")
            time.sleep(0.5)

            # ── Test 1: Page loads ──
            test("Page loads correctly", lambda: (
                page.wait_for_selector("#deck", timeout=5000),
                page.wait_for_selector("#editor-toggle-btn", timeout=5000)
            ))

            # ── Test 2: Editor activation ──
            test("Editor activates on toggle", lambda: (
                page.click("#editor-toggle-btn"),
                page.wait_for_selector("#editor-panel", timeout=3000),
                assert page.locator("#editor-toggle-btn").inner_text() == "编辑中…"
            ))

            # ── Test 3: Element selection ──
            test("Element selection on click", lambda: (
                page.locator(".slide.active .panel").first.click(),
                page.wait_for_selector("#editor-el-label.visible", timeout=3000),
                assert page.locator("#editor-el-label").is_visible()
            ))

            # ── Test 4: CSS property change ──
            test("CSS property change via color input", lambda: (
                page.locator('.editor-color-input[data-prop="color"]').first.fill("#ff0000"),
                page.locator('.editor-color-input[data-prop="color"]').first.dispatch_event("input"),
                time.sleep(0.2),
                # Check undo stack has an entry
                assert page.evaluate("() => window.__undoManager.canUndo()")
            ))

            # ── Test 5: Undo/Redo ──
            test("Undo reverts color change", lambda: (
                page.keyboard.press("Control+z"),
                time.sleep(0.2),
                assert page.evaluate("() => window.__undoManager.canRedo()")
            ))
            test("Redo re-applies color change", lambda: (
                page.keyboard.press("Control+y"),
                time.sleep(0.2),
                assert page.evaluate("() => window.__undoManager.canUndo()")
            ))

            # ── Test 6: Add component ──
            test("Add component via palette", lambda: (
                page.click(".palette-toggle"),
                time.sleep(0.2),
                # Count existing panels
                init_count := page.evaluate("() => document.querySelectorAll('.slide.active .panel').length"),
                page.click('.palette-item[data-type="panel"]'),
                time.sleep(0.3),
                new_count := page.evaluate("() => document.querySelectorAll('.slide.active .panel').length"),
                assert new_count == init_count + 1
            ))

            # ── Test 7: Delete element ──
            test("Delete selected element", lambda: (
                page.locator(".slide.active .panel").last.click(),
                time.sleep(0.2),
                page.click('.editor-btn[data-action="delete-el"]'),
                time.sleep(0.3),
                # Undo should bring it back
                page.keyboard.press("Control+z"),
                time.sleep(0.2),
                assert page.evaluate("() => !window.__undoManager.canRedo()")
            ))

            # ── Test 8: Clone element ──
            test("Clone selected element", lambda: (
                page.locator(".slide.active .panel").last.click(),
                time.sleep(0.1),
                init_count := page.evaluate("() => document.querySelectorAll('.slide.active .panel').length"),
                page.click('.editor-btn[data-action="clone-el"]'),
                time.sleep(0.3),
                new_count := page.evaluate("() => document.querySelectorAll('.slide.active .panel').length"),
                assert new_count == init_count + 1
            ))

            # ── Test 9: Text editing ──
            test("Double-click starts text editing", lambda: (
                page.locator(".slide.active p").first.dblclick(),
                time.sleep(0.2),
                assert page.evaluate("() => document.querySelector('.slide.active [contenteditable=\"true\"]") is not None)
            ))
            # Clean up text edit
            page.keyboard.press("Escape")
            time.sleep(0.1)

            # ── Test 10: Exit dialog appears ──
            test("Exit confirm dialog appears with pending changes", lambda: (
                page.click("#editor-toggle-btn"),  # deactivate
                time.sleep(0.3),
                dialog := page.locator("#editor-exit-dialog"),
                assert dialog.is_visible(),
                # Dismiss
                page.click('.editor-dialog-btn.cancel'),
                time.sleep(0.2)
            ))

            browser.close()

    except ImportError:
        print("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        print("Skipping E2E tests.")
        server_proc.terminate()
        print(f"\nRESULTS: {passed} passed, {failed} failed")
        sys.exit(0 if failed == 0 else 1)
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()

    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    if errors:
        print(f"\nFAILURES:")
        for i, e in enumerate(errors):
            print(f"  {i+1}) {e}")
        sys.exit(1)
    else:
        print("All E2E tests passed.")


if __name__ == "__main__":
    main()
