# Accessibility Considerations for GeneWeb‑Python

> This document outlines practical, testable accessibility requirements and practices for the GeneWeb‑Python project (a modernization effort of the GeneWeb genealogy software with a web interface). The goal is to ensure that people with disabilities can use the application effectively, whether self‑hosted or deployed as a web service.

## Scope & Principles

- **Audience:** end‑users browsing and editing genealogical data; admins configuring servers; contributors building UI and API features.
- **Standards target:** WCAG **2.2 Level AA** (minimum), align with **EN 301 549** for public‑sector deployments. Follow **WAI‑ARIA** for semantics and **ATAG** principles for authoring flows.
- **Platforms:** desktop and mobile web (progressive enhancement), including offline/low‑connectivity modes where applicable.

## User Needs to Address

- **Blind/low‑vision:** screen‑reader compatibility, keyboard access, strong focus indication, scalable text (200–400%) with reflow, high contrast.
- **Color‑vision deficiency:** do not rely on color alone; provide patterns, labels, icons.
- **Motor impairments:** full keyboard operability, generous hit areas, avoid time‑limited tasks, support pointer alternatives.
- **Cognitive/learning:** clear language, consistent layouts, undo/cancel, avoid content that unexpectedly moves; provide chunked forms and inline help.
- **Deaf/hard‑of‑hearing:** captions and transcripts for multimedia.
- **Photosensitive users:** avoid animations > 3 flashes/sec; honor “prefers‑reduced‑motion”.

## Functional Requirements (Do/Don’t)

### 1) Navigation & Focus
- **Do:** Provide a visible focus ring on all interactive elements; ensure a logical **Tab** order that follows the visual flow.
- **Do:** Add a “Skip to main content” link as the first focusable element.
- **Do:** Manage focus on route changes and dialogs (`focus()` the first meaningful control).
- **Don’t:** Trap focus; all modals must cycle focus and close with **Esc**.

### 2) Semantics & ARIA
- **Do:** Use native HTML landmarks (`<header>`, `<nav>`, `<main>`, `<footer>`) and headings in order (`h1…h6`).
- **Do:** Use `aria-live="polite"` for non‑blocking toasts (e.g., “Person saved”). Use `role="alert"` only for critical errors.
- **Don’t:** Add ARIA where native semantics suffice.

### 3) Color, Contrast, and Theming
- **Do:** Meet contrast ≥ **4.5:1** (text) and **3:1** (UI components). Provide a built‑in high‑contrast theme and dark mode.
- **Do:** Use tokenized colors; avoid encoding meaning with color alone (e.g., add icons or text).

### 4) Typography & Reflow
- **Do:** Support zoom to **400%** without loss of content or functionality; content should reflow to a single column where needed.
- **Do:** Respect user font settings and OS text scaling (no `!important` locks).

### 5) Keyboard & Shortcuts
- **Do:** Every action must be reachable by keyboard; provide visible accelerator hints.
- **Do:** If adding global shortcuts, require a modifier (e.g., `Alt+Shift+S`) and offer a way to remap/disable.

### 6) Forms, Tables, and Data Entry
- **Do:** Label every input (`<label for>` or `aria-labelledby`), provide helpful error text and programmatic error states.
- **Do:** Group related fields (`<fieldset><legend>`). Use input masks that do **not** block assistive tech.
- **Do:** For data tables (e.g., people lists, events), mark headers with `<th scope>`, enable row/column navigation, and provide responsive stacked views.
- **Don’t:** Use placeholder text as the only label.

### 7) Media & Images
- **Do:** Provide **alt text** for informative images; mark decorative images with empty `alt`.
- **Do:** Provide captions for videos and transcripts for audio. Offer audio descriptions where visuals convey essential meaning.
- **Don’t:** Autoplay audio/video; if absolutely necessary, mute by default and provide controls.

