export default function WelcomePanel(): JSX.Element {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--text-sm)',
      }}
    >
      Welcome to CodeVV OS. Open an app from the dock below.
    </div>
  )
}
