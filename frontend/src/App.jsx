import React, { useState, useEffect } from 'react';

// Main App Component
const App = () => {
    // API base - change if your backend runs elsewhere
    const API_BASE = "http://localhost:5000";

    // State to manage the current page and login status
    const [currentPage, setCurrentPage] = useState('home');
    const [message, setMessage] = useState('');

    // load user from localStorage if present
    const [user, setUser] = useState(() => {
        try {
            const u = localStorage.getItem('user');
            return u ? JSON.parse(u) : null;
        } catch {
            return null;
        }
    });

    // Dummy data for job listings (unchanged)
    const jobs = [
        { id: 1, title: "Frontend Developer", company: "ABC Corp", location: "Mumbai", description: "Build modern web interfaces with React, collaborate with designers and engineers, and drive UI innovation." },
        { id: 2, title: "Backend Developer", company: "XYZ Ltd", location: "Pune", description: "Architect scalable APIs using Node.js, integrate databases, and optimize backend performance for high-traffic systems." },
        { id: 3, title: "Fullstack Engineer", company: "Tech Solutions", location: "Bangalore", description: "Work across frontend and backend, deploy end-to-end solutions, and manage deployment with DevOps tools." },
        { id: 4, title: "HR Executive", company: "InnovateHub", location: "Delhi", description: "Manage recruitment and onboarding processes, build engagement programs, and support talent growth initiatives." },
    ];

    // Function to handle page navigation
    const handleNavigation = (page) => {
        setCurrentPage(page);
        setMessage(''); // Clear any messages on navigation
    };

    // Logout
    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setMessage('Logged out successfully.');
        // optionally navigate to home
        setTimeout(() => handleNavigation('home'), 600);
    };

    // --- Page Components ---

    const MessageDisplay = ({ text, type }) => {
        if (!text) return null;
        const baseStyle = "p-4 rounded-xl text-center font-semibold mb-4 mx-auto max-w-xl";
        const styles = {
            success: "bg-green-100 text-green-700",
            error: "bg-red-100 text-red-700",
            info: "bg-blue-100 text-blue-700"
        };
        const klass = styles[type] || styles.info;
        return <div className={`${baseStyle} ${klass}`}>{text}</div>;
    };

    const HomePage = () => {
        const jobCards = jobs.map(job => (
            <div key={job.id} className="bg-white rounded-2xl shadow-lg border-t-8 border-indigo-500 p-6 hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 flex flex-col justify-between">
                <div>
                    <h3 className="text-xl font-bold text-indigo-700 mb-2">{job.title}</h3>
                    <p className="text-gray-600 font-semibold mb-1 flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect width="18" height="18" x="3" y="3" rx="2"></rect>
                            <path d="M12 12h.01"></path>
                            <path d="M16 12h.01"></path>
                            <path d="M8 12h.01"></path>
                        </svg>{job.company}
                    </p>
                    <p className="text-gray-500 mb-4 flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                        </svg>{job.location}
                    </p>
                    <p className="mb-3 text-base text-gray-700">{job.description}</p>
                </div>
                <button className="bg-indigo-600 text-white py-2 px-4 rounded-xl mt-4 font-semibold shadow hover:bg-indigo-700 transition transform hover:scale-105">
                    Apply Now
                </button>
            </div>
        ));

        return (
            <>
                {/* Hero Banner */}
                <section className="text-center py-16 px-6 bg-gradient-to-r from-indigo-600 via-sky-400 to-purple-600 text-white rounded-b-3xl shadow-2xl mt-4 transform -skew-y-1">
                    <div className="transform skew-y-1">
                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold mb-4 drop-shadow-lg">
                            Welcome to RecruitAI
                        </h1>
                        <p className="text-base sm:text-lg lg:text-xl max-w-4xl mx-auto mb-8 font-light">
                            RecruitAI revolutionizes hiring and talent management with AI-powered job recommendations, seamless applicant tracking, and robust analytics. Connect talent and opportunity for high-growth teams.
                        </p>
                        <div className="flex justify-center flex-wrap gap-4">
                            <button className="bg-white text-indigo-700 font-bold px-8 py-3 rounded-full shadow-lg hover:bg-indigo-100 transition-all transform hover:scale-105">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block mr-2"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
                                Search Jobs
                            </button>
                            <button className="bg-indigo-800 text-white font-bold px-8 py-3 rounded-full hover:bg-indigo-900 shadow-lg border-2 border-transparent hover:border-white transition-all transform hover:scale-105" onClick={() => handleNavigation('signup')}>
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block mr-2"><path d="M12 2v20"></path><path d="M18 10h-4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-4"></path><path d="M12 22V2"></path><path d="M6 14H8a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2z"></path></svg>
                                Post a Job
                            </button>
                        </div>
                    </div>
                </section>

                {/* About Section */}
                <section className="relative -mt-16 z-10 max-w-6xl mx-auto bg-white rounded-3xl shadow-xl p-8 md:p-12 mb-12 transform hover:scale-100 transition-all duration-300">
                    <h2 className="text-3xl font-bold text-center text-indigo-700 mb-4">Empowering HR for the Future</h2>
                    <p className="text-lg text-gray-700 mb-4 text-center">
                        RecruitAI combines advanced AI matching algorithms with seamless workflows to help companies find and retain the best talent. Our customizable dashboard, automated interview scheduling, and analytics deliver a superior recruitment experience.
                    </p>
                    <p className="text-gray-600 text-center">
                        Whether you're scaling a startup or optimizing a large enterprise, RecruitAI provides secure onboarding, easy role management, and real-time candidate insights—all in a user-friendly portal.
                    </p>
                </section>

                {/* Job Cards Section */}
                <section className="max-w-7xl mx-auto px-4 py-8 mb-14">
                    <h2 className="text-3xl font-bold text-indigo-700 mb-8 text-center">Featured Job Opportunities</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {jobCards}
                    </div>
                </section>

                {/* Why Choose RecruitAI? Section */}
                <section className="bg-gradient-to-r from-sky-200 via-white to-indigo-100 rounded-3xl shadow-xl py-10 mb-12 px-6">
                    <h2 className="text-3xl font-bold text-center text-indigo-700 mb-8">Features That Set Us Apart</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-10 px-8">
                        <div className="bg-white p-7 rounded-3xl shadow-lg border-b-4 border-blue-400 text-center transform hover:scale-105 transition-all duration-300">
                            <div className="w-16 h-16 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mx-auto mb-4">
                                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4.5 16.5c-1.5 1.26-2.5 2-2.5 5.5v2l2-2h4.5a2 2 0 0 0 2-2z"></path><path d="M12 13V2.5l5.5 5.5"></path></svg>
                            </div>
                            <h3 className="font-bold text-xl text-blue-700 mb-2">Smart Talent Matching</h3>
                            <p className="text-gray-700">AI recommends ideal candidates based on your job requirements and company culture fit.</p>
                        </div>
                        <div className="bg-white p-7 rounded-3xl shadow-lg border-b-4 border-purple-400 text-center transform hover:scale-105 transition-all duration-300">
                            <div className="w-16 h-16 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mx-auto mb-4">
                                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                            </div>
                            <h3 className="font-bold text-xl text-purple-700 mb-2">Easy Interview Scheduling</h3>
                            <p className="text-gray-700">Automate interview workflows and communicate with candidates instantly, all inside the dashboard.</p>
                        </div>
                        <div className="bg-white p-7 rounded-3xl shadow-lg border-b-4 border-green-400 text-center transform hover:scale-105 transition-all duration-300">
                            <div className="w-16 h-16 rounded-full bg-green-100 text-green-600 flex items-center justify-center mx-auto mb-4">
                                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                            </div>
                            <h3 className="font-bold text-xl text-green-700 mb-2">Real-Time Analytics</h3>
                            <p className="text-gray-700">Track applications, analyze team performance, and view actionable hiring analytics to improve decision-making.</p>
                        </div>
                    </div>
                </section>

                {/* Testimonials Section */}
                <section className="max-w-6xl mx-auto px-4 py-8 mb-10">
                    <h2 className="text-3xl font-bold text-indigo-700 mb-8 text-center">What Our Users Say</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white p-6 rounded-2xl shadow-xl border-t-4 border-blue-400 transform hover:scale-105 transition-all duration-300">
                            <p className="text-gray-700 mb-4 italic">“RecruitAI helped us reduce hiring time by 40% and find the most talented engineers for our team!”</p>
                            <div className="font-bold text-blue-700">Priya Shah</div>
                            <div className="text-gray-500 text-sm">HR Manager, ABC Corp</div>
                        </div>
                        <div className="bg-white p-6 rounded-2xl shadow-xl border-t-4 border-indigo-400 transform hover:scale-105 transition-all duration-300">
                            <p className="text-gray-700 mb-4 italic">“The dashboard is intuitive and the matching accuracy is outstanding. My team loves it.”</p>
                            <div className="font-bold text-indigo-700">Rahul Patil</div>
                            <div className="text-gray-500 text-sm">Lead Recruiter, XYZ Ltd</div>
                        </div>
                        <div className="bg-white p-6 rounded-2xl shadow-xl border-t-4 border-purple-400 transform hover:scale-105 transition-all duration-300">
                            <p className="text-gray-700 mb-4 italic">“Managing a large candidate pool is easy and our onboarding is faster than ever.”</p>
                            <div className="font-bold text-purple-700">Neha Verma</div>
                            <div className="text-gray-500 text-sm">Talent Acquisition, InnovateHub</div>
                        </div>
                    </div>
                </section>

                {/* Contact & Call to Action */}
                <section className="bg-white max-w-4xl mx-auto rounded-3xl shadow-xl p-8 mb-12 text-center transform hover:scale-100 transition-all duration-300">
                    <h2 className="text-3xl font-bold text-indigo-700 mb-4">Ready to empower your HR?</h2>
                    <p className="text-gray-600 mb-6 max-w-xl mx-auto">
                        Join RecruitAI today and experience seamless hiring, smart matching, and powerful management tools.
                    </p>
                    <button onClick={() => handleNavigation('signup')} className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-8 rounded-full font-bold shadow-lg hover:from-indigo-700 hover:to-purple-700 transition-all transform hover:scale-105">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block mr-2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        Join Us Today
                    </button>
                </section>
            </>
        );
    };

    const LoginPage = () => {
        const handleLogin = async (e) => {
            e.preventDefault();
            const email = e.target[0].value;
            const password = e.target[1].value;

            try {
                const res = await fetch(`${API_BASE}/api/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                });
                const data = await res.json();
                if (res.ok) {
                    // store token and user
                    localStorage.setItem("token", data.token);
                    localStorage.setItem("user", JSON.stringify(data.user));
                    setUser(data.user);
                    setMessage("Login successful!");
                    // navigate to home after showing message briefly
                    setTimeout(() => handleNavigation("home"), 700);
                } else {
                    setMessage(data.error || data.message || "Login failed");
                }
            } catch (err) {
                console.error(err);
                setMessage("Network error. Please try again.");
            }
        };

        return (
            <div className="flex flex-col items-center justify-center p-8">
                <div className="bg-white p-8 rounded-3xl shadow-2xl w-full max-w-md mx-auto my-12 transform transition-all duration-300 hover:scale-105">
                    <h2 className="text-3xl font-bold text-center text-indigo-700 mb-6">Login</h2>
                    <MessageDisplay text={message} type="success" />
                    <form onSubmit={handleLogin}>
                        <div className="mb-4">
                            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="login-email">Email Address</label>
                            <input
                                className="shadow-inner appearance-none border rounded-xl w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-all"
                                id="login-email"
                                type="email"
                                placeholder="you@example.com"
                                required
                            />
                        </div>
                        <div className="mb-6">
                            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="login-password">Password</label>
                            <input
                                className="shadow-inner appearance-none border rounded-xl w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-all"
                                id="login-password"
                                type="password"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                        <div className="flex flex-col items-center justify-between gap-4">
                            <button
                                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-xl focus:outline-none focus:shadow-outline transition transform hover:scale-105"
                                type="submit"
                            >
                                Log In
                            </button>
                            <button
                                className="w-full text-indigo-600 font-semibold py-2 px-4 rounded-xl hover:bg-indigo-50 transition transform hover:scale-105"
                                onClick={() => handleNavigation('signup')}
                                type="button"
                            >
                                Don't have an account? Sign Up
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        );
    };

    const SignupPage = () => {
        const handleSignup = async (e) => {
            e.preventDefault();
            const name = e.target[0].value;
            const email = e.target[1].value;
            const password = e.target[2].value;

            try {
                const res = await fetch(`${API_BASE}/api/auth/signup`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, email, password }),
                });
                const data = await res.json();
                if (res.ok) {
                    setMessage("Account created successfully! Please log in.");
                    // navigate to login after short delay so message is visible
                    setTimeout(() => handleNavigation("login"), 800);
                } else {
                    setMessage(data.error || data.message || "Signup failed");
                }
            } catch (err) {
                console.error(err);
                setMessage("Network error. Please try again.");
            }
        };

        return (
            <div className="flex flex-col items-center justify-center p-8">
                <div className="bg-white p-8 rounded-3xl shadow-2xl w-full max-w-md mx-auto my-12 transform transition-all duration-300 hover:scale-105">
                    <h2 className="text-3xl font-bold text-center text-indigo-700 mb-6">Sign Up</h2>
                    <form onSubmit={handleSignup}>
                        <div className="mb-4">
                            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="signup-name">Full Name</label>
                            <input
                                className="shadow-inner appearance-none border rounded-xl w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-all"
                                id="signup-name"
                                type="text"
                                placeholder="John Doe"
                                required
                            />
                        </div>
                        <div className="mb-4">
                            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="signup-email">Email Address</label>
                            <input
                                className="shadow-inner appearance-none border rounded-xl w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-all"
                                id="signup-email"
                                type="email"
                                placeholder="you@example.com"
                                required
                            />
                        </div>
                        <div className="mb-6">
                            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="signup-password">Password</label>
                            <input
                                className="shadow-inner appearance-none border rounded-xl w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-all"
                                id="signup-password"
                                type="password"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                        <div className="flex flex-col items-center justify-between gap-4">
                            <button
                                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-xl focus:outline-none focus:shadow-outline transition transform hover:scale-105"
                                type="submit"
                            >
                                Create Account
                            </button>
                            <button
                                className="w-full text-indigo-600 font-semibold py-2 px-4 rounded-xl hover:bg-indigo-50 transition transform hover:scale-105"
                                onClick={() => handleNavigation('login')}
                                type="button"
                            >
                                Already have an account? Log In
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        );
    };

    // Conditional rendering based on the current page
    const renderPageContent = () => {
        switch (currentPage) {
            case 'home':
                return <HomePage />;
            case 'login':
                return <LoginPage />;
            case 'signup':
                return <SignupPage />;
            default:
                return <HomePage />;
        }
    };

    return (
        <div className="relative min-h-screen bg-gradient-to-tr from-sky-100 via-fuchsia-100 to-indigo-100 font-sans text-gray-800 antialiased">
            <style>
                {`
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
                    body {
                        font-family: 'Inter', sans-serif;
                    }
                `}
            </style>
            
            {/* Navbar */}
            <nav className="flex justify-between items-center px-4 md:px-10 py-5 bg-white bg-opacity-80 backdrop-blur-lg shadow-md sticky top-0 z-50 transition-all duration-300">
                <button onClick={() => handleNavigation('home')} className="text-2xl font-extrabold text-indigo-700 tracking-wide select-none">RecruitAI</button>
                <div className="hidden md:flex gap-8 text-gray-700 font-bold items-center">
                    <button onClick={() => handleNavigation('home')} className="hover:text-indigo-500 transition-colors">Home</button>
                    <a href="#" className="hover:text-indigo-500 transition-colors">Jobs</a>
                    <a href="#" className="hover:text-indigo-500 transition-colors">Companies</a>
                    <a href="#" className="hover:text-indigo-500 transition-colors">For Recruiters</a>

                    {user ? (
                        <>
                            <div className="text-sm text-indigo-700 font-semibold">Hi, {user.name}</div>
                            <button onClick={handleLogout} className="bg-red-500 text-white font-semibold px-4 py-2 rounded-full hover:bg-red-600 transition shadow-lg transform hover:scale-105">
                                Logout
                            </button>
                        </>
                    ) : (
                        <button onClick={() => handleNavigation('login')} className="bg-indigo-600 text-white font-semibold px-6 py-2 rounded-full hover:bg-indigo-700 transition shadow-lg transform hover:scale-105">
                            Login / Signup
                        </button>
                    )}
                </div>
                {/* Burger menu for mobile */}
                <div className="md:hidden">
                    <button className="text-gray-700 focus:outline-none">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7"></path>
                        </svg>
                    </button>
                </div>
            </nav>

            {/* Main Content Container */}
            <main id="main-content" className="container mx-auto px-4 sm:px-6 lg:px-8">
                {renderPageContent()}
            </main>

            {/* Footer */}
            <footer className="bg-indigo-900 text-white py-10 rounded-t-3xl shadow-inner mt-10 text-center">
                <div className="flex flex-col sm:flex-row justify-center items-center gap-6 md:gap-8 mb-4">
                    <button onClick={() => handleNavigation('home')} className="hover:underline hover:text-indigo-300 transition-colors">Home</button>
                    <a href="#" className="hover:underline hover:text-indigo-300 transition-colors">Jobs</a>
                    <a href="#" className="hover:underline hover:text-indigo-300 transition-colors">Companies</a>
                    <a href="#" className="hover:underline hover:text-indigo-300 transition-colors">For Recruiters</a>
                    <a href="#" className="hover:underline hover:text-indigo-300 transition-colors">Contact</a>
                </div>
                <div className="flex justify-center gap-4 text-indigo-200 mt-4">
                    {/* Social icons... (unchanged) */}
                </div>
                <p className="mt-6 text-indigo-200 text-sm md:text-base">&copy; 2025 RecruitAI. All rights reserved.</p>
            </footer>
        </div>
    );
};

export default App;
