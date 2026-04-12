# Keyboard Navigation — Design Spec

**Issue:** #19
**Date:** 2026-04-12
**Status:** Approved

## Goal

Full keyboard navigation for the genome-toolkit web app: table row navigation with arrow keys, focus traps in overlays, visible focus indicators, and return-focus-on-close behavior.

## Approach

Custom hooks (no new dependencies). The codebase already uses manual keydown listeners; this extends the pattern with two reusable hooks.

## 1. `useTableKeyboardNav` hook

**File:** `frontend/src/hooks/useTableKeyboardNav.ts`

**Interface:**
```ts
function useTableKeyboardNav(opts: {
  rowCount: number;
  onSelect: (index: number) => void;
  tableRef: RefObject<HTMLTableSectionElement>;
  enabled?: boolean;
}): {
  focusedIndex: number;
  getRowTabIndex: (index: number) => 0 | -1;
  onRowKeyDown: (e: React.KeyboardEvent, index: number) => void;
}
```

**Behavior:**
- Roving tabindex: only the focused row has `tabIndex={0}`, all others get `-1`
- Arrow Up/Down: move focus between rows, wrap at boundaries
- Home/End: jump to first/last row on current page
- Enter: call `onSelect(focusedIndex)` to open VariantDrawer
- Reset `focusedIndex` to 0 on page change
- Focus the active row DOM element via ref when index changes

## 2. `useFocusTrap` hook

**File:** `frontend/src/hooks/useFocusTrap.ts`

**Interface:**
```ts
function useFocusTrap(
  containerRef: RefObject<HTMLElement>,
  isOpen: boolean,
  opts?: {
    onEscape?: () => void;
    autoFocus?: boolean; // default true
    returnFocus?: boolean; // default true
  }
): void
```

**Behavior:**
- On open: save `document.activeElement`, then focus first focusable element inside container
- Tab / Shift+Tab: cycle within container's focusable elements (`a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])`)
- Escape: call `onEscape` callback
- On close: restore focus to saved element
- Focusable elements queried once on open and on DOM mutations (MutationObserver)

## 3. Component integration

### SNPTable.tsx
- Import and use `useTableKeyboardNav`
- Replace static `tabIndex={0}` on all rows with `getRowTabIndex(index)`
- Add `onRowKeyDown` to each row's `onKeyDown`
- Pass `onSelect` that calls `selectVariant(row.original)`

### VariantDrawer.tsx
- Import and use `useFocusTrap(drawerRef, true, { onEscape: onClose })`
- Remove existing manual Escape keydown listener (lines 152-156)
- Add `ref={drawerRef}` to container div

### ChecklistSidebar.tsx
- Import and use `useFocusTrap(sidebarRef, isOpen, { onEscape: onClose })`
- Add Escape-to-close (handled by the hook)

### CommandPalette.tsx
- Import and use `useFocusTrap(paletteRef, isOpen, { onEscape: onClose })`
- Remove existing manual Escape listener (lines 434-440)
- Keep existing auto-focus on input (hook's autoFocus will focus first element; input is first)

## 4. Focus indicator styles

Visible focus ring on table rows:
```css
.snp-table tbody tr:focus-visible {
  outline: 2px solid #4a90d9;
  outline-offset: -2px;
}
```

Suppress default outline on mouse click (`:focus:not(:focus-visible)`).

## 5. Out of scope

- Skip links / landmark navigation
- Screen reader announcements (aria-live)
- Arrow key navigation within VariantDrawer tabs
- Keyboard shortcuts help dialog

## 6. Testing

- Unit tests for `useTableKeyboardNav`: arrow keys, wrap, Home/End, Enter, page reset
- Unit tests for `useFocusTrap`: trap Tab, Escape, return focus, autoFocus
- Integration: SNPTable keyboard nav with mocked selectVariant
