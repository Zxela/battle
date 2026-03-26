from .base import TestTemplate, register_template

register_template(TestTemplate(
    name="mobile",
    description="Greenfield React Native app with navigation and data list",
    prompt="""Build a greenfield React Native application using Expo.

Requirements:
1. Initialize with `npx create-expo-app@latest . --template blank-typescript`
2. Install @react-navigation/native and @react-navigation/stack
3. Create two screens: HomeScreen (shows a list of items) and DetailScreen (shows one item's details)
4. HomeScreen: fetch a list of posts from https://jsonplaceholder.typicode.com/posts (limit to 20), display as FlatList with title and body preview
5. Tapping a list item navigates to DetailScreen with the full post
6. DetailScreen: shows title, full body, and a back button
7. Handle loading and error states on the fetch
8. The app must pass `npx tsc --noEmit` without errors

Write the complete, working application.""",
    acceptance_criteria=[
        "TypeScript compiles without errors",
        "HomeScreen fetches and displays 20 posts in a FlatList",
        "Tapping an item navigates to DetailScreen",
        "DetailScreen shows full post details",
        "Loading and error states handled",
        "Back navigation works",
    ],
))
