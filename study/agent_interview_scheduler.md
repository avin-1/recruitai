# Agent Deep Dive: Interview Scheduler Agent

## 1. Introduction and Architectural Role

The Interview Scheduler Agent acts as the intelligent "Executive Assistant" of the platform. Running as a dedicated microservice on port 5002, it automates one of the most tedious aspects of recruitment: finding a mutual time to meet. By integrating directly with Google Calendar via the Google Cloud Platform (GCP) APIs, it solves the mathematical "Constraint Satisfaction Problem" of scheduling. It ensures that interviews are booked only when the HR manager is truly free, respecting working hours and avoiding double bookings.

## 2. The Core Logic: Constraint Satisfaction

The heart of this agent is an algorithmic engine (`compute_free_slots`) that views time not as a continuous flow, but as a series of discrete blocks.

**The Time-Finding Algorithm:**
The algorithm operates on a simple but powerful heuristic. It takes the HR manager's "Busy Slots" (e.g., a meeting from 9:00 to 10:00) and the defined "Working Window" (9:00 AM to 5:00 PM). It then iterates through the day in 30-minute increments, effectively asking a series of questions: "Is 9:00 to 9:30 free? No, it overlaps with the meeting. Okay, jump to the end of the meeting. Is 10:00 to 10:30 free? Yes? Save it." This "Greedy" approach ensures that we find every possible gap in the schedule. It creates a robust list of `free_slots`, which are then presented to the system as valid interview options.

**The Automatic Meet Link Generation:**
Once a slot is selected, the agent moves from analysis to action. It sends a request to the Google Calendar API to insert an event. Crucially, it sets the `conferenceDataVersion=1` parameter. This flag instructs Google to automatically provision a **Google Meet** video conference link and attach it to the calendar invite. This seamless integration saves the recruiter from manually creating and pasting Zoom links, further automating the workflow.

## 3. Security and Authentication: The OAuth Story

To interact with a user's private calendar, the system relies on the **OAuth 2.0** protocol, a standard for secure delegation.

**The Token Lifecycle:**
The authentication process begins with a "Handshake." The app sends its Client ID to Google, which asks the user, "Do you trust RecruitAI to manage your calendar?" Upon consent, the system receives a `refresh_token`—a long-lived secret stored securely in `token.json`. The agent uses this refresh token to continually request short-lived `access_tokens` (valid for 1 hour). This "Silent Refresh" mechanism ensures that the agent can run indefinitely in the background without nagging the user to log in every hour, balancing security with user experience.

**Failure Recovery:**
If a user revokes the app's permission in their Google Security settings, the `refresh_token` becomes invalid. The next time the agent tries to fetch an access token, it will trigger a `RefreshError`. The code is designed to catch this specific exception and halt operations safely, logging the error so an administrator can re-authenticate. This fail-safe prevents the system from entering a crash loop when credentials go stale.

## 4. Algorithms Under the Hood: A Trace

To visualize the scheduling logic, imagine a scenario where the HR manager works a short day from 9:00 to 12:00, with existing meetings at 9:15-9:45 and 11:00-11:30.
1.  **Probe 1:** The algorithm checks 9:00. It sees a conflict at 9:15. It rejects the slot and jumps its pointer to 9:45 (the end of the conflict).
2.  **Probe 2:** It checks 9:45 to 10:15. The path is clear. It saves **09:45**.
3.  **Probe 3:** It advances 30 minutes to 10:15. The slot 10:15-10:45 is clear. It saves **10:15**.
4.  **Probe 4:** It advances to 10:45. Checking the window 10:45-11:15, it hits the 11:00 meeting. Reject.
5.  **Probe 5:** It jumps to 11:30. The window 11:30-12:00 is clear. It saves **11:30**.
The result is a clean list `['09:45', '10:15', '11:30']`, perfectly navigating the fragmented schedule.

## 5. Advanced Topics and Defense Questions

**Race Conditions:**
# Agent Deep Dive: Interview Scheduler Agent

## 1. Introduction and Architectural Role

The Interview Scheduler Agent acts as the intelligent "Executive Assistant" of the platform. Running as a dedicated microservice on port 5002, it automates one of the most tedious aspects of recruitment: finding a mutual time to meet. By integrating directly with Google Calendar via the Google Cloud Platform (GCP) APIs, it solves the mathematical "Constraint Satisfaction Problem" of scheduling. It ensures that interviews are booked only when the HR manager is truly free, respecting working hours and avoiding double bookings.

## 2. The Core Logic: Constraint Satisfaction

The heart of this agent is an algorithmic engine (`compute_free_slots`) that views time not as a continuous flow, but as a series of discrete blocks.

**The Time-Finding Algorithm:**
The algorithm operates on a simple but powerful heuristic. It takes the HR manager's "Busy Slots" (e.g., a meeting from 9:00 to 10:00) and the defined "Working Window" (9:00 AM to 5:00 PM). It then iterates through the day in 30-minute increments, effectively asking a series of questions: "Is 9:00 to 9:30 free? No, it overlaps with the meeting. Okay, jump to the end of the meeting. Is 10:00 to 10:30 free? Yes? Save it." This "Greedy" approach ensures that we find every possible gap in the schedule. It creates a robust list of `free_slots`, which are then presented to the system as valid interview options.

