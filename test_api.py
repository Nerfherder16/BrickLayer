import anthropic
c = anthropic.Anthropic()
r = c.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=50,
    messages=[{"role": "user", "content": "say hi"}]
)
print(r.content[0].text)
