Short version:

* **LinkedIn** → has an official, well-documented *Job Posting API* (but it’s **partner-only**). I’ll give you links + a dev-ready integration brief.
* **Naukri** → also has a job-posting API, but it’s **not publicly documented**; you only get docs once you’re an approved partner/employer. I’ll show you what to ask them for and how to structure your code so it’s easy to plug in when you get their spec.

You can copy-paste the “**Hand-off for Agent**” sections directly to your implementation agent.

---

## 1. LinkedIn Job Posting API – Documentation + Tech Overview

### 1.1 Official docs & collections

Give these URLs to your dev/agent:

* **Job Posting API overview (Talent)** – main functional description ([Microsoft Learn][1])
* **Create Jobs – `/simpleJobPosting`** (how to create jobs, request bodies, etc.) ([Microsoft Learn][2])
* **Update / Renew / Close Jobs** ([Microsoft Learn][3])
* **LinkedIn Talent Solutions – product catalog** (Job Posting, Apply Connect, etc.) ([LinkedIn Developer Solutions][4])
* **Job Posting Postman collection** (ready-made requests) ([Postman][5])
* **Getting access to LinkedIn APIs (OAuth + permissions)** ([Microsoft Learn][6])
* **Job Posting API Terms (legal + allowed use cases)** ([LinkedIn][7])

> Important: LinkedIn Job Posting APIs are **not open to all apps**. You need to be an approved **Talent Solutions / Job Posting partner**, or a customer with the right Recruiter contract. ([Microsoft Learn][6])

---

### 1.2 Core concepts

**Main endpoint (REST style)** ([Microsoft Learn][3])

* `POST https://api.linkedin.com/v2/simpleJobPostings`
* (There is also `https://api.linkedin.com/rest/simpleJobPostings` as part of the newer REST style.)

This endpoint is used to **create, update, renew, and close** jobs by changing a field like `jobPostingOperationType` in the body. ([Microsoft Learn][3])

**Auth:**

* OAuth 2.0 (LinkedIn specific implementation).
* Depending on use case, you’ll use:

  * **2-legged (application)**: server-to-server calls with app credentials.
  * **3-legged (member)**: when acting on behalf of a Recruiter / organization. ([Microsoft Learn][8])
* Required scopes are part of LinkedIn’s **Talent / Job Posting program**, not the standard open scopes.

**Job lifecycle (high level)** ([Microsoft Learn][1])

1. **Create** job (`jobPostingOperationType = CREATE`).
2. **Update / Renew** (`jobPostingOperationType = UPDATE` or `RENEW`).
3. **Close** (`jobPostingOperationType = CLOSE`).
4. Each POST usually returns an **async task**; you call a **status endpoint** to see if the operation succeeded.

---

### 1.3 Request schema (simplified skeleton)

Paraphrased structure (not copied from docs) based on `/simpleJobPostings` documentation: ([Microsoft Learn][2])

```json
{
  "elements": [
    {
      "externalJobPostingId": "your-system-job-id-123",
      "jobPostingOperationType": "CREATE",   // or UPDATE, RENEW, CLOSE
      "job": {
        "title": "Senior Backend Engineer",
        "description": {
          "text": "Full job description as plain text or limited markup"
        },
        "company": {
          "companyApplyUrl": "https://yourcompany.com/careers/123",
          "companyName": "Your Company Pvt Ltd",
          "companyDescription": "Optional employer branding text"
        },
        "workplaceTypes": ["REMOTE"],        // REMOTE / HYBRID / ONSITE
        "location": {
          "country": "IN",
          "city": "Bengaluru",
          "postalCode": "560001"
        },
        "jobFunctions": ["ENGINEERING"],
        "industries": ["INTERNET"],
        "employmentType": "FULL_TIME",
        "experienceLevel": "MID_SENIOR",
        "salary": {
          "min": 1500000,
          "max": 2500000,
          "currencyCode": "INR",
          "timePeriod": "YEAR"
        }
        // plus other fields defined in the foundation schema and any extensions
      },
      "promotedJobOptions": {
        "jobPostingType": "BASIC"            // or PROMOTED if allowed for your contract
      }
    }
  ]
}
```

