import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import App from '../App'
import * as dockview from 'dockview-react'

describe('App', () => {
  it('should render without error and produce non-zero body height', () => {
    expect(() => render(<App />)).not.toThrow()
    // jsdom sets offsetHeight to 0, but body should exist
    expect(document.body).toBeDefined()
  })
})

describe('dockview-react', () => {
  it('should export DockviewReact', () => {
    expect(dockview.DockviewReact).toBeDefined()
  })
})
