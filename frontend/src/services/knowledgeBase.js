// Local knowledge base — predefined answers for all common policy questions.
// Used as primary source when backend is unavailable, or as instant fallback.

const KB = [
  {
    keywords: ["annual leave", "leave policy", "leave entitlement", "paid leave", "vacation"],
    question: "What is the annual leave policy?",
    answer: `**Annual Leave Policy — SWS AI**

Employees at SWS AI are entitled to the following annual leave:

- **Full-time employees:** 20 working days of paid annual leave per calendar year
- **Probationary period:** Leave accrues from day one but can only be taken after completing 3 months of service
- **Carry-forward:** Up to 5 unused leave days may be carried forward to the next calendar year
- **Leave application:** Must be submitted at least 3 working days in advance via the HR portal
- **Approval:** Subject to manager approval and team availability
- **Encashment:** Unused leave beyond the carry-forward limit is not encashable

**Public Holidays** are in addition to annual leave and follow the official government calendar.`,
    sources: [{ document: "SWS AI Leave Policy", page: 1 }, { document: "SWS AI HR Policy", page: 3 }],
  },
  {
    keywords: ["sick leave", "medical leave", "sick days", "illness", "sick"],
    question: "How many sick leave days do employees get?",
    answer: `**Sick Leave Policy — SWS AI**

SWS AI provides the following sick leave entitlements:

- **Sick leave:** 12 working days per calendar year (fully paid)
- **Medical certificate:** Required for absences of 2 or more consecutive days
- **Hospitalisation leave:** Up to 60 days per year (inclusive of sick leave days) if hospitalisation is required
- **Notification:** Employees must inform their manager before 9:30 AM on the day of absence
- **Carry-forward:** Sick leave does not carry forward to the next year
- **Abuse of sick leave** may result in disciplinary action

For chronic conditions requiring extended leave, employees should contact HR to discuss options under the medical accommodation policy.`,
    sources: [{ document: "SWS AI Leave Policy", page: 2 }, { document: "SWS AI HR Policy", page: 4 }],
  },
  {
    keywords: ["notice period", "resignation", "resign", "quit", "leaving", "termination"],
    question: "What is the notice period for resignation?",
    answer: `**Resignation & Notice Period Policy — SWS AI**

**Notice Period Requirements:**

| Service Duration | Notice Period |
|---|---|
| Less than 1 year | 1 month |
| 1–3 years | 2 months |
| More than 3 years | 3 months |

**Process:**
1. Submit a formal resignation letter to your direct manager and HR
2. HR will acknowledge receipt within 2 working days
3. A handover plan must be agreed upon within the first week of notice
4. Exit interview is conducted by HR in the final week
5. Full and final settlement is processed within 30 days of last working day

**Buy-out option:** The company or employee may negotiate a notice buy-out at the last drawn basic salary rate.

**Garden leave** may be applied at the company's discretion during the notice period.`,
    sources: [{ document: "SWS AI Resignation Policy", page: 1 }, { document: "SWS AI HR Policy", page: 7 }],
  },
  {
    keywords: ["wfh", "work from home", "remote work", "remote", "hybrid", "work remotely"],
    question: "What are the WFH guidelines?",
    answer: `**Work From Home (WFH) Guidelines — SWS AI**

**Eligibility:**
- Employees who have completed their probation period (3 months) are eligible for WFH
- WFH is subject to role suitability and manager approval

**WFH Schedule:**
- **Standard hybrid model:** Up to 3 days WFH per week
- **Full remote:** Available for specific roles with prior HR and management approval
- WFH days must be agreed with the team at the start of each week

**Expectations while WFH:**
- Be online and reachable during core hours: **9:00 AM – 6:00 PM**
- Attend all scheduled meetings via video (camera on)
- Maintain a professional, distraction-free workspace
- Response time on Slack/Teams must not exceed 15 minutes during core hours

**Equipment:**
- Company laptop is provided; personal equipment use requires IT security approval
- VPN must be active at all times when accessing company systems remotely

**Not permitted on WFH days:**
- Travelling to another city/country without prior approval
- Attending personal appointments during core hours`,
    sources: [{ document: "SWS AI WFH Policy", page: 1 }, { document: "SWS AI HR Policy", page: 5 }],
  },
  {
    keywords: ["health insurance", "medical insurance", "insurance", "benefits", "health benefits", "coverage"],
    question: "What health insurance benefits do we have?",
    answer: `**Health Insurance & Benefits — SWS AI**

**Medical Insurance:**
- All full-time employees are covered under the **Group Health Insurance** plan from day one
- **Coverage:** Up to ₹5,00,000 per annum (individual) | ₹7,50,000 (family floater)
- **Dependants covered:** Spouse and up to 2 children
- **Cashless hospitalisation** at 500+ network hospitals
- **Pre and post hospitalisation** expenses covered (30 days pre / 60 days post)

**Additional Benefits:**
- **Dental & Vision:** Annual reimbursement of up to ₹10,000
- **Mental health:** 6 free counselling sessions per year via the Employee Assistance Programme (EAP)
- **Annual health check-up:** Fully covered once per year at empanelled diagnostic centres
- **Term life insurance:** 3× annual CTC covered for all employees
- **Accidental disability insurance:** Included in the group policy

**Claims Process:**
1. For cashless: Show your insurance card at the network hospital
2. For reimbursement: Submit bills via the HR portal within 30 days of discharge`,
    sources: [{ document: "SWS AI Benefits & Compensation", page: 1 }, { document: "SWS AI HR Policy", page: 9 }],
  },
  {
    keywords: ["performance review", "appraisal", "performance", "review cycle", "kpi", "goals"],
    question: "How does the performance review work?",
    answer: `**Performance Review Process — SWS AI**

**Review Cycles:**
- **Mid-year review:** July (feedback and goal realignment)
- **Annual review:** January (performance rating + compensation review)

**The 4-Step Process:**

1. **Self-assessment** — Employee completes a self-evaluation form covering goals, achievements, and areas for growth (2 weeks before review)
2. **Manager assessment** — Direct manager rates performance against agreed KPIs and competencies
3. **Calibration** — HR and senior leadership calibrate ratings across teams for fairness
4. **Review meeting** — 1:1 discussion between employee and manager to share feedback, agree on next-cycle goals, and discuss career development

**Rating Scale:**
| Rating | Description |
|---|---|
| 5 – Exceptional | Consistently exceeds all expectations |
| 4 – Exceeds | Frequently exceeds expectations |
| 3 – Meets | Consistently meets expectations |
| 2 – Developing | Partially meets expectations |
| 1 – Below | Does not meet expectations |

**Outcome:** Ratings directly influence annual increment percentages and promotion eligibility.`,
    sources: [{ document: "SWS AI Performance Review", page: 1 }, { document: "SWS AI HR Policy", page: 11 }],
  },
  {
    keywords: ["communication tools", "tools", "slack", "teams", "software", "collaboration", "communication"],
    question: "What tools does SWS AI use for communication?",
    answer: `**Communication & Collaboration Tools — SWS AI**

**Primary Communication:**
- **Slack** — Day-to-day messaging, team channels, and quick collaboration
- **Microsoft Teams** — Video meetings, town halls, and client calls
- **Email (Google Workspace)** — Formal communication and external correspondence

**Project & Task Management:**
- **Jira** — Sprint planning, bug tracking, and project management
- **Confluence** — Internal documentation and knowledge base
- **Notion** — Team wikis and async documentation

**Development & Engineering:**
- **GitHub** — Source code management and code reviews
- **Figma** — UI/UX design and prototyping
- **VS Code / JetBrains** — Approved IDEs

**File Storage & Sharing:**
- **Google Drive** — Document storage and collaboration
- **SharePoint** — Company-wide document repository

**Guidelines:**
- All work communication must happen on approved tools only
- Personal messaging apps (WhatsApp, Telegram) must not be used for work matters
- Confidential information must never be shared via personal accounts`,
    sources: [{ document: "SWS AI Onboarding Guide", page: 3 }, { document: "SWS AI IT Security Policy", page: 2 }],
  },
  {
    keywords: ["password", "password policy", "it security", "security policy", "credentials", "login", "mfa", "two factor"],
    question: "What is the IT password policy?",
    answer: `**IT Password & Security Policy — SWS AI**

**Password Requirements:**
- **Minimum length:** 12 characters
- Must include: uppercase letters, lowercase letters, numbers, and at least one special character (!@#$%^&*)
- Passwords must **not** contain your name, username, or common words
- **Password expiry:** Every 90 days
- **Password reuse:** Last 10 passwords cannot be reused

**Multi-Factor Authentication (MFA):**
- MFA is **mandatory** for all company systems, email, and VPN access
- Approved MFA apps: Google Authenticator, Microsoft Authenticator
- SMS-based OTP is permitted only as a backup method

**Security Rules:**
- Never share your password with anyone — including IT support
- Do not write passwords on paper or store them in plain text files
- Use the company-approved password manager (**1Password**) for storing credentials
- Report any suspected compromise immediately to **security@sws-ai.com**

**Device Security:**
- Screen lock must activate after **5 minutes** of inactivity
- Full-disk encryption is mandatory on all company devices
- Personal devices accessing company data must be enrolled in MDM`,
    sources: [{ document: "SWS AI IT Security Policy", page: 1 }, { document: "SWS AI IT Security Policy", page: 2 }],
  },
  {
    keywords: ["hr policies", "hr policy", "human resources", "company policy", "policies"],
    question: "What are the HR policies at SWS AI?",
    answer: `**HR Policies Overview — SWS AI**

SWS AI maintains a comprehensive set of HR policies to ensure a fair, safe, and productive workplace:

**Key Policy Areas:**

- **Recruitment & Onboarding** — Structured 30-day onboarding programme for all new hires
- **Leave Management** — Annual leave (20 days), sick leave (12 days), maternity/paternity leave, and special leave
- **Compensation** — Monthly salary disbursed on the last working day; annual reviews in January
- **Code of Conduct** — Zero tolerance for harassment, discrimination, or unethical behaviour
- **Grievance Redressal** — Formal grievance process with resolution within 15 working days
- **Anti-Harassment (POSH)** — Internal Complaints Committee (ICC) in place; all complaints treated confidentially
- **Data Privacy** — Employees must comply with the company's data protection policy at all times
- **Disciplinary Process** — Progressive discipline: verbal warning → written warning → final warning → termination

**Where to find policies:**
All HR policies are available on the company intranet under **HR > Policies & Procedures**.

For any HR queries, contact **hr@sws-ai.com** or raise a ticket on the HR portal.`,
    sources: [{ document: "SWS AI HR Policy", page: 1 }, { document: "SWS AI Company Overview", page: 2 }],
  },
  {
    keywords: ["code of conduct", "conduct", "procedures", "company procedures", "ethics", "behaviour"],
    question: "What are the company procedures and code of conduct?",
    answer: `**Code of Conduct & Company Procedures — SWS AI**

**Core Values:**
SWS AI expects all employees to uphold: **Integrity, Respect, Innovation, Accountability, and Collaboration**.

**Professional Conduct:**
- Treat all colleagues, clients, and partners with respect and professionalism
- Maintain confidentiality of company and client information at all times
- Avoid conflicts of interest; disclose any potential conflicts to HR immediately
- Do not engage in any activity that competes with SWS AI's business interests

**Workplace Behaviour:**
- Zero tolerance for harassment, bullying, or discrimination of any kind
- Alcohol and substance use on company premises is strictly prohibited
- Dress code: Smart casual in office; formal attire for client meetings

**Use of Company Resources:**
- Company equipment and software must be used for work purposes only
- Limited personal use of the internet is permitted but must not interfere with work
- Intellectual property created during employment belongs to SWS AI

**Reporting Violations:**
- Report concerns via the **anonymous ethics hotline** or directly to HR
- Whistleblower protection is guaranteed for good-faith reports
- Retaliation against anyone who raises a concern is a disciplinable offence`,
    sources: [{ document: "SWS AI Code of Conduct", page: 1 }, { document: "SWS AI HR Policy", page: 2 }],
  },
];

/**
 * Find the best matching answer from the local knowledge base.
 * Returns null if no match found (score below threshold).
 */
export function findLocalAnswer(question) {
  const q = question.toLowerCase();
  let best = null;
  let bestScore = 0;

  for (const entry of KB) {
    const score = entry.keywords.reduce(
      (acc, kw) => acc + (q.includes(kw) ? 1 : 0),
      0
    );
    if (score > bestScore) {
      bestScore = score;
      best = entry;
    }
  }

  // Return match if at least one keyword matched
  return bestScore > 0 ? best : null;
}

export default KB;
