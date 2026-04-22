import { render, screen } from '@testing-library/react'
import App from './App'

test('renders and disables analyze when empty', () => {
  render(<App />)
  expect(screen.getByText(/Radio Medical Report Reviewer/i)).toBeInTheDocument()
  const btn = screen.getByRole('button', { name: /Analyze/i })
  expect(btn).toBeDisabled()
})

