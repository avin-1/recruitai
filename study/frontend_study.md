# Frontend Study Guide

## 1. Tech Stack Overview

- **Framework:** React 19 (via Vite)
- **Language:** JavaScript (ES6+)
- **Build Tool:** Vite
- **Styling:** Tailwind CSS v4
- **UI Components:** Radix UI (Headless primitive), Lucide React (Icons)
- **State Management:** React Hooks (`useState`, `useEffect`) + Context API (implied)
- **HTTP Client:** Axios

### Why this stack?
- **React 19:** The latest standard. It introduces new hooks and concurrency features (though we mostly use standard patterns here).
- **Vite:** Replaces Webpack. It's significantly faster because it uses native ES modules during development. It doesn't bundle the whole app every time you save a file.
- **Tailwind CSS v4:** A utility-first CSS framework. Instead of writing custom CSS classes (`.my-button { color: red }`), we write utility classes directly in HTML (`className="text-red-500"`). Version 4 is the newest, rust-based, and faster compilation.
- **Radix UI:** "Headless" components. They provide the *logic* (accessibility, keyboard nav) but no *styles*. We style them with Tailwind. This gives us full control over the look while keeping accessibility perfect.

## 2. Key Components Analysis

### Directory Structure (`front/src/`)
- `components/`: Reusable UI bits (Buttons, Cards, Inputs).
- `pages/`: Full page views (Home, Dashboard, Login).
- `App.jsx`: The main router and layout definition.
- `index.css`: Global styles and Tailwind imports.

### Important Principles Used
- **Component Composition:** Building complex UIs from small, single-purpose components.
- **Responsive Design:** Using Tailwind's prefixes (`md:flex`, `lg:w-1/2`) to ensure mobile compatibility.
- **Client-Side Routing:** `react-router-dom` handles page switches instantly without reloading the browser.

## 3. Exam Q&A Preparation

**Q: Why use Vite instead of Create React App (CRA)?**
**A:** CRA is deprecated and slow. Vite is the modern standard. It offers instant server start and Hot Module Replacement (HMR) that stays fast regardless of app size.

**Q: Explain the benefit of Tailwind CSS.**
**A:** Speed of development and consistency. You don't have to context-switch between a `.js` file and a `.css` file. It also creates smaller production bundles because it purges unused styles automatically.

**Q: What is the Virtual DOM?**
**A:** React keeps a lightweight copy of the UI in memory. When data changes, it updates this copy, compares it to the real DOM (diffing), and only updates the specific elements that changed. This minimizes slow browser repaints.

**Q: How does the Frontend talk to the Backend?**
**A:** Through **Axios** requests.
```javascript
const response = await axios.post('/api/upload', formData);
```
These requests are asynchronous (Promises/async-await), meaning the UI doesn't freeze while waiting for the server.
