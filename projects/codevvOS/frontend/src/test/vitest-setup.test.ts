import { describe, it, expect } from 'vitest'
describe('vitest setup', () => {
  it('should have import.meta.env defined', () => {
    expect(import.meta.env).toBeDefined()
  })
})
