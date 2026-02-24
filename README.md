# JobStreet Auto-Applier

An automated, hands-free job application bot for JobStreet Indonesia built with Python and Playwright. It intelligently scans for jobs matching your criteria, filters out unwanted keywords, navigates application forms, and securely saves your answers to automatically fill out future questionnaires.

## 🚀 Quick Start (For Non-Coders!)

We've made it incredibly simple to run the automation without touching any code.

### 1. Requirements
Ensure you have Python installed on your Windows machine. If you don't, download it from [python.org](https://www.python.org/downloads/).

### 2. Run the App
1. Open the folder containing this project: `jobscraper-api`
2. **Double-click** the file named `Run_Auto_Applier.bat`.
3. A command prompt window will open with a green tint.

### 3. Answer the Prompts
The script will ask you a few quick questions:
- **Job keyword:** What job do you want? (e.g., `Manager`, `Designer`). Leave empty for anything.
- **Location:** Where do you want to work? (e.g., `Jakarta`, `Bali`, `Indonesia`).
- **Extra exclude keywords:** Any words you *don't* want in the job title? (e.g., `intern, freelance`). Separate by commas.
- **Max applications:** How many jobs to apply to? Type `ALL` to apply to every visible job, or type a number like `10`.
- **Dry run:** Type `N` to actually submit applications. (If you type `Y`, it just pretends to apply for testing).

### 4. The First Run (Login)
The very first time you run this, a Chrome browser will pop up and ask you to log into JobStreet (using Google, Apple, or Email). **Log in manually once.** The script will detect when you've successfully logged in, save your session forever, and automatically begin applying to jobs! You won't have to log in manually again.

---

## 🏗️ Architecture & How It Works

This bot doesn't just blindly click buttons. It behaves like a human and learns from the questions it encounters.

### Directory Structure

```text
jobscraper-api/
├── automaton/
│   ├── apply_jobs.py             # Main Python automation logic
│   ├── company_questions.json    # The Intelligence Bank (Question/Answer pairings)
│   └── applied_job.md            # History log of every job applied to
├── playwright-profile/           # Automatically generated folder that saves your browser cookies
└── Run_Auto_Applier.bat          # The 1-click execution file
```

### The "Brain" (`company_questions.json`)
When the bot clicks "Apply" on a job, it often encounters Custom Questions (e.g., "How many years of management experience do you have?"). 

- If it **doesn't** know the answer, the script will pause, ask you to type the answer in the black console window, and then it will save that exact answer into `company_questions.json`.
- Next time it sees that *exact* question on a different job, it will **instantly and automatically** fill it out without bothering you!

### Dynamic Waiting (Performance Overhaul)
Instead of waiting arbitrary amounts of time (like 5 seconds per page), the bot uses "Dynamic Waiting". It simultaneously looks for Questions, Next buttons, and Submit buttons the millisecond a page loads. This means moving through multi-page application wizards is blisteringly fast—happening in milliseconds instead of seconds.

### Resilient Clicking (`safe_click`)
Modern websites constantly refresh elements, which often breaks scrapers with "Element is detached from DOM" errors. This project implements a custom `safe_click` function that gracefully catches detached elements and retries clicking seamlessly.

---

## 🛠️ Configuration (For Advanced Users)

If you wish to edit the core filtering logic, open `automaton/apply_jobs.py` in your favorite code editor (like VSCode).

### Built-in Exclusions
At the top of the script, there is a `KEYWORDS_TO_EXCLUDE` list:
```python
KEYWORDS_TO_EXCLUDE = [
    "mandarin", "chinese", "japanese", "german", "religous", "agama",
    "kristen", "christian", "principal", "kepala sekolah", "seni", r"\bart\b"
]
```
The bot will automatically skip any job whose title or description contains these whole words, regardless of what you type in the start-up prompt. Add or remove words here to permanently change the bot's standard filtering.

---

## 🛡️ Best Practices & Safety

- **Headless Mode is Off by Default:** You can literally watch the bot apply to jobs in real-time. This is intentional to avoid bot-detection and ensure you can intervene if JobStreet throws an unexpected CAPTCHA.
- **Dry Runs:** Always do a "Dry Run" (`Y` when prompted) when you change your search keywords! It lets you watch what the bot *would* have applied to, so you don't accidentally send your CV to 50 wrong jobs.
- **Do not share your `playwright-profile` folder:** That folder contains your live JobStreet login cookies. If sent to someone else, they will be logged into your account!
