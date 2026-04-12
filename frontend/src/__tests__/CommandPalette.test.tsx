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

describe('CommandPalette Collapsed Mode', () => {
  const collapsedProps = {
    ...baseProps,
    collapsed: true,
    onToggleCollapse: vi.fn(),
  }

  it('renders EXPAND button when collapsed', () => {
    render(<CommandPalette {...collapsedProps} />)
    expect(screen.getByText('EXPAND')).toBeTruthy()
  })

  it('renders COLLAPSE button when expanded', () => {
    render(<CommandPalette {...baseProps} collapsed={false} onToggleCollapse={vi.fn()} />)
    expect(screen.getByText('COLLAPSE')).toBeTruthy()
  })

  it('calls onToggleCollapse when EXPAND is clicked', () => {
    const onToggle = vi.fn()
    render(<CommandPalette {...collapsedProps} onToggleCollapse={onToggle} />)
    fireEvent.click(screen.getByText('EXPAND'))
    expect(onToggle).toHaveBeenCalledOnce()
  })

  it('hides empty state when collapsed', () => {
    render(<CommandPalette {...collapsedProps} />)
    expect(screen.queryByText('WHAT I CAN DO')).toBeNull()
    expect(screen.queryByText('SUGGESTED FOR YOU')).toBeNull()
    expect(screen.queryByText('EXPLORE')).toBeNull()
  })

  it('shows compact labels (YOU/AI) when collapsed with messages', () => {
    render(
      <CommandPalette
        {...collapsedProps}
        messages={[
          { role: 'user', content: 'Show CYP2D6' },
          { role: 'assistant', content: 'Found 23 variants' },
        ]}
      />
    )
    expect(screen.getByText('YOU')).toBeTruthy()
    expect(screen.getByText('AI')).toBeTruthy()
    expect(screen.queryByText('INPUT //')).toBeNull()
    expect(screen.queryByText('OUTPUT //')).toBeNull()
  })

  it('shows full labels (INPUT/OUTPUT) when expanded with messages', () => {
    render(
      <CommandPalette
        {...baseProps}
        collapsed={false}
        messages={[
          { role: 'user', content: 'Show CYP2D6' },
          { role: 'assistant', content: 'Found 23 variants' },
        ]}
      />
    )
    expect(screen.getByText('INPUT //')).toBeTruthy()
    expect(screen.getByText('OUTPUT //')).toBeTruthy()
  })

  it('hides COPY buttons on messages when collapsed', () => {
    render(
      <CommandPalette
        {...collapsedProps}
        messages={[
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'World' },
        ]}
      />
    )
    expect(screen.queryByText('COPY')).toBeNull()
    expect(screen.queryByText('COPY_ALL')).toBeNull()
  })

  it('shows streaming status bar when collapsed and streaming', () => {
    render(
      <CommandPalette
        {...collapsedProps}
        streaming={true}
        streamingText="Filtering..."
        status="FILTERING"
      />
    )
    // Status appears in both the collapsed status bar and the input area
    expect(screen.getAllByText('FILTERING').length).toBeGreaterThanOrEqual(1)
  })

  it('uses transparent background when collapsed (no overlay)', () => {
    const { container } = render(<CommandPalette {...collapsedProps} />)
    const backdrop = container.firstChild as HTMLElement
    expect(backdrop.style.background).toBe('transparent')
  })

  it('does not render when open is false', () => {
    const { container } = render(<CommandPalette {...collapsedProps} open={false} />)
    expect(container.innerHTML).toBe('')
  })
})

/* ── Messages rendering ── */

describe('CommandPalette Messages', () => {
  it('renders user messages with INPUT // label', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'user', content: 'Show my CYP2D6 variants' }]}
      />
    )
    expect(screen.getByText('INPUT //')).toBeTruthy()
    expect(screen.getByText('Show my CYP2D6 variants')).toBeTruthy()
  })

  it('renders assistant messages with OUTPUT // label', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: 'Found 23 variants in CYP2D6.' }]}
      />
    )
    expect(screen.getByText('OUTPUT //')).toBeTruthy()
    expect(screen.getByText(/Found 23 variants/)).toBeTruthy()
  })

  it('renders multiple messages in order', () => {
    const { container } = render(
      <CommandPalette
        {...baseProps}
        messages={[
          { role: 'user', content: 'What about BRCA1?' },
          { role: 'assistant', content: 'BRCA1 is associated with breast cancer risk.' },
          { role: 'user', content: 'Any variants?' },
        ]}
      />
    )
    const labels = container.querySelectorAll('.label')
    const labelTexts = Array.from(labels).map(l => l.textContent)
    // Should contain INPUT //, OUTPUT //, INPUT // in order (plus the header label)
    expect(labelTexts.filter(t => t === 'INPUT //').length).toBe(2)
    expect(labelTexts.filter(t => t === 'OUTPUT //').length).toBe(1)
  })

  it('strips [VOICE] prefix from user messages', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'user', content: '[VOICE] Tell me about APOE' }]}
      />
    )
    expect(screen.getByText('Tell me about APOE')).toBeTruthy()
    expect(screen.queryByText('[VOICE] Tell me about APOE')).toBeNull()
  })
})

