# Browser access across harnesses

The harness supplies the reasoning loop. A browser backend supplies navigation, fresh page observations, actions and screenshots. MCP is one way to expose those capabilities; a permitted CLI called through Shell is another. Keep choosing and interpreting videos in the current agent rather than starting a second autonomous agent just to operate the browser.

## Choose an available route

1. **Existing browser tools:** Use the user-specified browser or connected tab. Follow that tool's session, permission and screenshot rules. No installation or CLI probing is needed if this route works.
2. **Shell plus image reading:** Look for `agent-browser`, `playwright-cli` or `browser-use` on PATH. The optional `scripts/doctor.py` reports them in `commands`, separately from Python packages. Read the selected CLI's help. Prefer attaching to the user's existing, authorized browser so their login and recommendations are retained. With agent-browser, use its supported `--auto-connect` or an explicitly provided connection endpoint. Do not replace that request with a fresh profile, incognito window or copied profile. Prefer an already installed backend; do not install all three.
3. **No CLI installed:** If package installation is allowed, prepare one CLI in a writable task directory. Respect the harness's approval requirements. Prefer the official package and keep package caches in the permitted directory.
4. **Browser launch is blocked:** Distinguish an unwritable cache from a process, socket or nested-sandbox restriction. Attaching to an already running, authorized Chrome can avoid launching another browser inside the command sandbox. If a host-side launcher or connector is still needed, prepare that narrow setup and explain the authorization. A separate profile is an option only when the user accepts it; it can require another login. Do not disable Chrome's sandbox or switch the harness to unrestricted execution as a default fix.
5. **No permitted browser route:** Explain the exact missing capability and continue with supplied links or local media where useful. This is a partial fallback, not successful feed browsing.

An installed Chrome app, a CLI version string, or `npx --no-install playwright --version` is not a browser smoke test. The last command checks a package without installing it; its failure does not prove that all browser automation is unavailable. Capture the actual error rather than truncating it to the first two lines.

## Use agent-browser through Shell

These examples use macOS/Linux shell syntax. On other systems, use the corresponding environment-variable and executable-path syntax. `$TODDLE_DATA` is the writable root selected for this task. Keep the session name and socket directory consistent across commands, and keep runtime files ignored by Git.

Inspect an existing installation:

```bash
agent-browser --version
agent-browser --help
```

Recent versions provide `agent-browser skills get core` for version-matched instructions. Use the commands supported by the installed version. If installation is needed and allowed:

```bash
export npm_config_cache="$TODDLE_DATA/cache/npm"
npm install --prefix "$TODDLE_DATA/browser-cli" agent-browser
```

Use the resulting executable under `$TODDLE_DATA/browser-cli/node_modules/.bin/` for later commands, or the existing PATH command. This does not require installing another skill. Reuse an installed Chrome/Chromium executable with `--executable-path` when appropriate; if a browser download is needed, follow the selected CLI's instructions and the harness's write permissions.

## Reuse the current Chrome session

Choose an unused task-specific CLI session name. This identifies the controller, not a replacement Chrome profile. `toddle-session` below is an example, not a shared global session. `AGENT_BROWSER_SOCKET_DIR` is supported by the tested agent-browser 0.27.0; consult the installed version if its behavior differs.

Current Chrome versions can allow connections through `chrome://inspect/#remote-debugging`. Enabling this setting and approving a debugging session are separate steps: Chrome can ask again for each new connection. Explain that it permits access to existing tabs and signed-in pages. Let the user handle required approvals; do not promise permanent approval or automatically dismiss the prompt. If the harness blocks the setting or connection, respect that boundary and ask for user action; do not reach the same blocked setting through another interface. Do not restart the user's browser with debugging flags or copy cookies to avoid that step.

```bash
export AGENT_BROWSER_SOCKET_DIR="$TODDLE_DATA/browser-sockets"
agent-browser --session toddle-session --auto-connect get title
agent-browser --session toddle-session tab list
```

Select the intended Douyin/Bilibili tab from the returned list, then inspect it. If no matching tab is open, create a tab in that same connected browser. Do not navigate an unrelated user tab. Keep the controller's session and socket directory consistent for later commands:

```bash
agent-browser --session toddle-session snapshot -i
agent-browser --session toddle-session screenshot "$TODDLE_DATA/home.png"
```

Open the screenshot with the harness's image-reading tool. An interactive snapshot helps locate controls; use a fuller or scoped snapshot when titles and captions are needed. Act only on refs or selectors observed in the current page, and obtain a new snapshot after navigation or dynamic updates. Use the same session for the next click or scroll. Preserve user-owned tabs and the existing Chrome process. Check the backend's detach behavior before cleanup; do not assume its `close` command only detaches from a connected personal browser.

