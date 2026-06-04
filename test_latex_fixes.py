#!/usr/bin/env python3
"""Test script for LaTeX rendering fixes in ObsidianGenerator."""

import sys
from pathlib import Path

# Add the source directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from pdf_summarizer.obsidian_generator import ObsidianNoteGenerator

def test_all_latex_fixes():
    """Test all LaTeX fix functions with problematic examples."""
    
    test_cases = [
        # Test 1: Escaped dollars bug
        (
            "Original: $\\hbar\\$frac{1}{2}$",
            "$\\hbar\\$frac{1}{2}$",
            "Fix escaped dollars"
        ),
        
        # Test 2: Nested dollar signs
        (
            "Original: $\\hat{$O}$",
            "$\\hat{$O}$",
            "Fix nested dollar signs"
        ),
        
        # Test 3: Double vertical bars
        (
            "Original: $\\|\\Psi(x,t)\\|$",
            "$\\|\\Psi(x,t)\\|$",
            "Fix double vertical bars"
        ),
        
        # Test 4: Backtick-wrapped formulas
        (
            "Original: `$\\int \\Psi dx$`",
            "`$\\int \\Psi dx$`",
            "Fix backtick-wrapped formulas"
        ),
        
        # Test 5: Command prefix dollars
        (
            "Original: $\\frac{1}{2}$ and $$\\frac{1}{2}$$",
            "$\\frac{1}{2}$ and $$\\frac{1}{2}$$",
            "Fix command prefix dollars"
        ),
        
        # Test 6: Parenthesis environments
        (
            "Original: \\(E=mc^2\\) and \\[\\frac{1}{2}\\]",
            "\\(E=mc^2\\) and \\[\\frac{1}{2}\\]",
            "Fix parenthesis environments"
        ),
        
        # Test 7: Mixed complex example
        (
            "Original: 让我们考虑波函数 $\\hat{$O}$ \\(E=mc^2\\)，其中 $\\|\\Psi\\|$ 和 `$\\int dx$`",
            "让我们考虑波函数 $\\hat{$O}$ \\(E=mc^2\\)，其中 $\\|\\Psi\\|$ 和 `$\\int dx$`",
            "Mixed complex example"
        ),
    ]
    
    print("=" * 80)
    print("Testing LaTeX Fixes")
    print("=" * 80)
    
    all_passed = True
    for description, original, test_name in test_cases:
        print(f"\n--- {test_name} ---")
        print(f"Input:  {repr(original[:100])}")
        
        try:
            fixed = ObsidianNoteGenerator._fix_latex_for_obsidian(original)
            print(f"Output: {repr(fixed[:100])}")
            print("✓ Processed successfully")
        except Exception as e:
            print(f"✗ Error: {e}")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All tests executed successfully!")
    else:
        print("❌ Some tests failed!")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = test_all_latex_fixes()
    sys.exit(0 if success else 1)