/* ── Streaming state ── */

describe('CommandPalette Streaming', () => {
  it('shows streaming text with cursor block', () => {
    const { container } = render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'user', content: 'Analyze MTHFR' }]}
        streaming={true}
        streamingText="MTHFR is a gene involved in folate metabolism"
      />
    )
    expect(screen.getByText(/MTHFR is a gene involved in folate metabolism/)).toBeTruthy()
    // The blinking cursor block character
    expect(container.textContent).toContain('█')
  })

  it('shows OUTPUT // label for streaming block', () => {
    render(
      <CommandPalette
        {...baseProps}
        streaming={true}
        streamingText="Loading..."
      />
    )
    expect(screen.getByText('OUTPUT //')).toBeTruthy()
  })

  it('disables input while streaming', () => {
    render(
      <CommandPalette
        {...baseProps}
        streaming={true}
        streamingText="Processing..."
      />
    )
    const input = screen.getByPlaceholderText('ASK_ABOUT_YOUR_GENOME...')
    expect(input).toBeDisabled()
  })
})

/* ── Action buttons ── */

describe('CommandPalette Actions', () => {
  const actions = [
    { type: 'show_gene' as const, label: 'View CYP2D6', params: { gene: 'CYP2D6' } },
    { type: 'add_to_checklist' as const, label: 'Add to checklist', params: { item: 'CYP2D6 review' } },
  ]

  it('renders action buttons', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: 'Here are your results.' }]}
        actions={actions}
      />
    )
    expect(screen.getByText('View CYP2D6')).toBeTruthy()
    expect(screen.getByText('Add to checklist')).toBeTruthy()
  })

  it('calls onAction when an action button is clicked', () => {
    const onAction = vi.fn()
    render(
      <CommandPalette
        {...baseProps}
        onAction={onAction}
        messages={[{ role: 'assistant', content: 'Done.' }]}
        actions={actions}
      />
    )
    fireEvent.click(screen.getByText('View CYP2D6'))
    expect(onAction).toHaveBeenCalledWith(actions[0])
  })

  it('hides actions while streaming', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: 'Done.' }]}
        actions={actions}
        streaming={true}
        streamingText="Still going..."
      />
    )
    expect(screen.queryByText('View CYP2D6')).toBeNull()
  })
})

/* ── Suggestion chips ── */

describe('CommandPalette Suggestions', () => {
  const suggestions = ['Tell me more about CYP2D6', 'Show risk summary']

  it('renders suggestion chips', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: 'Analysis complete.' }]}
        suggestions={suggestions}
      />
    )
    expect(screen.getByText('Tell me more about CYP2D6')).toBeTruthy()
    expect(screen.getByText('Show risk summary')).toBeTruthy()
  })

  it('calls onSend when a suggestion chip is clicked', () => {
    const onSend = vi.fn()
    render(
      <CommandPalette
        {...baseProps}
        onSend={onSend}
        messages={[{ role: 'assistant', content: 'Done.' }]}
        suggestions={suggestions}
      />
    )
    fireEvent.click(screen.getByText('Show risk summary'))
    expect(onSend).toHaveBeenCalledWith('Show risk summary')
  })

  it('hides suggestions while streaming', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: 'Done.' }]}
        suggestions={suggestions}
        streaming={true}
        streamingText="..."
      />
    )
    expect(screen.queryByText('Tell me more about CYP2D6')).toBeNull()
  })
})

/* ── Copy buttons ── */

