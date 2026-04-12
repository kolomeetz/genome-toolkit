import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useRef } from 'react'
import { useFocusTrap } from '../useFocusTrap'

function createContainer(): HTMLDivElement {
  const container = document.createElement('div')
  const btn1 = document.createElement('button')
  btn1.textContent = 'First'
  const btn2 = document.createElement('button')
  btn2.textContent = 'Second'
  const btn3 = document.createElement('button')
  btn3.textContent = 'Third'
  container.append(btn1, btn2, btn3)
  document.body.appendChild(container)
  return container
}

describe('useFocusTrap', () => {
  it('focuses first focusable element on open', () => {
    const container = createContainer()
    const { unmount } = renderHook(() => {
      const ref = useRef(container)
      useFocusTrap(ref, true)
    })
    expect(document.activeElement).toBe(container.querySelector('button'))
    unmount()
    container.remove()
  })

  it('calls onEscape when Escape is pressed', () => {
    const container = createContainer()
    const onEscape = vi.fn()
    const { unmount } = renderHook(() => {
      const ref = useRef(container)
      useFocusTrap(ref, true, { onEscape })
    })
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(onEscape).toHaveBeenCalledOnce()
    unmount()
    container.remove()
  })

  it('does not call onEscape when closed', () => {
    const container = createContainer()
    const onEscape = vi.fn()
    const { unmount } = renderHook(() => {
      const ref = useRef(container)
      useFocusTrap(ref, false, { onEscape })
    })
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(onEscape).not.toHaveBeenCalled()
    unmount()
    container.remove()
  })

  it('traps Tab forward — wraps from last to first', () => {
    const container = createContainer()
    const buttons = container.querySelectorAll('button')
    const { unmount } = renderHook(() => {
      const ref = useRef(container)
      useFocusTrap(ref, true)
    })
    ;(buttons[2] as HTMLElement).focus()
    const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })
    Object.defineProperty(event, 'preventDefault', { value: vi.fn() })
    container.dispatchEvent(event)
    expect(document.activeElement).toBe(buttons[0])
    unmount()
    container.remove()
  })

  it('traps Shift+Tab backward — wraps from first to last', () => {
    const container = createContainer()
    const buttons = container.querySelectorAll('button')
    const { unmount } = renderHook(() => {
      const ref = useRef(container)
      useFocusTrap(ref, true)
    })
    ;(buttons[0] as HTMLElement).focus()
    const event = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })
    Object.defineProperty(event, 'preventDefault', { value: vi.fn() })
    container.dispatchEvent(event)
    expect(document.activeElement).toBe(buttons[2])
    unmount()
    container.remove()
  })

  it('restores focus to previously focused element on close', () => {
    const trigger = document.createElement('button')
    trigger.textContent = 'Trigger'
    document.body.appendChild(trigger)
    trigger.focus()

    const container = createContainer()
    const { rerender, unmount } = renderHook(
      ({ isOpen }) => {
        const ref = useRef(container)
        useFocusTrap(ref, isOpen, { returnFocus: true })
      },
      { initialProps: { isOpen: true } }
    )
    expect(document.activeElement).toBe(container.querySelector('button'))
    rerender({ isOpen: false })
    expect(document.activeElement).toBe(trigger)
    unmount()
    container.remove()
    trigger.remove()
  })

  it('skips auto-focus when autoFocus is false', () => {
    const trigger = document.createElement('button')
    trigger.textContent = 'Trigger'
    document.body.appendChild(trigger)
    trigger.focus()

    const container = createContainer()
    const { unmount } = renderHook(() => {
      const ref = useRef(container)
      useFocusTrap(ref, true, { autoFocus: false })
    })
    expect(document.activeElement).toBe(trigger)
    unmount()
    container.remove()
    trigger.remove()
  })
})
