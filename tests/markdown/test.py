import unittest

from tests.markdown import (
    check
)

class MarkdownCheckTests(unittest.TestCase):
    def test_counts_indented_math_fences(self) -> None:
        markdown = "1. Formula:\n\n   ```math\nx=1\n   ```\n" # Indented math fence.
        self.assertEqual(check.count_math_blocks(markdown), 1) # Count the number of math blocks in the markdown.
        self.assertEqual(check.lint_markdown(markdown), []) # Verify that no linting errors are found. 
        
    def test_rejects_known_github_hazards(self) -> None:
        markdown = "$$\nx=1\n$$\n\\begin{cases}x\\end{cases}\n" # Markdown with known GitHub hazards. 
        errors = check.lint_markdown(markdown) # Verify that linting errors are found. 
        self.assertEqual(len(errors), 3) # Verify that the number of linting errors is 3. 
        
    def test_counts_github_math_output(self) -> None:
        # Verify that the number of rendered math blocks in the HTML output is counted correctly.
        html = (
            '<math-renderer class="js-display-math">$$x=1$$</math-renderer>'
            '<math-renderer class="js-display-math">$$y=2$$</math-renderer>'
        )
        self.assertEqual(check.count_rendered_math_blocks(html), 2)
        
if __name__ == "__main__":
    unittest.main()
