from .base import TestTemplate, register_template

register_template(TestTemplate(
    name="spa",
    description="Greenfield React SPA with routing, form, and API call",
    prompt="""Build a greenfield React single-page application using Vite + React + TypeScript.

Requirements:
1. Set up a new Vite project with React and TypeScript (use `npm create vite@latest . -- --template react-ts`)
2. Install react-router-dom for routing
3. Create three pages: Home, Contact, and About
4. The Contact page must have a form with: name (required), email (required, validated), message (required, min 10 chars)
5. On form submit, POST to https://jsonplaceholder.typicode.com/posts and display a success message with the response ID
6. Handle loading and error states on the form
7. Add navigation between pages
8. The app must compile without TypeScript errors (`npm run build` passes)

Do not use any UI component library (no shadcn, no MUI, no chakra). Plain CSS is fine.
Write the complete, working application.""",
    acceptance_criteria=[
        "npm run build completes without errors",
        "Three routes exist: /, /contact, /about",
        "Contact form has name, email, message fields with validation",
        "Form submits to jsonplaceholder API and shows success with response ID",
        "Loading and error states are handled on form submit",
        "Navigation links between pages work",
        "No TypeScript errors (strict mode)",
    ],
))
