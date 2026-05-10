import { render, screen, waitFor } from '@testing-library/react'
import { test, vi } from 'vitest'
import App from './App'

test('renders and disables analyze when empty', async () => {
  // App loads history on mount; stub fetch to avoid network in tests.
  const fetchSpy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue({ ok: true, json: async () => [], text: async () => '' } as any)

  render(<App />)
  expect(screen.getByText(/Radio Medical Report Reviewer/i)).toBeInTheDocument()
  const btn = screen.getByRole('button', { name: /Analyze/i })
  expect(btn).toBeDisabled()

  // Allow the history-loading effect to run without act warnings.
  await waitFor(() => expect(fetchSpy).toHaveBeenCalled())

  fetchSpy.mockRestore()
})