> The *exact* field names, allowed enums, and nested objects must be taken from the official **Create Jobs** + **Job Posting Postman** docs. The above is just a structural guide. ([Microsoft Learn][2])

---

### 1.4 Typical interaction flow

**Step 1 – Access + app setup**

1. Apply / confirm your **Job Posting** product access in LinkedIn Developer / Talent Solutions. ([LinkedIn Developer Solutions][9])
2. Register app, get **Client ID** and **Client Secret**. ([Microsoft Learn][6])
3. Configure OAuth redirect URL(s).

**Step 2 – OAuth 2.0**

* Implement:

  * **Auth URL** (user / admin consents → you get `code`).
  * **Token URL** (exchange `code` for `access_token`).
* Use `access_token` in `Authorization: Bearer <token>` for API calls. ([Microsoft Learn][8])

**Step 3 – Create job(s)**

* POST to `/simpleJobPostings` with:

  * `x-restli-method: batch_create` header (for batch operations).
  * Request body with `elements` array (see above skeleton). ([Microsoft Learn][3])
* Response includes:

  * Task URN / ID to check status.

**Step 4 – Poll operation status**

* Call the **task status** endpoint shown in the docs/Postman collection to confirm success or error and capture:

  * LinkedIn job ID (e.g. `urn:li:jobPosting:123456789`).
  * Any error codes.

**Step 5 – Update / renew / close**

* Same `/simpleJobPostings` endpoint.
* Set `jobPostingOperationType` to `UPDATE`, `RENEW` or `CLOSE` and include the relevant fields (usually same `externalJobPostingId` to identify the job). ([Microsoft Learn][3])

**Step 6 – Error handling & throttling**

* Implement handling for:

  * 4xx errors → auth, invalid fields, permissions.
  * 429 → rate-limit, apply retry-after.
  * 5xx → transient LinkedIn issues.

---

### 1.5 Hand-off for Agent – LinkedIn (you can copy this block)

> **Target**: LinkedIn Job Posting API (Talent Solutions – `/simpleJobPostings`).
> **Docs**:
>
> * Job Posting API overview
> * Create / Update / Renew / Close Jobs (`/simpleJobPostings`)
> * LinkedIn Talent Solutions Job Posting Postman collection
> * OAuth access docs for LinkedIn APIs
> * Job Posting API Terms
>
> **Access model**
>
> * Assume we will have an approved LinkedIn Talent / Job Posting integration with appropriate permissions.
> * Use OAuth 2.0 (application or 3-legged, depending on LinkedIn’s guidance for our account).
>
> **What to implement**
>
> 1. **Config**
>
>    * Client ID / Client Secret
>    * Redirect URI (for 3-legged, if needed)
>    * Contract / organization identifiers required by LinkedIn (e.g. Recruiter contract ID, org URN, etc.).
> 2. **OAuth module**
>
>    * Generate authorize URL.
>    * Exchange authorization code → access token.
>    * Token storage & refresh.
> 3. **Job Posting client**
>
>    * `createJob(jobData)`
>
>      * Maps our internal Job model → LinkedIn foundation schema (title, description, location, workplace type, salary, etc.).
>      * Calls `POST /simpleJobPostings` with `jobPostingOperationType = CREATE`.
>      * Parses async task response and stores LinkedIn job URN + status.
>    * `updateJob(jobData)`
>
>      * Same endpoint with `jobPostingOperationType = UPDATE`.
>    * `renewJob(jobId)`
>
>      * `jobPostingOperationType = RENEW`.
>    * `closeJob(jobId)`
>
>      * `jobPostingOperationType = CLOSE`.
>    * `getJobTaskStatus(taskId)`
>
>      * Poll task endpoint from docs; update local status (CREATED / FAILED / CLOSED etc.).
> 4. **Error + rate limit handling**
>
>    * Handle 4xx/5xx according to LinkedIn docs.
>    * Expose structured error codes/messages back to the core app.
> 5. **Security & compliance**
>
>    * Respect LinkedIn Job Posting API Terms.
>    * No scraping / unsupported endpoints.

