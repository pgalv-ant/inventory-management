# Anthropic Marketing Re-skin — Design

**Date:** 2026-03-31
**Scope:** Color palette + serif headings. One file. No layout changes.

## Decisions

| Question | Choice |
|---|---|
| Which Anthropic reference? | anthropic.com marketing (warm ivory, terracotta, editorial) |
| Typography scope? | Serif headings only — tables/body/nav stay sans |
| Dark mode? | Keep the toggle, swap cool slate → warm charcoal |
| Implementation approach? | CSS variables only (`App.vue` alone) |

## Light palette

| Variable | New | Old |
|---|---|---|
| `--color-bg` | `#F0EEE6` | `#f8fafc` |
| `--color-surface` | `#FFFFFF` | `#ffffff` |
| `--color-surface-hover` | `#FAF8F3` | `#f1f5f9` |
| `--color-text` | `#191919` | `#0f172a` |
| `--color-text-body` | `#2D2D2A` | `#1e293b` |
| `--color-text-secondary` | `#87715E` | `#64748b` |
| `--color-border` | `#E5DFD3` | `#e2e8f0` |
| `--color-border-hover` | `#D4C5B0` | `#cbd5e1` |
| `--color-link` | `#CC785C` | `#2563eb` |
| `--color-link-bg` | `#F5E6DF` | `#eff6ff` |

## Warm dark palette

| Variable | New | Old |
|---|---|---|
| `--color-bg` | `#1C1917` | `#0f172a` |
| `--color-surface` | `#292524` | `#1e293b` |
| `--color-surface-hover` | `#3B3633` | `#334155` |
| `--color-text` | `#F5F1EC` | `#f1f5f9` |
| `--color-text-body` | `#E7E0D8` | `#e2e8f0` |
| `--color-text-secondary` | `#A8998A` | `#94a3b8` |
| `--color-border` | `#3B3633` | `#334155` |
| `--color-border-hover` | `#524A44` | `#475569` |
| `--color-link` | `#E09B7D` | `#60a5fa` |
| `--color-link-bg` | `#3D2E28` | `#1e3a8a` |

## Typography

Add to `:root`:
```css
--font-serif: Georgia, 'Times New Roman', serif;
```

Add one rule:
```css
h1, h2, h3, .page-header h2, .stat-value, .kpi-value {
  font-family: var(--font-serif);
}
```

## Explicitly unchanged

- Status colors (green `#059669` / blue `#2563eb` / yellow `#f59e0b` / red `#dc2626`) on stat cards, badges, donut chart — semantic, same in both modes
- Layout, spacing, border-radius, shadows
- All other files — views have `var(--color-*)` refs from the dark-mode work, they inherit automatically
- Dark mode toggle behavior (`useTheme.js`, `DarkModeToggle.vue`)

## Testing

- Vite build must succeed
- Playwright: screenshot light + dark dashboard, verify computed `body.backgroundColor` is `rgb(240, 238, 230)` light / `rgb(28, 25, 23)` dark
- Verify serif font-family on `h2` element
- Toggle still flips both palettes

## Risk

Near-zero. Value swap in existing properties, one new selector. Git revert is a clean rollback.
