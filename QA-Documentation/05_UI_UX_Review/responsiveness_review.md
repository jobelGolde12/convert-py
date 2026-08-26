# Responsiveness Review

## Breakpoints

| Breakpoint | Usage |
|-----------|-------|
| < 768px | Mobile: container padding, section padding, footer grid |
| < 860px | Nav collapse: desktop nav hidden, hamburger shown, steps grid single column |
| < 900px | Hero: reduced padding |
| > 900px | Desktop: full layout |

## Viewport Behavior

### Mobile (< 768px)

| Element | Behavior | Status |
|---------|----------|--------|
| Container padding | 20px sides | PASS |
| Hero title | Fluid clamp(52px, 5.6vw, 96px) | PASS |
| Steps grid | Single column | PASS |
| Format grid | Auto-fill minmax(240px, 1fr) | PASS |
| Split grid (privacy) | Single column | PASS |
| Footer grid | Single column | PASS |
| Dropzone | Full width, adequate padding | PASS |
| Target row | Wraps with flex-wrap | PASS |
| Convert button | Full width on narrow screens | PASS |

### Tablet (768px - 860px)

| Element | Behavior | Status |
|---------|----------|--------|
| Navigation | Hamburger menu | PASS |
| Steps grid | Single column (collapses at 860px) | PASS |
| Format grid | 2-column auto-fill | PASS |
| Split grid | Single column (collapses at 860px) | PASS |

### Desktop (> 860px)

| Element | Behavior | Status |
|---------|----------|--------|
| Navigation | Full horizontal nav | PASS |
| Steps grid | 3-column grid | PASS |
| Format grid | Multi-column auto-fill | PASS |
| Split grid | 2-column (1.2fr / 0.8fr) | PASS |
| Footer grid | 3-column (1.4fr / 1fr / 1fr) | PASS |

## Identified Issues

### RESP-001: Format Grid Minimum Width

- **Severity**: Informational
- **Issue**: Format grid uses `minmax(240px, 1fr)` which could cause horizontal overflow on very narrow screens (< 240px)
- **Impact**: Extremely unlikely in practice; most phones are >= 320px
- **Status**: Acceptable

### RESP-002: Select Dropdown on Mobile

- **Severity**: Minor
- **Issue**: Target select has `min-width: 220px` which could overflow on very narrow screens
- **Impact**: Minor — the select is inside a flex container with `flex-wrap: wrap`
- **Status**: Acceptable

## Summary

The application is well-responsive across all standard viewport sizes. No critical responsiveness issues found. The use of `clamp()` for fluid typography and CSS Grid with auto-fill for format cards provides good adaptability.
