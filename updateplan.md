# Jobscraper Automation: Enhancement Plan

This document outlines a strategic plan to elevate the job scraper from a functional script to a robust, user-friendly, and high-performance system. This plan leverages 5 specialized developer skills to address stability, speed, user-friendliness, and code maintainability.

## 1. Skill: `browser-automation` & `playwright-skill` (Stability & Bypassing)
**Goal:** Make the scraper invisible to anti-bot systems and handle dynamic DOMs gracefully.
* **Smart Waiting Strategies:** Replace static `asyncio.sleep()` calls with dynamic, state-based waits (e.g., waiting for specific network idle states or React hydration completions).
* **Stealth Enhancements:** Implement `playwright-stealth` advanced plugins to mask WebDriver signatures, spoof WebGL fingerprints, and randomize canvas hashes to prevent JobStreet from triggering captchas.
* **Resilient Locators:** Transition all brittle CSS selectors to semantic, role-based locators (e.g., `get_by_role("button", name="Apply")`) to survive JobStreet UI updates.

## 2. Skill: `python-performance-optimization` (Speed)
**Goal:** Drastically reduce the time it takes to apply to 100+ jobs.
* **Concurrent Scraping:** Currently, the script runs linearly. We will introduce `asyncio.gather()` to fetch job descriptions and evaluate `is_job_valid` for multiple job cards simultaneously *before* clicking into them.
* **Resource Management:** Optimize the Playwright context by blocking unnecessary network requests (images, fonts, analytics trackers, and heavy ad scripts) via `route.abort()`. This cuts bandwidth use and memory leaks, significantly speeding up page loads.

## 3. Skill: `error-handling-patterns` (Reliability)
**Goal:** Ensure the script never crashes silently and handles edge cases predictably.
* **Circuit Breaker Pattern:** If JobStreet goes down or blocks the IP, the script currently might loop or fail repeatedly. We will implement circuit breakers that pause the execution, notify the user, and wait before retrying. 
* **Granular Exception Classes:** Replace generic `Exception` catch-alls with specific exceptions like `JobStreetCaptchaError`, `FormStructureChangedError`, and `RateLimitError` to make debugging instantly clear in the logs.

## 4. Skill: `codebase-cleanup-tech-debt` (Maintainability)
**Goal:** Break down the monolithic 1000+ line `apply_jobs.py` into a clean architecture.
* **Modularization:** Split the code into specialized modules:
  * `auth_manager.py`: Handles session state and logins.
  * `job_scanner.py`: Handles searching, pagination, and keyword validation.
  * `form_solver.py`: Handles translating questions, database lookups, and DOM interactions.
* **Configuration Management:** Move all hardcoded variables (like `PLAYWRIGHT_PROFILE` and timeout durations) into a `.env` file or a typed YAML config file using Pydantic for schema validation.

## 5. Skill: `ui-ux-pro-max` (Ease of Use)
**Goal:** Abstract the terminal away and give the user a simple, modern interface.
* **Dashboard Wrapper (Streamlit or FastAPI+React):** Instead of running CLI commands containing arguments, build a lightweight local web interface. 
* **Features:**
  * Visual toggles for "Recommendation Mode" vs "Search Mode".
  * Live-updating table of "Jobs Applied Today" and "Jobs Skipped" with reasons.
  * A settings page to easily edit the `exclude_list` and update the `company_questions.json` database without touching code.
  * One-click "Start Run", "Pause", and "Stop" controls.