**The Automatic Meet Link Generation:**
Once a slot is selected, the agent moves from analysis to action. It sends a request to the Google Calendar API to insert an event. Crucially, it sets the `conferenceDataVersion=1` parameter. This flag instructs Google to automatically provision a **Google Meet** video conference link and attach it to the calendar invite. This seamless integration saves the recruiter from manually creating and pasting Zoom links, further automating the workflow.

## 3. Security and Authentication: The OAuth Story

To interact with a user's private calendar, the system relies on the **OAuth 2.0** protocol, a standard for secure delegation.

**The Token Lifecycle:**
The authentication process begins with a "Handshake." The app sends its Client ID to Google, which asks the user, "Do you trust RecruitAI to manage your calendar?" Upon consent, the system receives a `refresh_token`—a long-lived secret stored securely in `token.json`. The agent uses this refresh token to continually request short-lived `access_tokens` (valid for 1 hour). This "Silent Refresh" mechanism ensures that the agent can run indefinitely in the background without nagging the user to log in every hour, balancing security with user experience.

**Failure Recovery:**
If a user revokes the app's permission in their Google Security settings, the `refresh_token` becomes invalid. The next time the agent tries to fetch an access token, it will trigger a `RefreshError`. The code is designed to catch this specific exception and halt operations safely, logging the error so an administrator can re-authenticate. This fail-safe prevents the system from entering a crash loop when credentials go stale.

## 4. Algorithms Under the Hood: A Trace

To visualize the scheduling logic, imagine a scenario where the HR manager works a short day from 9:00 to 12:00, with existing meetings at 9:15-9:45 and 11:00-11:30.
1.  **Probe 1:** The algorithm checks 9:00. It sees a conflict at 9:15. It rejects the slot and jumps its pointer to 9:45 (the end of the conflict).
2.  **Probe 2:** It checks 9:45 to 10:15. The path is clear. It saves **09:45**.
3.  **Probe 3:** It advances 30 minutes to 10:15. The slot 10:15-10:45 is clear. It saves **10:15**.
4.  **Probe 4:** It advances to 10:45. Checking the window 10:45-11:15, it hits the 11:00 meeting. Reject.
5.  **Probe 5:** It jumps to 11:30. The window 11:30-12:00 is clear. It saves **11:30**.
The result is a clean list `['09:45', '10:15', '11:30']`, perfectly navigating the fragmented schedule.

## 5. Advanced Topics and Defense Questions

**Race Conditions:**
A critical theoretical flaw in any scheduling system is the "Race Condition." If two candidates try to book the 10:00 slot at the exact same millisecond, the system might read the calendar, see it as free for both, and insert two events. In a robust production environment, we would use a **Distributed Lock** (like Redis Redlock) or a Database Transaction to "Lock" the slot while writing. For our prototype, we rely on the low volume of traffic making this statistically unlikely.

**Computational Complexity:**
Critics might argue that checking every 30-minute block is inefficient ($O(N)$). However, scale matters. For a 5-day work week, there are only about 80 blocks to check. A modern CPU can process this in microseconds. Implementing a complex "Interval Tree" data structure would be a case of "Premature Optimization"—adding complexity where no performance bottleneck exists.

**Timezone Management:**
Managing timezones is notoriously difficult. Our system mitigates this by normalizing all data to **UTC** (Coordinated Universal Time) within the backend logic. The Google Calendar API stores events in UTC, and our agent respects the timezone offset configured in the HR Manager's calendar settings. This ensures that we never accidentally book a meeting at 3:00 AM local time.
## 8. Architectural Defense: Why This Technology?

**Why Google Calendar API vs. Building Our Own Calendar?**
You chose Google.
- **Argument:** "User Adoption. Asking an HR Manager to switch to a custom 'RecruitAI Calendar' is a non-starter. They live in Google Calendar. By integrating where the user *already is*, we reduce friction. Technically, Google also handles the hard parts: Timezones, Mobile Notifications, and Video Link generation (Meet), which would take months to build from scratch."

**Why Greedy Algorithm vs. Linear Programming?**
You chose Greedy.
- **Argument:** "Sufficiency. We are not trying to optimize the entire company's workforce schedule (which is an NP-Hard problem requiring Linear Programming). We are just finding *one* open slot for *one* interview. A Greedy approach (Iterate -> Check -> Book First Available) is $O(N)$ implementation complexity and works perfectly for this use case. It is the pragmatic engineering choice."

**Why OAuth 2.0 vs. Service Account?**
You chose OAuth.
- **Argument:** "Permission Scope. A Service Account acts as a 'God User' or a rigid bot. OAuth 2.0 allows the *User* (HR Manager) to grant access to *their specific* calendar. It respects the principle of least privilege and allows the application to act on behalf of the user, rather than as a separate entity."
