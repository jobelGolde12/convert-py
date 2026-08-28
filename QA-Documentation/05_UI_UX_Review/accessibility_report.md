# Accessibility Report

## Summary

| Severity | Count | Resolved |
|----------|-------|----------|
| Critical | 0 | 0 |
| Major | 0 | 0 |
| Minor | 2 | 0 |
| Informational | 3 | 0 |

## Findings

### A11Y-001: Skip link target may not receive focus

```
Finding ID: A11Y-001
WCAG Area: 2.4.1 Bypass Blocks
Severity: Minor
Affected Page: All (base.html)
Affected Element: <a href="#main" class="skip-link">
Problem: The skip link is present but its CSS visibility behavior is not
  confirmed to work correctly with all screen readers. The #main target
  exists on <main id="main">.
Expected Behavior: Skip link should be visible on focus and move focus to main content
Recommended Fix: Verify skip-link CSS includes :focus-visible styles
Implementation Status: OPEN
Verification Status: NOT TESTED
```

### A11Y-002: Form select lacks visible label

```
Finding ID: A11Y-002
WCAG Area: 1.3.1 Info and Relationships
Severity: Minor
Affected Page: /convert (convert.html)
Affected Element: <select id="target-select">
Problem: The label "Convert to" is present as a <label> element associated
  via for="target-select", and there is an aria-describedby on a sr-only
  span. This is correct implementation.
Expected Behavior: Label is associated and accessible
Recommended Fix: No fix needed — implementation is correct
Implementation Status: VERIFIED (not an issue)
Verification Status: VERIFIED
```

### A11Y-003: Progress bar uses aria-live correctly

```
Finding ID: A11Y-003
WCAG Area: 4.1.3 Status Messages
Severity: Informational
Affected Page: /convert (convert.html)
Affected Element: <div id="progress-wrap" aria-live="polite">
Problem: Progress updates are announced to screen readers via aria-live="polite".
  The progressbar role has aria-valuemin, aria-valuemax, aria-valuenow.
Expected Behavior: Screen reader announces progress changes
Recommended Fix: No fix needed — correct implementation
Implementation Status: VERIFIED
Verification Status: VERIFIED
```

### A11Y-004: Dark mode toggle has proper ARIA

```
Finding ID: A11Y-004
WCAG Area: 4.1.2 Name, Role, Value
Severity: Informational
Affected Page: All (base.html)
Affected Element: <button id="theme-toggle">
Problem: Button has aria-label and aria-pressed that update dynamically
  via JavaScript. Correct implementation.
Expected Behavior: Toggle announces current state
Recommended Fix: No fix needed
Implementation Status: VERIFIED
Verification Status: VERIFIED
```

### A11Y-005: Mobile navigation has proper ARIA

```
Finding ID: A11Y-005
WCAG Area: 4.1.2 Name, Role, Value
Severity: Informational
Affected Page: All (base.html)
Affected Element: <button id="menu-toggle">, <div id="mobile-nav">
Problem: Menu toggle has aria-expanded, aria-controls. Mobile nav links
  are in a <nav aria-label="Mobile">. Escape key closes menu and returns
  focus to toggle. First link receives focus on open.
Expected Behavior: Accessible mobile navigation
Recommended Fix: No fix needed — excellent implementation
Implementation Status: VERIFIED
Verification Status: VERIFIED
```

## Positive Findings

The application demonstrates strong accessibility practices:
- Semantic HTML with `<header>`, `<main>`, `<footer>`, `<nav>` landmarks
- Skip link for keyboard navigation
- ARIA labels on interactive elements
- `aria-live` regions for dynamic content
- Keyboard support on dropzone (Enter/Space triggers file picker)
- Screen reader text via `.sr-only` class
- Proper heading hierarchy (h1 → h2 → h3)
- Form labels associated via `for` attribute
- `role="progressbar"` with value attributes
- `aria-hidden="true"` on decorative SVGs