describe('CommandPalette Copy', () => {
  const writeTextMock = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: { writeText: writeTextMock },
    })
    writeTextMock.mockClear()
  })

  it('shows COPY button on assistant messages', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'World' },
        ]}
      />
    )
    expect(screen.getByText('COPY')).toBeTruthy()
  })

  it('does not show COPY button on user messages', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'user', content: 'Hello' }]}
      />
    )
    expect(screen.queryByText('COPY')).toBeNull()
  })

  it('copies single message to clipboard on COPY click', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Response text here' },
        ]}
      />
    )
    fireEvent.click(screen.getByText('COPY'))
    expect(writeTextMock).toHaveBeenCalledWith('Response text here')
  })

  it('shows COPY_ALL button when messages exist', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[
          { role: 'user', content: 'Hi' },
          { role: 'assistant', content: 'Hello' },
        ]}
      />
    )
    expect(screen.getByText('COPY_ALL')).toBeTruthy()
  })

  it('copies all messages to clipboard on COPY_ALL click', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[
          { role: 'user', content: 'Hi' },
          { role: 'assistant', content: 'Hello back' },
        ]}
      />
    )
    fireEvent.click(screen.getByText('COPY_ALL'))
    expect(writeTextMock).toHaveBeenCalledWith(
      '**You:**\n\nHi\n\n---\n\n**AI:**\n\nHello back'
    )
  })
})

/* ── Input form submission ── */

describe('CommandPalette Input', () => {
  it('calls onSend and clears input on submit', () => {
    const onSend = vi.fn()
    render(<CommandPalette {...baseProps} onSend={onSend} />)
    const input = screen.getByPlaceholderText('ASK_ABOUT_YOUR_GENOME...')
    fireEvent.change(input, { target: { value: 'Tell me about APOE' } })
    fireEvent.submit(input.closest('form')!)
    expect(onSend).toHaveBeenCalledWith('Tell me about APOE')
    expect(input).toHaveValue('')
  })

  it('does not call onSend when input is empty', () => {
    const onSend = vi.fn()
    render(<CommandPalette {...baseProps} onSend={onSend} />)
    const input = screen.getByPlaceholderText('ASK_ABOUT_YOUR_GENOME...')
    fireEvent.submit(input.closest('form')!)
    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not call onSend when input is whitespace only', () => {
    const onSend = vi.fn()
    render(<CommandPalette {...baseProps} onSend={onSend} />)
    const input = screen.getByPlaceholderText('ASK_ABOUT_YOUR_GENOME...')
    fireEvent.change(input, { target: { value: '   ' } })
    fireEvent.submit(input.closest('form')!)
    expect(onSend).not.toHaveBeenCalled()
  })

  it('shows FOLLOW_UP placeholder when messages exist', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'user', content: 'Hi' }]}
      />
    )
    expect(screen.getByPlaceholderText('FOLLOW_UP...')).toBeTruthy()
  })
})

/* ── Markdown rendering ── */

describe('CommandPalette Markdown', () => {
  it('renders markdown content in assistant messages', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: 'This has **bold** text and a [link](https://example.com).' }]}
      />
    )
    // Bold text should be rendered inside a <strong> tag
    const strong = document.querySelector('strong')
    expect(strong).toBeTruthy()
    expect(strong!.textContent).toBe('bold')
    // Link should be rendered
    const link = document.querySelector('a[href="https://example.com"]')
    expect(link).toBeTruthy()
    expect(link!.textContent).toBe('link')
  })

  it('renders markdown lists', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: '- Item one\n- Item two\n- Item three' }]}
      />
    )
    const listItems = document.querySelectorAll('li')
    expect(listItems.length).toBe(3)
  })
})

/* ── Insight blocks ── */

describe('CommandPalette Insight Blocks', () => {
  const insightContent = `Here is some preamble.

★ Insight ──────────────
Your CYP2D6 status suggests you are an ultra-rapid metabolizer.
──────────────

And some follow-up text.`

  it('renders insight block with star label', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: insightContent }]}
      />
    )
    expect(screen.getByText('★ INSIGHT')).toBeTruthy()
  })

  it('renders insight content text', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: insightContent }]}
      />
    )
    expect(screen.getByText(/ultra-rapid metabolizer/)).toBeTruthy()
  })

  it('renders surrounding markdown alongside insight', () => {
    render(
      <CommandPalette
        {...baseProps}
        messages={[{ role: 'assistant', content: insightContent }]}
      />
    )
    expect(screen.getByText(/preamble/)).toBeTruthy()
    expect(screen.getByText(/follow-up text/)).toBeTruthy()
  })
})
