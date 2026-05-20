import sys
sys.path.insert(0, 'src')
from pdf_summarizer.obsidian_generator import ObsidianNoteGenerator

test_cases = [
    {
        'name': 'Double $$ wrapping',
        'input': r'''
$$

$$\Psi(x,t) = A \cdot \exp\left[i\left(\frac{2\pi}{\lambda}x\right)\right]$$
$$
''',
        'expected_contains': ['$$\\Psi(x,t)'],
        'expected_not_contains': ['$$\n\n$$']
    },
    {
        'name': '\\[...\\] environment',
        'input': r'''
\[
\frac{\partial^2}{\partial t^2}\Psi(x,t) = c^2 \frac{\partial^2}{\partial x^2}\Psi(x,t)
\]
''',
        'expected_contains': ['$$\\frac{\\partial^2'],
        'expected_not_contains': ['\\[', '\\]']
    },
    {
        'name': 'begin{equation} -> $$ (simple)',
        'input': r'''
\begin{equation}
E = h\nu = \frac{h}{T}
\end{equation}
''',
        'expected_contains': ['$$E = h\\nu'],
        'expected_not_contains': ['\\begin{equation}', '\\end{equation}']
    },
    {
        'name': 'begin{align} -> $$ with align preserved (complex)',
        'input': r'''
\begin{align}
\hat{E}\Psi &= E\Psi \\
\hat{p}\Psi &= p\Psi
\end{align}
''',
        'expected_contains': ['$$', '\\begin{align}', '\\hat{E}\\Psi'],
        'expected_not_contains': []
    },
    {
        'name': 'begin{pmatrix} -> $$ with pmatrix preserved',
        'input': r'''
\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}
''',
        'expected_contains': ['$$', '\\begin{pmatrix}', 'a & b'],
        'expected_not_contains': []
    },
    {
        'name': 'Inline formula with messy $',
        'input': r'The energy is $E = h$\nu$ and momentum is $p = $\frac{h}{\lambda}$',
        'expected_contains': ['$E = h\\nu$', '$p = \\frac{h}{\\lambda}$'],
        'expected_not_contains': ['$\\nu', '$\\frac']
    }
]

print('=== LaTeX Suite Compatibility Tests ===')
all_pass = True

for i, test in enumerate(test_cases, 1):
    result = ObsidianNoteGenerator._fix_latex_for_obsidian(test['input'])
    
    passed = True
    for expected in test['expected_contains']:
        if expected not in result:
            passed = False
            print(f'  FAIL: Expected "{expected}" not found')
    
    for not_expected in test['expected_not_contains']:
        if not_expected in result:
            passed = False
            print(f'  FAIL: Unexpected "{not_expected}" found')
    
    status = 'PASS' if passed else 'FAIL'
    all_pass = all_pass and passed
    print(f'\n[{status}] Test {i}: {test["name"]}')
    if not passed:
        print(f'  Input:  {repr(test["input"][:100])}')
        print(f'  Output: {repr(result[:200])}')

print(f'\n{"=" * 50}')
print(f'Result: {"ALL PASSED" if all_pass else "SOME FAILED"}')