### 8) Feedback, Errors, and Status
- **Do:** Show inline error messages next to the relevant field and summarize errors at the top.
- **Do:** Use non‑color indicators (icons, weights, text) for status (e.g., “Imported”, “Conflict”, “Duplicate”).

### 9) Motion & Timing
- **Do:** Respect `prefers-reduced-motion`; reduce parallax/transitions and freezing animated GIFs/SVGs where possible.
- **Do:** Avoid time limits; if needed, provide **pause/extend** functionality.

### 10) Authentication & Security Challenges
- **Do:** Provide non‑visual alternatives to CAPTCHA (e.g., logic questions, passkeys, email link). Ensure MFA flows are keyboard and SR accessible.

### 11) Internationalization
- **Do:** Use correct `lang` attributes; update them for localized strings. Format dates/numbers using locale‑aware APIs.
- **Do:** Keep a translation glossary; avoid culture‑specific idioms in UI strings.

### 12) Documents & Exports
- **Do:** Ensure exported documents (PDF/HTML) contain proper tags and reading order; supply CSV as a fallback for screen‑reader friendly analysis.
- **Do:** For family trees/charts, provide text‑only summaries and keyboard navigable tree views with SR‑friendly labels.

## Implementation Notes (Web UI)

- **Routing:** On SPA route changes, set focus to `<h1>` or the main landmark and announce page title.
- **Components:** Centralize accessible components (Button, Link, Modal, Menu, Tabs, Table, Toast) with baked‑in a11y.
- **Forms:** Adopt a form schema that returns both constraints and localized messages; validate on blur and on submit.
- **Dialog Example:**

```html
<button aria-haspopup="dialog" aria-controls="edit-person">Edit</button>
<div role="dialog" id="edit-person" aria-modal="true" aria-labelledby="dlg-title" hidden>
  <h2 id="dlg-title">Edit person</h2>
  <!-- First focusable element should receive focus when opened -->
  <button>Save</button>
  <button>Cancel</button>
</div>
```

## Testing & QA

**Tooling (automated):**
- `axe-core`/browser extensions and CI runners, `pa11y`, Lighthouse CI budgets.
- ESLint rules for JSX a11y (or equivalent), type‑safe ARIA attributes.

**Manual AT matrix (minimum):**
- **Windows:** NVDA + Firefox/Chrome; **JAWS** (if available).
- **macOS/iOS:** VoiceOver + Safari.
- **Android:** TalkBack + Chrome.

**Core scenarios to test each release:**
1. Navigate the home page and a typical person record **with keyboard only**.
2. Create/edit a person: labels read correctly, error states announced, focus returns to the trigger.
3. Import/export data: progress uses live regions; results summarized in text.
4. Theme switch: contrast remains valid; focus ring visible in all states.
5. Zoom at 200–400%: content reflows, no horizontal scroll for text blocks.

**CI policy:**
- Block merges on WCAG “serious/critical” violations detected by automated checks.
- Accessibility issues carry the `a11y` label with severity/impact/assistive‑tech tags.
- Maintain a changelog of a11y fixes and regression tests.

## Content Guidelines

- Prefer simple, direct language; avoid jargon where possible.
- Use consistent page structure: title (`h1`), lead paragraph, actions area, main content, related links.
- Provide examples and inline help close to the task.

## Governance

- Assign an **Accessibility Champion** per feature team.
- Run **design reviews** with an a11y checklist and quick prototyping in Storybook (or equivalent).
- Schedule **quarterly audits** and publish results/issues transparently.

## Definition of Done (a11y)

A feature is “done” when:
- Keyboard path verified (no traps, proper order, visible focus).
- Screen‑reader announces role, name, state for all controls.
- Contrast and zoom criteria met.
- Automated scans pass; manual spot‑checks recorded.
- User help and error messages localized and understandable.

---

*Questions or improvements? Open an issue with the `a11y` label and include the page URL, browser/OS, assistive tech (if any), and steps to reproduce.*