If auto-discovery fails after the user has enabled and authorized the connection, inspect the backend's connection diagnostics. An explicit endpoint supplied by the user or published by that Chrome instance can be used with `--cdp`; do not guess ports or reuse a different browser's endpoint. If a controller retains failed launch settings, start a fresh CLI controller session with the correct attachment settings. This must not launch another Chrome or reset the user's profile. Keep connection metadata private.

Keep one established connection for the browsing session and serialize commands through it. Do not attach or probe again for every screenshot, click or status check. Repeated reconnections can cause repeated Chrome permission dialogs; if those appear, stop connection retries and inspect the controller lifecycle. A timeout does not establish that a running operation is finished. Before replacing a stuck controller, stop its active requests and explain any new approval the replacement will require. See [Chrome's connection-approval behavior](https://developer.chrome.com/blog/chrome-devtools-mcp-debug-your-browser-session).

For video evidence, prefer a screenshot of the observed player container when the backend supports element screenshots. Inspect the resulting image; a successful file write is not proof that the video rendered. After seeking, verify the actual player time and readiness before capturing, and record the actual time rather than only the requested one. A fixed sleep alone does not prove that seeking completed. Keep captures in new directories and propagate navigation/capture errors instead of printing an unconditional success marker.

`agent-browser --profile Default` is not the same as attaching: version 0.27.0 copies the named Chrome profile to a temporary directory. Do not use it for a request to operate the user's current Chrome. `--profile /path` creates or uses a separate profile and may require login; use it only if the user accepts that alternative.

For a browser instance created for the task with the user's agreement, close only that owned instance when finished:

```bash
agent-browser --session toddle-session close
```

Do not use `close --all` or kill unrelated browser processes. Unix socket paths have platform length limits; if a long workspace path prevents startup, use a shorter permitted runtime directory and retain it for the task.

## Browse without taking desktop focus

Background browsing means the agent can navigate, inspect frames and advance while the user works in another app. Do not call `bringToFront`, `Page.bringToFront`, `Target.activateTarget` or OS activation commands as a playback fix. Selecting a page in a controller must not be assumed to leave the desktop unchanged; verify the backend's behavior. Keep using the same page and connection.

If playback stalls, inspect the actual player before changing the browser setup:

1. Check the current page, visible player, play/pause state and actual time. Exclude hidden preloaded players. Observe again after a short playback interval; a resolved `play()` call is not evidence of advancing video.
2. Inspect a screenshot. A black player may be a loading state, an overlay or picture-in-picture. If the page offers “点击可退出小窗播放”, use the matching control in the current viewport, then inspect again. Do not click an offscreen duplicate.
3. If the site pauses because its tab is hidden, a backend with an already authorized CDP connection can try target-scoped `Emulation.setFocusEmulationEnabled` with `enabled: true`. This emulates page focus; it does not require activating Chrome's desktop window. [Chrome documents](https://developer.chrome.com/docs/devtools/rendering/apply-effects#emulate_a_focused_page) that it changes `document.visibilityState` to `visible`, so that property alone cannot verify background operation. Verify advancing video frames while another app remains in front. This is a playback aid, not a guarantee for every site.
4. Reuse that logical target session; do not establish another browser connection for each action. Disable the emulation when the browsing session ends, and detach only the session you created. Follow the harness's rules if it does not expose this capability.

When seeking fails, watch a short interval at normal playback speed and capture its actual times. Some Douyin media elements report `Infinity` while the current player displays a finite duration; this alone proves neither a live stream nor a playable ordinary video. Check the current image, captions and player state. Use an observed UI duration with its source labeled, or report duration as unknown. Do not convert a requested seek time into evidence when the player did not reach it. Label a few observed seconds as sampled coverage, and gather more evidence when a conclusion needs it.

Treat a route as usable only after navigation, image inspection, advancement to another work and saving a viewing record succeed. Test interest updates as well as browser commands. If a backend needs more small steps or larger snapshots, accept that cost before reducing the requested coverage. Choose by available capabilities and permissions, not the model vendor or its country of origin.

## Playwright CLI alternative

[Playwright CLI](https://github.com/microsoft/playwright-cli) can attach directly to the authorized Chrome instance without MCP or a new profile. Read the installed version's help; these commands were exercised with `@playwright/cli` 0.1.19. If needed, install it under a writable task directory using `npm install --prefix "$TODDLE_DATA/playwright-cli" @playwright/cli`, with the npm cache redirected as above. Use that directory's `node_modules/.bin/playwright-cli` executable for subsequent commands.

Prepare a private JSON config with `outputDir` inside the selected data directory, `outputMode: "file"` and `browser.contextOptions.viewport: null`. `$TODDLE_CDP_ENDPOINT` below means the authorized endpoint published by the intended Chrome instance; keep it and connection logs private.

```bash
playwright-cli -s=toddle-session attach --cdp="$TODDLE_CDP_ENDPOINT" --config="$TODDLE_DATA/browser-config.json"
playwright-cli -s=toddle-session tab-list
```

Attach once, let the user handle Chrome's approval, then select the intended page from the fresh list using `tab-select`. Reuse `-s=toddle-session` for `snapshot`, `eval`, `mousemove`, `mousewheel`, `screenshot` and `run-code`. `goto` navigates the selected page; it does not choose the correct user tab for you. Use `detach` at the end to leave the external browser running. Inspect each command's exit status and the returned page state.

In a workspace-only macOS sandbox, version 0.1.19 still writes controller state under `~/Library/Caches/ms-playwright` even when `XDG_CACHE_HOME` is set. The tested package exposes `PWTEST_DAEMON_SESSION_DIR` and `PWTEST_SERVER_REGISTRY` to redirect its controller and registry directories. These are internal, version-specific hooks: inspect the installed implementation before using them, and do not assume later releases preserve them. Set both to short, permitted, task-specific paths before attachment and retain them for every command. Redirecting these files does not relax the sandbox or authorize a browser connection.

For the optional focus emulation described above, `run-code` can create a target session on the existing Playwright connection and retain it on the controller's Page object:

```javascript
async (page) => {
  if (!page.__toddleFocusSession)
    page.__toddleFocusSession = await page.context().newCDPSession(page);
  await page.__toddleFocusSession.send('Emulation.setFocusEmulationEnabled', {enabled: true});
}
```

This property belongs to the controller, not the webpage. Apply it only to the intended browsing page. At cleanup, send the same method with `enabled: false`, detach that target session and delete the property before detaching the CLI. Never substitute a browser or OS activation call.

## When the browser must run outside the command sandbox

In a macOS workspace-write test using dsh's Seatbelt profile, the CLI could execute but Chrome's own sandbox initialization failed. Redirecting caches did not resolve that launch failure. Prefer an approved connection to the user's running Chrome. Another architecture, when the user agrees to a separate browser, is a dedicated browser service on the host with the agent's sandboxed CLI connecting to it. The harness and Chrome keep their existing sandbox settings.

Prepare a concrete launch command for the user or the harness's approved host-side tool to run. Use an independent profile and session, with runtime files under the permitted task directory. Do not silently run a denied launch outside the sandbox, attach without authorization, export cookies, or open a debugging endpoint on a public interface. Avoid inherited CLI configuration that would select another profile or cloud service. A host-side launch, only for this accepted alternative, can use:

```bash
export AGENT_BROWSER_SOCKET_DIR="$TODDLE_DATA/browser-sockets"
agent-browser --session toddle-session --profile "$TODDLE_DATA/browser-profiles/toddle-session" \
  --headed open https://www.bilibili.com/
```

Subsequent sandboxed commands use the same socket directory and session name to reach that service.

Only call the connection usable after a real navigation, page read and screenshot succeed from the constrained client. An isolated profile will not contain the user's platform login. If personalized recommendations require it, let the user sign in through that browser; do not copy a personal browser's profile or credentials. Existing approved browser connectors remain preferable when they already provide the required session.

If host-side authorization is unavailable, preserve a clear setup handoff and report the blocker. Do not claim support for a harness merely because it has Shell.

## Verification and other backends

Verify a backend with an accessible page: open it, read its title or visible content, capture and inspect an image, then perform one observed navigation or scroll and read the updated state. Distinguish a public-page smoke test from access to a logged-in recommendation feed. Tool names and installation paths are capabilities to discover, not a fixed list of supported model vendors.

- [agent-browser](https://github.com/vercel-labs/agent-browser) is the primary CLI example here; its basic browser commands do not need another LLM.
- [Playwright CLI](https://github.com/microsoft/playwright-cli) provides Shell-driven browser actions independently of Playwright MCP. Follow its own session and output-directory options.
- [Browser Use](https://github.com/browser-use/browser-use#which-browser-use-do-i-need) also offers a CLI route. Keep the existing harness in charge when using it; an additional autonomous agent or cloud service is not a prerequisite for toddle.

Do not interchange flags across these tools. Keep setup details in this reference and load only the route needed for the current environment.

Version-specific input caveat: in agent-browser 0.27.0, the `mouse wheel` parser sends only deltas, and the handler defaults the event coordinates to `(0,0)` rather than reusing the preceding mouse move. This was observed during the Douyin test; consult the [parser](https://github.com/vercel-labs/agent-browser/blob/v0.27.0/cli/src/commands.rs) and [handler](https://github.com/vercel-labs/agent-browser/blob/v0.27.0/cli/src/native/actions.rs) when diagnosing that version. Use a verified input route or another permitted backend instead of repeating the same failed wheel command. Do not interpret an unchanged preloaded video ID as proof that the visible page did not change.
