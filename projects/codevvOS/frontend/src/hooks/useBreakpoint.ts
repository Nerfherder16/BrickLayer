import { useState, useEffect } from 'react'

interface Breakpoint {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
}

function getBreakpoint(): Breakpoint {
  const w = window.innerWidth
  return {
    isMobile: w < 768,
    isTablet: w >= 768 && w < 1024,
    isDesktop: w >= 1024,
  }
}

export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>(getBreakpoint)

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>

    function handleResize(): void {
      clearTimeout(timer)
      timer = setTimeout(() => {
        setBreakpoint(getBreakpoint())
      }, 150)
    }

    window.addEventListener('resize', handleResize)
    return () => {
      clearTimeout(timer)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return breakpoint
}
