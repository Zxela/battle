from .base import TestTemplate, register_template

register_template(TestTemplate(
    name="tooling",
    description="Node.js CLI tool with argument parsing, file I/O, and error handling",
    prompt="""Build a Node.js CLI tool called `wordcount` using TypeScript.

Requirements:
1. Initialize a new Node.js project with TypeScript
2. Use `commander` for argument parsing
3. The CLI must support: `wordcount <file>` to count words in a file
4. Options: `--chars` (count characters), `--lines` (count lines), `--words` (default, count words)
5. If the file doesn't exist, print a clear error message to stderr and exit with code 1
6. If no file is provided, read from stdin
7. Output format: `<count> <filename>` (matching Unix `wc` style)
8. The tool must compile with `npm run build` and the compiled output must be executable as `node dist/index.js <args>`
9. Add at least 3 unit tests using Jest for the counting logic

Write the complete, working tool including tests.""",
    acceptance_criteria=[
        "npm run build compiles without errors",
        "wordcount <file> counts words correctly",
        "--lines flag counts lines",
        "--chars flag counts characters",
        "Missing file prints to stderr and exits with code 1",
        "stdin input works when no file provided",
        "Jest tests pass for counting logic",
    ],
))
