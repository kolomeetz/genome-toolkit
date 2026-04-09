import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CommandPalette } from '../components/CommandPalette'

const baseProps = {
  open: true,
  onClose: vi.fn(),
  messages: [],
  streaming: false,
  streamingText: '',
  status: '',
  suggestions: [],
  actions: [],
  onSend: vi.fn(),
  onAction: vi.fn(),
  starterPrompts: [
    { text: 'Which drugs should I discuss?', subtitle: 'Based on CYP2D6', priority: 1 },
    { text: 'Am I at risk?', subtitle: '12 interactions', priority: 2 },
  ],
  starterCapabilities: ['Read vault notes', 'Search 3.4M variants'],
  starterExplore: ["What's interesting in my genome?"],
}

describe('CommandPalette EmptyState', () => {
  it('renders capabilities when no messages', () => {
    render(<CommandPalette {...baseProps} />)
    expect(screen.getByText('WHAT I CAN DO')).toBeTruthy()
    expect(screen.getByText('Read vault notes')).toBeTruthy()
    expect(screen.getByText('Search 3.4M variants')).toBeTruthy()
  })

  it('renders personalized prompts when no messages', () => {
    render(<CommandPalette {...baseProps} />)
    expect(screen.getByText('SUGGESTED FOR YOU')).toBeTruthy()
    expect(screen.getByText('Which drugs should I discuss?')).toBeTruthy()
    expect(screen.getByText('Based on CYP2D6')).toBeTruthy()
    expect(screen.getByText('Am I at risk?')).toBeTruthy()
    expect(screen.getByText('12 interactions')).toBeTruthy()
  })

  it('renders explore prompts when no messages', () => {
    render(<CommandPalette {...baseProps} />)
    expect(screen.getByText('EXPLORE')).toBeTruthy()
    expect(screen.getByText("What's interesting in my genome?")).toBeTruthy()
  })

  it('calls onSend when a prompt is clicked', () => {
    const onSend = vi.fn()
    render(<CommandPalette {...baseProps} onSend={onSend} />)
    fireEvent.click(screen.getByText('Which drugs should I discuss?'))
    expect(onSend).toHaveBeenCalledWith('Which drugs should I discuss?')
  })

  it('calls onSend when an explore prompt is clicked', () => {
    const onSend = vi.fn()
    render(<CommandPalette {...baseProps} onSend={onSend} />)
    fireEvent.click(screen.getByText("What's interesting in my genome?"))
    expect(onSend).toHaveBeenCalledWith("What's interesting in my genome?")
  })

  it('does NOT render empty state when messages exist', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'user', content: 'Hello' }]}
      />
    )
    expect(screen.queryByText('WHAT I CAN DO')).toBeNull()
    expect(screen.queryByText('SUGGESTED FOR YOU')).toBeNull()
    expect(screen.queryByText('EXPLORE')).toBeNull()
  })
})
