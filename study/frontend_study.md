# Frontend Study Guide (Deep Dive)

## 1. Tech Stack Overview

Our Frontend is built on **React 19**, the latest iteration of the library, utilizing **Vite** as our build tool and **Tailwind CSS v4** for styling.

### Why this stack matters?
In the past, developers used "Create React App" (Webpack), which would bundle the entire application into a massive file before you could even see the first page. We chose **Vite** because it serves files using native browser modules (ESM). This means when you save a file, the browser updates instantly—in milliseconds—making development incredibly fast.

We pair this with **Tailwind CSS v4**. Unlike frameworks like Bootstrap that give you "cookie-cutter" components, Tailwind provides low-level utility classes. This allowed us to build a completely custom, "AI-Themed" design system with dark modes, glassmorphism, and gradients that would have been very difficult to fight Bootstrap to achieve.

## 2. Project Structure & Philosophy

The project is organized to scale. Inside `front/src/`, we separate concerns:

- `components/`: This holds our "Lego blocks"—reusable UI elements like Buttons, Cards, and Inputs. We use the **Atomic Design** principle loosely here, where small atoms (buttons) build molecules (forms) which build organisms (pages).
- `pages/`: These are the actual views the user sees. Each page manages its own state and data fetching.
- `App.jsx`: This is our "Traffic Controller." It defines the Routing Map.

### The Virtual DOM Explained
One of the key reasons we use React is the **Virtual DOM**. Imagine the browser's DOM (Document Object Model) as a slow, heavy database. Every time you change something, it has to recalculate the entire page layout. React keeps a lightweight copy of this DOM in memory (the Virtual DOM). When we update a state variable, React updates this lightweight copy, compares it to the previous version (a process called "Diffing"), and then calculates the *minimum* number of changes needed to update the real DOM. This "Reconciliation" process makes our app feel incredibly fast and responsive.

## 3. Deep Dive: Routing & Layouts

We use `react-router-dom` to handle navigation without reloading the page (Single Page Application).

### The Dashboard Layout Pattern
If you look at `App.jsx`, you'll see we wrap most routes in a `<Dashboard>` component. This is a powerful pattern. The `Dashboard` renders the persistent Sidebar and Header, and then uses the special `{children}` prop to render the specific page content (like `Home` or `Jobs`) inside the main content area. This ensures that as the user navigates, the Sidebar doesn't flicker or reload—only the main content changes.

**Routing Map:**
- **Public:** `/test/:testId` is a standalone route. We strip away the Sidebar here because candidates taking a test shouldn't see the HR admin controls.
- **Protected:** `/upload`, `/jobs` etc. are nested inside the Dashboard, creating a secure, cohesive admin experience.

## 4. Key React Concepts Used

### Hooks: `useState` and `useEffect`
- **`useState`**: This allows our functional components to "remember" things. For example, in a form, we use state to track what the user types.
- **`useEffect`**: This is our "Side Effect" manager. It mimics the old lifecycle methods like `componentDidMount`. We use it primarily to fetch data when a component first loads. For instance, "When the JobPortal loads, fetch the list of jobs from the API."

### Context API (Implied)
While we mostly use local state, libraries like `react-router-dom` use the **Context API** under the hood to pass the current URL and Navigation functions down to every link and button in the app without us having to pass props manually through every layer.

## 5. Technology Trade-offs (Why we chose X vs Y)

### React vs. Angular
- **Why React?** Angular is a full-blown "Framework" with its own strict way of doing HTTP, Routing, and State. React is a "Library" that lets us choose the best tools for the job (like Axios and React Router).
- **Benefit:** React's ecosystem is larger, and the component model is more flexible for rapid prototyping.

### Vite vs. Webpack (Create React App)
- **Why Vite?** CRA (Webpack) bundles the *entire* app before starting the server, which takes 30s+ on big apps. Vite serves files instantly using native browser modules (ESM).
- **Benefit:** Fast feedback loop. You save a file, and the browser updates in <100ms.

### Tailwind vs. Bootstrap
- **Why Tailwind?** Bootstrap gives you "Pre-made components" (like a Navbar that looks the same on every site). Tailwind gives you "Utility classes" to build *custom* designs.
- **Benefit:** We needed a "Premium, AI-themed" look (dark gradients, glassmorphism), which is hard to fight Bootstrap to achieve. Tailwind makes custom styling easy.

### Axios vs. Fetch
- **Why Axios?** It has built-in features like "Interceptors" (great for adding Auth tokens automaticlaly) and better error handling (throws on 400/500 errors automatically).
- **Benefit:** Less boilerplate code than `fetch()`.

## 6. Exam Q&A Preparation

**Q: How does the Dashboard layout work?**
**A:** In `App.jsx`, we wrap the protected routes in `<Dashboard><Routes>...</Routes></Dashboard>`. The `Dashboard` component accepts a `children` prop. It renders the fixed Sidebar and then `{children}` in the main content area. This ensures the Sidebar persists while the inner content changes.

**Q: What happens when a user navigates to `/test/123`?**
**A:** The Router matches `/test/:testId`. It renders `CandidateTest` *outside* the Dashboard layout. This is important because candidates shouldn't see the HR admin sidebar. To them, it looks like a standalone standalone test page.