---

## 2. Naukri.com Job Posting API – Reality & How to Work With It

### 2.1 Public docs vs real situation

For Naukri, there is **no open public developer portal** like LinkedIn.

What we know from ATS integrations (Greenhouse, Workable, Darwinbox, etc.):

* These systems can **post jobs directly to Naukri** once an employer gets an API key from Naukri. ([Greenhouse Support][10])
* Workable, for example, asks the employer to **enter an API key obtained from Naukri** into their settings, after which jobs created in Workable are synced to Naukri. ([Workable Help][11])
* Naukri positions this under **Naukri Talent Cloud / hiring automation** offerings, not as a generic public API. ([Naukri][12])

So:

> **Naukri’s job-posting API is a private / partner API.** You only get the detailed REST spec once you’ve signed a contract or enabled the integration from a Naukri employer account.

Because of that, I can’t give you accurate endpoint URLs or exact request schema without guessing (and guessing API details would be dangerous for the dev).

What I *can* give you:

* How these APIs typically look.
* A **checklist of what to request from Naukri**.
* An abstraction your agent can implement now, and then plug in Naukri once you get the official docs.

---

### 2.2 Typical shape of Naukri job APIs (inferred from partner docs)

From ATS integration descriptions: ([Greenhouse Support][10])

* There is an **API key** or similar token issued by Naukri to the employer / ATS partner.
* Jobs created in the ATS are **“synced” to Naukri** (one-click or automatic based on business rules).
* Naukri returns:

  * A **job post URL** (so the ATS can show “View on Naukri”). ([Greenhouse Integrations][13])
  * **Errors** (if posting fails).
  * Sometimes **basic applicant info** flowing back to the ATS.

Most likely they expose:

* `POST /jobs` (or similar) → draft/post job.
* `PUT/PATCH /jobs/{id}` → update.
* `DELETE /jobs/{id}` or `POST /jobs/{id}/close` → close.
* `GET /jobs/{id}` → fetch status / view URL.
* Webhook(s) or polling endpoint for applications.

**But again: exact paths/fields must come from Naukri’s official documentation for your account**, not guessed.

---

### 2.3 What you should ask Naukri for

When you talk to Naukri (usually via your sales / account manager or Talent Cloud support), ask explicitly:

> “We’re building a direct integration to post jobs from our system to Naukri.com. Please share the **official API documentation** for job posting and lifecycle management.”

Specifically request:

1. **Auth details**

   * Is it API key in header? OAuth2? Something else?
   * Example auth header (e.g. `Authorization: Bearer <token>` or `x-api-key` etc.).

2. **Base URL(s)**

   * Sandbox / staging base URL.
   * Production base URL.

3. **Endpoints for:**

   * Create job.
   * Update job.
   * Close / delete job.
   * Get job status & public job URL.
   * Fetch applicants / application counts (if supported).
   * Webhooks (if they push candidate data).

4. **Schema & validation rules**

   * Required fields: title, description, experience range, location, salary, industry, functional area, role, education, etc.
   * Valid values / enums for:

     * Job type, shift, employment type, location codes, industry codes, etc.
   * Limits:

     * Max description length.
     * Max number of skills / tags.

5. **Rate limits & quotas**

6. **Error format**

   * Structure of error responses (fields like `code`, `message`, `details`).

Once they send that as a PDF/Word/postman collection, your agent can implement it exactly.

---

### 2.4 Hand-off for Agent – Naukri (copy this too)

