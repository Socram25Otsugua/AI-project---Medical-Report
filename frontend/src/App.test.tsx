import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { test, vi } from 'vitest'
import App from './App'

test('blocks send and shows observation chart notice when chart is incomplete', async () => {
  const fetchSpy = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValue({ ok: true, json: async () => [], text: async () => '' } as any)

  render(<App />)
  expect(screen.getByText(/Radio Medical Assistant/i)).toBeInTheDocument()
  expect(document.querySelector('.chatDoctorTitle')).toHaveTextContent('AI Doctor')
  expect(screen.queryByRole('button', { name: /^Form$/i })).not.toBeInTheDocument()

  const btn = screen.getByRole('button', { name: /Send to AI doctor/i })
  expect(btn).not.toBeDisabled()

  fireEvent.click(btn)
  expect(await screen.findByText(/Observation chart incomplete/i)).toBeInTheDocument()

  await waitFor(() => expect(fetchSpy).toHaveBeenCalled())

  fetchSpy.mockRestore()
})
