import pathlib
import re

BLOCK_PAT = re.compile(
    r'```\n((?:(?!```)(?:recall_(?:store|search))[^\n]*\n?|[ \t]*[^\n]*\n?)*?)```',
    re.DOTALL
)

agents_dir = pathlib.Path('C:/Users/trg16/Dev/Bricklayer2.0/template/.claude/agents')
for fname in ['mortar.md', 'parallel-debugger.md', 'pointer.md']:
    f = agents_dir / fname
    text = f.read_text(encoding='utf-8')
    matches = BLOCK_PAT.findall(text)
    print(f'{fname}: {len(matches)} match(es) with script BLOCK_PAT')
    # Show what a recall block actually looks like
    simple = re.compile(r'```\n(.*?)```', re.DOTALL)
    all_blocks = simple.findall(text)
    for b in all_blocks:
        if 'recall_' in b:
            print(f'  RECALL BLOCK BODY: {repr(b[:120])}')

print('DONE')