> **Status**: Naukri job posting API is **partner / employer-only**. We’ll receive the **real docs from Naukri** later. For now, please implement a clean provider abstraction and leave the Naukri implementation as a separate module that consumes their spec once we have it.
>
> **What to assume conceptually**
>
> * Authentication: likely API key or token-based.
> * REST JSON API with endpoints to: create, update, close, and query jobs.
> * Naukri returns a **Naukri job ID** and **public URL** for the posting, plus errors on failure.
>
> **What to build now**
>
> 1. **Generic JobProvider interface** (or similar abstraction):
>
>    * `postJob(jobData): ProviderJobResult`
>    * `updateJob(providerJobId, jobData): ProviderJobResult`
>    * `closeJob(providerJobId): ProviderJobResult`
>    * `getJobStatus(providerJobId): ProviderJobStatus`
> 2. **LinkedInJobProvider** – implement using LinkedIn spec above.
> 3. **NaukriJobProvider** – create the class/structure, but:
>
>    * Leave HTTP details in a config file or env-driven constants.
>    * Write TODO markers where we need:
>
>      * Base URL
>      * Auth header
>      * Exact JSON schema
>      * Error mapping
> 4. Once Naukri sends their documentation, we:
>
>    * Plug their base URLs and paths into `NaukriJobProvider`.
>    * Map our internal job model → Naukri’s fields.
>    * Map Naukri response → `ProviderJobResult` and `ProviderJobStatus`.
>
> **Important**: Do not hardcode any guessed Naukri endpoints or field names. Wait for the official spec.

---

## 3. If you want, I can…

If you paste **Naukri’s API PDF / Postman collection** once you get it, I can:

* Extract the exact endpoints and fields.
* Design **ready-to-use Node.js / Python client code**.
* Or generate a **one-page internal API contract** for your project repo.

For now, the safest thing you can hand to your agent is:

1. The **LinkedIn links + spec** above.
2. The **Naukri “we need the official docs from them” checklist + abstraction**.

[1]: https://learn.microsoft.com/en-us/linkedin/talent/job-postings/api/overview?view=li-lts-2025-10&utm_source=chatgpt.com "Job Posting API Overview - LinkedIn"
[2]: https://learn.microsoft.com/en-us/linkedin/talent/job-postings/api/create-jobs?view=li-lts-2025-10&utm_source=chatgpt.com "Create Jobs - LinkedIn"
[3]: https://learn.microsoft.com/en-us/linkedin/talent/job-postings/api/update-renew-jobs?view=li-lts-2025-10&utm_source=chatgpt.com "Update and Renew Jobs - LinkedIn"
[4]: https://developer.linkedin.com/product-catalog/talent?utm_source=chatgpt.com "LinkedIn API | Talent"
[5]: https://www.postman.com/linkedin-developer-apis/linkedin-talent-solutions/documentation/ycpzuyn/job-posting?utm_source=chatgpt.com "Job Posting | Documentation | Postman API Network"
[6]: https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access?utm_source=chatgpt.com "Getting Access to LinkedIn APIs"
[7]: https://www.linkedin.com/legal/l/job-posting-api-terms?utm_source=chatgpt.com "LinkedIn Job Posting API Terms"
[8]: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication?utm_source=chatgpt.com "Authenticating with OAuth 2.0 Overview - LinkedIn"
[9]: https://developer.linkedin.com/product-catalog?utm_source=chatgpt.com "LinkedIn API | Products"
[10]: https://support.greenhouse.io/hc/en-us/articles/16297968058651-Naukri-integration?utm_source=chatgpt.com "Naukri integration"
[11]: https://help.workable.com/hc/en-us/articles/26298085189271-Integrating-with-Naukri?utm_source=chatgpt.com "Integrating with Naukri"
[12]: https://www.naukri.com/naukri-talent-cloud?utm_source=chatgpt.com "Naukri Talent Cloud"
[13]: https://integrations.greenhouse.com/partners/naukri?utm_source=chatgpt.com "Naukri - Greenhouse Partner Directory"
