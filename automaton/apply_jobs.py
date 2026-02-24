"""
JobStreet Interactive Auto-Applier
===================================
Skills applied:
1. python-pro       - async/await, type hints, modern Python patterns
2. browser-automation - Playwright launch_persistent_context with real Chrome profile
3. error-handling-patterns - graceful degradation per job, resilient loop
4. clean-code       - single-responsibility functions, clear naming
5. python-patterns  - async I/O separation, asyncio.to_thread for blocking prompts

How to use:
  1. Close Chrome (the script will open it for you)
  2. Run: python automaton/apply_jobs.py
  Your existing login session is loaded automatically from your Chrome profile.
"""
import asyncio
import re
import os
from typing import Set, Dict, Optional, List
from playwright.async_api import async_playwright, BrowserContext, Page
from rich.console import Console
from rich.prompt import Prompt

console = Console()

import json

QUESTIONS_FILE = "automaton/company_questions.json"
APPLIED_JOBS_FILE = "automaton/applied_job.md"

# Dedicated profile dir for this automation — session is saved after first login
PLAYWRIGHT_PROFILE = os.path.join(os.path.dirname(__file__), "playwright-profile")

# Whole-word exclusion keywords — avoids false matches like 'art' in 'Elementary'
KEYWORDS_TO_EXCLUDE = [
    "mandarin", "chinese", "japanese", "german", "religous", "agama",
    "kristen", "christian", "principal", "kepala sekolah", "seni", r"\bart\b"
]

# ---------------------------------------------------------------------------
# I/O Helpers
# ---------------------------------------------------------------------------


def load_applied_jobs() -> Set[str]:
    applied_urls: Set[str] = set()
    if not os.path.exists(APPLIED_JOBS_FILE):
        return applied_urls
    with open(APPLIED_JOBS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for match in re.finditer(r"\[.*?\]\((.*?)\)", content):
        applied_urls.add(match.group(1).split("?")[0])
    return applied_urls


def log_applied_job(title: str, url: str, salary: str, location: str, is_dry_run: bool) -> None:
    try:
        is_new = not os.path.exists(APPLIED_JOBS_FILE)
        with open(APPLIED_JOBS_FILE, "a", encoding="utf-8") as f:
            if is_new:
                f.write("# Applied Jobs History\n\n| Job Title | Location | Salary | Link |\n|---|---|---|---|\n")
            tag = " (DRY RUN)" if is_dry_run else ""
            clean_url = url.split("?")[0]
            f.write(f"| {title}{tag} | {location} | {salary} | [Link]({clean_url}) |\n")
    except Exception as e:
        console.print(f"[red]Failed to log: {e}[/red]")


def load_answers() -> Dict[str, str]:
    if not os.path.exists(QUESTIONS_FILE):
        return {}
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # For apply logic, we only strictly need the 'answer' string mapped by question text
        return {q: d["answer"] for q, d in data.items() if "answer" in d and d["answer"]}
    except Exception as e:
        console.print(f"[red]Failed to load JSON answers: {e}[/red]")
        return {}


def append_question(q_text: str, q_type: str, answer: str = "", options: Optional[List[str]] = None) -> None:
    data = {}
    if os.path.exists(QUESTIONS_FILE):
        try:
            with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    data[q_text] = {
        "type": q_type,
        "options": options or [],
        "answer": answer
    }
    
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def is_job_valid(title: str, description: str, exclude_list: List[str]) -> bool:
    """Whole-word keyword check. Regex patterns like r'\\bart\\b' are supported."""
    text = f"{title} {description}".lower()
    for kw in exclude_list:
        kw = kw.strip()
        if not kw:
            continue
        # If keyword starts with \b it's a regex pattern, otherwise literal whole-word
        pattern = kw if kw.startswith(r"\b") else rf"\b{re.escape(kw)}\b"
        if re.search(pattern, text):
            return False
    return True

# ---------------------------------------------------------------------------
# Browser / DOM Helpers
# ---------------------------------------------------------------------------

async def safe_click(locator, retries=3, timeout=3000):
    """Reliable clicking with retries to handle flaky DOM rendering."""
    for i in range(retries):
        try:
            await locator.click(timeout=timeout)
            return True
        except Exception as e:
            if i == retries - 1:
                console.print(f"      [red]Click failed after {retries} retries: {e}[/red]")
                raise e
            await asyncio.sleep(1)


async def get_question_groups(page: Page) -> list:
    """
    Find all question groups on the current form page using confirmed JobStreet selectors.
    Each group is a div containing a label[for^='question-ID_Q'] and its associated input.
    """
    # The apply page URL confirms we're on the questionnaire step
    groups = []
    # 1. Locate all standard question labels by their for attribute pattern (handles both ID_Q and AU_Q)
    label_handles = await page.query_selector_all("label[for^='question-']")
    for label in label_handles:
        try:
            q_text_el = await label.query_selector("strong")
            q_text = (await q_text_el.inner_text()).strip() if q_text_el else (await label.inner_text()).strip()
            q_text = re.sub(r"\*", "", q_text).strip()
            if not q_text or len(q_text) < 4:
                continue

            label_for = await label.get_attribute("for") or ""
            is_required = "*" in (await label.inner_text())

            # Find the associated input (select or input)
            try:
                # Give React a moment to mount the input after the label appears
                target_el = await page.wait_for_selector(f"#{label_for}", state="attached", timeout=2000)
            except Exception:
                target_el = await page.query_selector(f"#{label_for}")
            
            q_type, options = "Text", []

            if target_el:
                tag = await target_el.evaluate("e => e.tagName.toLowerCase()")
                if tag == "select":
                    q_type = "Dropdown"
                    try:
                        # Wait a moment for React to populate the dropdown options
                        await target_el.wait_for_selector("option", state="attached", timeout=2000)
                    except Exception:
                        pass
                    for opt in await target_el.query_selector_all("option"):
                        val = (await opt.inner_text()).strip()
                        opt_val = await opt.get_attribute("value") or ""
                        if val and "pilih" not in val.lower() and opt_val:
                            options.append(val)
                elif tag == "input":
                    inp_type = await target_el.get_attribute("type") or "text"
                    q_type = "Choice" if inp_type in ("checkbox", "radio") else "Text"

            # Always add the question even if options couldn't be parsed immediately
            groups.append({
                "text": q_text,
                "type": q_type,
                "options": options,
                "label_for": label_for,
                "is_required": is_required,
                "page": page,
            })
        except Exception:
            continue

    # 2. Locate React-style radio groups (fieldset)
    fieldsets = await page.query_selector_all("fieldset[role='radiogroup']")
    for fs in fieldsets:
        try:
            legend = await fs.query_selector("legend")
            if not legend: continue
            q_text = (await legend.inner_text()).strip()
            q_text = re.sub(r"\*", "", q_text).strip()
            if not q_text or len(q_text) < 4: continue
            
            # The fieldset itself contains the actual ID, e.g. question-AU_Q_402_V_2
            fs_id = await fs.get_attribute("id") or ""
            is_required = "*" in (await legend.inner_text())
            
            radios = await fs.query_selector_all("input[type='radio']")
            options = []
            for r in radios:
                r_id = await r.get_attribute("id") or ""
                r_label = await fs.query_selector(f"label[for='{r_id}']")
                if r_label:
                    options.append((await r_label.inner_text()).strip())
            
            groups.append({
                "text": q_text,
                "type": "Choice",
                "options": options,
                "label_for": fs_id,
                "is_required": is_required,
                "page": page,
            })
        except Exception:
            continue

    # 3. Also find checkbox groups (id^='ID_Q_' or 'AU_Q_' without 'question-' prefix)
    # These are multi-choice skills/tags grouped under a common heading
    checkbox_inputs = await page.query_selector_all("input[type='checkbox'][id^='ID_Q_'], input[type='checkbox'][id^='AU_Q_']")
    seen_prefixes: set = set()
    for inp in checkbox_inputs:
        inp_id = await inp.get_attribute("id") or ""
        # Group prefix = everything up to last _A_
        prefix = re.sub(r"_A_\d+$", "", inp_id)
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        # Find heading label for this group (look for preceding strong/span)
        heading = await page.query_selector(f"label[for^='{prefix}']")
        heading_text = (await heading.inner_text()).strip() if heading else prefix
        # Collect all options in this group
        group_inputs = await page.query_selector_all(f"input[id^='{prefix}_A_']")
        opts = []
        for gi in group_inputs:
            gi_id = await gi.get_attribute("id") or ""
            lbl = await page.query_selector(f"label[for='{gi_id}']")
            if lbl:
                opts.append((await lbl.inner_text()).strip())
        if opts:
            groups.append({
                "text": heading_text,
                "type": "MultiChoice",
                "options": opts,
                "label_for": prefix,
                "is_required": False,
                "page": page,
            })
    return groups


async def fill_question_group(q_data: Dict, answer: str) -> bool:
    """
    Fill a single question group given the answer string.
    Uses confirmed JobStreet DOM patterns.
    """
    page: Page = q_data["page"]
    label_for = q_data["label_for"]
    q_type = q_data["type"]
    label = q_data["text"]
    try:
        if q_type == "Dropdown":
            select = await page.query_selector(f"#{label_for}")
            if select:
                # Try matching by visible text
                options = await select.query_selector_all("option")
                for opt in options:
                    t = await opt.inner_text()
                    if answer.lower() in t.lower() or t.lower() in answer.lower():
                        try:
                            val = await opt.get_attribute("value")
                            await select.select_option(value=val, timeout=3000, force=True)
                            await select.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
                            console.print(f"      [green]✓ '{label}' → '{t.strip()}'[/green]")
                            return True
                        except Exception as e:
                            console.print(f"      [red]Fill error '{label}': {e}[/red]")
                            continue
                # Fallback: select by index from answer (e.g. "2")
                try:
                    idx = int(answer) - 1
                    opt_els = [o for o in options if await o.get_attribute("value")]
                    if 0 <= idx < len(opt_els):
                        try:
                            val = await opt_els[idx].get_attribute("value")
                            await select.select_option(value=val, timeout=3000, force=True)
                            await select.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
                            console.print(f"      [green]✓ '{label}' by index[/green]")
                            return True
                        except Exception as e:
                            console.print(f"      [red]Fill error '{label}' by index: {e}[/red]")
                except ValueError:
                    pass

        elif q_type in ("Choice", "MultiChoice"):
            # Find checkbox/radio by matching label text
            fieldset = await page.query_selector(f"fieldset#{label_for}")
            if fieldset:
                group_inputs = await fieldset.query_selector_all("input[type='radio'], input[type='checkbox']")
            else:
                prefix = label_for if "_A_" not in label_for else re.sub(r"_A_\d+$", "", label_for)
                group_inputs = await page.query_selector_all(f"input[id^='{prefix}_A_'], input[id='{label_for}']")
            
            answer_parts = [a.strip().lower() for a in answer.split('|')] if q_type == "MultiChoice" else [answer.lower()]
            
            clicked_any = False
            for gi in group_inputs:
                gi_id = await gi.get_attribute("id") or ""
                lbl_el = await page.query_selector(f"label[for='{gi_id}']")
                if lbl_el:
                    lbl_text = (await lbl_el.inner_text()).strip()
                    for part in answer_parts:
                        if part and (part in lbl_text.lower() or lbl_text.lower() in part):
                            is_checked = await gi.is_checked()
                            if not is_checked:
                                await lbl_el.click()
                            console.print(f"      [green]✓ '{label}' → '{lbl_text}'[/green]")
                            clicked_any = True
                            if q_type == "Choice":
                                return True
                            break
            if clicked_any:
                return True

        else:  # Text
            inp = await page.query_selector(f"#{label_for}")
            if inp:
                await inp.fill(answer)
                console.print(f"      [green]✓ '{label}' → '{answer[:40]}'[/green]")
                return True

    except Exception as e:
        console.print(f"      [red]Fill error '{label}': {e}[/red]")
    return False


async def prompt_for_answer(q_data: Dict, auto_mode: str) -> str:
    """
    python-patterns: use asyncio.to_thread so blocking Prompt.ask
    never stalls the Playwright event loop.
    """
    console.print(f"\n[bold magenta]⚠  New Question![/bold magenta]  {q_data['text']}")
    console.print(f"[dim]Type: {q_data['type']}[/dim]")

    options = q_data.get("options", [])

    q_text_lower = q_data['text'].lower()
    is_years_exp = "how many years" in q_text_lower or "berapa tahun pengalaman" in q_text_lower

    if is_years_exp and q_data["type"] in ("Dropdown", "Choice") and options:
        import msvcrt
        import random

        if auto_mode == "Semi":
            console.print("  [cyan]Semi-Auto Mode: Waiting 2s (Press any key to cancel/answer manually)...[/cyan]")
            for _ in range(20):
                if msvcrt.kbhit():
                    break
                await asyncio.sleep(0.1)
            else:
                return _auto_select_exp(options)
        else:
            console.print("  [cyan]Fully Auto Mode: Instantly resolving experience question...[/cyan]")
            return _auto_select_exp(options)

    if q_data["type"] in ("Dropdown", "Choice", "MultiChoice") and options:
        for i, opt in enumerate(options, 1):
            console.print(f"  {i}. {opt}")
            
        prompt_txt = "Select number(s) comma-separated or type exact text" if q_data["type"] == "MultiChoice" else "Select number or type exact text"
        raw = await asyncio.to_thread(Prompt.ask, prompt_txt, default="1")
        
        if q_data["type"] == "MultiChoice":
            parts = [p.strip() for p in raw.split(",")]
            ans_list = []
            for p in parts:
                try:
                    idx = int(p) - 1
                    ans_list.append(options[idx] if 0 <= idx < len(options) else p)
                except ValueError:
                    ans_list.append(p)
            return " | ".join(ans_list)
        else:
            try:
                idx = int(raw) - 1
                return options[idx] if 0 <= idx < len(options) else raw
            except ValueError:
                return raw
    else:
        return await asyncio.to_thread(Prompt.ask, "Your answer")


def _auto_select_exp(options: List[str]) -> str:
    import random
    is_less = random.random() < 0.6
    ans_str = ""
    for opt in options:
        opt_lower = opt.lower()
        if is_less:
            if "less" in opt_lower or "kurang" in opt_lower:
                ans_str = opt
                break
        else:
            if ("1 year" in opt_lower or "1 tahun" in opt_lower) and "less" not in opt_lower and "kurang" not in opt_lower:
                ans_str = opt
                break
    
    if not ans_str:
        ans_str = options[1] if len(options) > 1 else options[0]

    console.print(f"  [bold cyan]Auto-selected: {ans_str}[/bold cyan]")
    return ans_str


async def fill_answer(q_data: Dict, answer: str) -> bool:
    """
    error-handling-patterns: return False on failure so caller can decide
    whether to skip the job rather than crashing.
    """
    try:
        wrapper = q_data["wrapper"]
        q_type = q_data["type"]
        label = q_data["text"]

        if q_type == "Dropdown":
            select = await wrapper.query_selector("select")
            if select:
                for opt in await select.query_selector_all("option"):
                    t = await opt.inner_text()
                    if answer.lower() in t.lower():
                        await select.select_option(value=await opt.get_attribute("value"))
                        console.print(f"      [green]✓ '{label}' → '{t.strip()}'[/green]")
                        return True

        elif q_type == "Choice":
            for lbl in await wrapper.query_selector_all("label"):
                t = await lbl.inner_text()
                if answer.lower() in t.lower():
                    await lbl.click()
                    console.print(f"      [green]✓ '{label}' → '{t.strip()}'[/green]")
                    return True
            # value fallback
            for inp in await wrapper.query_selector_all("input[type='radio'], input[type='checkbox']"):
                val = await inp.get_attribute("value") or ""
                if answer.lower() in val.lower():
                    await inp.click(force=True)
                    console.print(f"      [green]✓ '{label}' → '{val}'[/green]")
                    return True

        else:  # Text / textarea
            for sel in ["input[type='text']", "textarea", "input:not([type='radio']):not([type='checkbox'])"]:
                inputs = await wrapper.query_selector_all(sel)
                if inputs:
                    await inputs[0].fill(answer)
                    console.print(f"      [green]✓ '{label}' → '{answer[:40]}'[/green]")
                    return True

    except Exception as e:
        console.print(f"      [red]Fill error for '{q_data['text']}': {e}[/red]")
    return False

# ---------------------------------------------------------------------------
# Form Wizard Navigator
# ---------------------------------------------------------------------------

async def navigate_form(page: Page, answers_db: Dict[str, str], title: str, dry_run: bool, auto_mode: str, job_log: Dict) -> bool:
    """
    Walk through a multi-step application form using confirmed JobStreet selectors.
    Auto-fills known answers, prompts for unknowns, handles Lanjut/Kirim buttons.
    """
    # Wait to land on the apply page
    try:
        await page.wait_for_url("**/apply**", timeout=15000)
    except Exception:
        pass

    last_url = ""
    stuck_count = 0

    for step in range(15):
        try:
            # Wait for either questions, headers, or the Next/Submit buttons to spawn
            await page.wait_for_selector(
                "label[for^='question-'], fieldset[role='radiogroup'], h2, button:has-text('Lanjut'), button:has-text('Next'), button:has-text('Kirim'), button:has-text('Submit')", 
                timeout=3000
            )
        except Exception:
            pass
        await page.wait_for_load_state("domcontentloaded")
        current_url = page.url
        
        # Anti-loop guard: if we're stuck on the same URL for 3 iterations, abort
        if current_url == last_url:
            stuck_count += 1
            if stuck_count == 1:
                await page.screenshot(path="debug_loop.png")
                html = await page.evaluate("() => document.documentElement.outerHTML")
                with open("debug_loop.html", "w", encoding="utf-8") as f:
                    f.write(html)
            if stuck_count >= 3:
                console.print(f"  [red]Stuck in infinite loop on {current_url} — aborting application.[/red]")
                return False
        else:
            last_url = current_url
            stuck_count = 0

        # If we got redirected to login or Google OAuth, pause and wait for user to sign in
        if "login" in current_url or "masuk" in current_url or "accounts.google" in current_url or "seek.com/login" in current_url:
            console.print("  [bold yellow]⚠ Login required — please sign in to JobStreet in the browser![/bold yellow]")
            console.print("  [dim]The script will continue automatically once you're logged in...[/dim]")
            try:
                await page.wait_for_url(
                    lambda url: "jobstreet.com" in url
                        and "login" not in url
                        and "masuk" not in url
                        and "accounts.google" not in url
                        and "seek.com/login" not in url,
                    timeout=0  # Wait indefinitely
                )
                await page.wait_for_timeout(2000)
                console.print("  [green]✓ Logged in! Continuing...[/green]")
                continue  # Re-enter loop from current URL
            except Exception as e:
                console.print(f"  [red]Login wait failed: {e}[/red]")
                return False

        # Detect final review/confirmation step
        if "/review" in current_url or "/confirm" in current_url:
            submit = page.get_by_role("button", name=re.compile(r"(Kirim|Submit)", re.IGNORECASE))
            if await submit.count():
                if dry_run:
                    console.print(f"  [bold yellow][DRY RUN][/bold yellow] Would click Kirim for '{title}'")
                else:
                    await safe_click(submit.first)
                    try:
                        await page.wait_for_selector("text='Application sent', text='Lamaran terkirim', h1", timeout=5000)
                    except Exception:
                        await page.wait_for_load_state("domcontentloaded")
                console.print(f"  [bold green]✓ Applied '{title}'[/bold green]")
                return True

        groups = await get_question_groups(page)
        console.print(f"    [dim]Step {step + 1} ({current_url.split('/')[-1]}): {len(groups)} questions[/dim]")

        had_missing = False
        for q_data in groups:
            q_text = q_data["text"]
            
            # 1. Exact match
            matched_answer = answers_db.get(q_text)
            

            if matched_answer:
                success = await fill_question_group(q_data, matched_answer)
                if not success:
                    console.print(f"      [yellow]⚠ Saved answer '{matched_answer}' failed to apply. Prompting...[/yellow]")
                    ans = await prompt_for_answer(q_data, auto_mode)
                    answers_db[q_text] = ans
                    append_question(q_text, q_data["type"], ans, q_data["options"] or None)
                    console.print(f"      [bold green]Saved to bank![/bold green]")
                    ok = await fill_question_group(q_data, ans)
                    if ok:
                        job_log["questions"].append({"question": q_text, "answer": ans})
                    elif q_data["is_required"]:
                        had_missing = True
                else:
                    job_log["questions"].append({"question": q_text, "answer": matched_answer})
            else:
                ans = await prompt_for_answer(q_data, auto_mode)
                answers_db[q_text] = ans
                append_question(q_text, q_data["type"], ans, q_data["options"] or None)
                console.print(f"      [bold green]Saved to bank![/bold green]")
                ok = await fill_question_group(q_data, ans)
                if ok:
                    job_log["questions"].append({"question": q_text, "answer": ans})
                elif q_data["is_required"]:
                    had_missing = True

        if had_missing:
            console.print("    [red]Required field unanswered — skipping.[/red]")
            return False

        submit = page.get_by_role("button", name=re.compile(r"^(Kirim lamaran|Kirim|Submit application)$", re.IGNORECASE)).first
        nxt = page.get_by_role("button", name=re.compile(r"^(Lanjut|Lanjutkan|Next)$", re.IGNORECASE)).first

        try:
            # Wait concurrently for either button to render (fixes React race condition without sequential penalties)
            await submit.or_(nxt).wait_for(state="attached", timeout=3000)
        except Exception:
            pass

        # Check Submit
        is_submit = await submit.is_visible()
        if is_submit:
            if dry_run:
                console.print(f"  [bold yellow][DRY RUN][/bold yellow] '{title}'")
            else:
                await safe_click(submit)
                try:
                    await page.wait_for_selector("text='Application sent', text='Lamaran terkirim', html", state="attached", timeout=5000)
                except Exception:
                    pass
            console.print(f"  [bold green]✓ Applied '{title}'[/bold green]")
            return True

        # Check Next
        is_nxt = await nxt.is_visible()
        if is_nxt:
            # Check if it's disabled due to missing mandatory fields
            is_disabled = await nxt.is_disabled()
            if is_disabled:
                console.print("    [red]Lanjut button is disabled — a required field was missed![/red]")
                return False
            
            await safe_click(nxt)
            # Wait for URL to change or new questions to appear
            await page.wait_for_load_state("domcontentloaded")
            continue

        console.print(f"    [yellow]No Lanjut/Kirim on {current_url.split('/')[-1]} — done.[/yellow]")
        return False

    return False

# ---------------------------------------------------------------------------
# Main Application Loop
# ---------------------------------------------------------------------------

async def run(keyword: str, location: str, exclude_list: List[str], max_apps: int, dry_run: bool, auto_mode: str) -> None:
    """
    Main application loop to search for jobs and apply.
    Uses Playwright's persistent context to reuse an existing Chrome profile
    for logged-in sessions.
    """
    answers_db = load_answers()
    applied_history = load_applied_jobs()
    console.print(f"[green]Questions bank: {len(answers_db)} | History: {len(applied_history)}[/green]")

    import datetime
    run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_log = {
        "timestamp": run_timestamp,
        "settings": {
            "keyword": keyword,
            "location": location,
            "exclude_list": exclude_list,
            "max_apps": max_apps,
            "dry_run": dry_run,
            "auto_mode": auto_mode
        },
        "applied_jobs": []
    }

    async with async_playwright() as pw:
        # browser-automation skill: dedicated Playwright profile
        # - No conflict with real Chrome (separate profile dir)
        # - Session is SAVED after first login: no re-login needed on next run
        # - First run only: browser opens, user logs in manually, presses Enter
        import subprocess
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
        await asyncio.sleep(1)

        console.print("[dim]Launching browser...[/dim]")
        context: BrowserContext = await pw.chromium.launch_persistent_context(
            user_data_dir=PLAYWRIGHT_PROFILE,
            headless=False,
            slow_mo=30,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )

        # Reliable login check: look for a user-specific nav element in the DOM
        # The profile/avatar link only renders when a session exists
        check_page: Page = await context.new_page()
        console.print("[dim]Checking login status...[/dim]")
        await check_page.goto("https://id.jobstreet.com", wait_until="domcontentloaded", timeout=20000)
        await check_page.wait_for_timeout(2000)

        # Check for login button (shown when logged out) vs profile icon (shown when logged in)
        login_btn_visible = await check_page.locator("a[href*='/id/login'], a:has-text('Masuk')").count()
        is_logged_out = login_btn_visible > 0 or "login" in check_page.url or "accounts.google" in check_page.url

        if is_logged_out:
            console.print("\n[bold yellow]═══ LOGIN REQUIRED ═══[/bold yellow]")
            console.print("Please log in to JobStreet in the browser window (use Google, etc.)")
            console.print("[dim]The script will continue automatically once you're logged in.[/dim]")
            # Wait until user is on a jobstreet page that isn't login
            await check_page.wait_for_url(
                lambda url: "jobstreet.com" in url
                    and "login" not in url
                    and "masuk" not in url
                    and "accounts.google" not in url
                    and "seek.com/login" not in url,
                timeout=0
            )
            await check_page.wait_for_timeout(2000)
            console.print("[bold green]✓ Logged in! Starting automation...[/bold green]")
        else:
            console.print("[green]✓ Already logged in.[/green]")

        await check_page.close()

        safe_kw = keyword.replace(" ", "-").lower()
        safe_loc = location.replace(" ", "-").lower()
        
        import urllib.parse
        encoded_loc = urllib.parse.quote(location)
        search_url = f"https://id.jobstreet.com/id/job-search/{safe_kw}-jobs/in-{safe_loc}/?where={encoded_loc}"

        main_page: Page = await context.new_page()
        console.print(f"[cyan]Navigating to {search_url}[/cyan]")
        await main_page.goto(search_url, wait_until="domcontentloaded")
        try:
            await main_page.wait_for_selector('article[data-automation="normalJob"], a[data-automation^="recommendedJobLink_"]', timeout=10000)
        except Exception:
            pass

        console.print("[bold]Scanning for jobs...[/bold]\n")
        apps_done = 0

        while apps_done < max_apps:
            # Collect all job links on this page
            all_elements = (
                await main_page.locator('article[data-automation="normalJob"]').element_handles()
                + await main_page.locator('a[data-automation^="recommendedJobLink_"]').element_handles()
            )

            unique: Dict[str, Dict] = {}
            for el in all_elements:
                try:
                    tag = await el.evaluate("e => e.tagName.toLowerCase()")
                    if tag == "article":
                        link = await el.query_selector('a[data-automation="jobTitle"]') or await el.query_selector('a[href*="/job/"]')
                        if not link:
                            continue
                    else:
                        link = el
                    href = await link.get_attribute("href") or ""
                    title = (await link.inner_text()).strip()
                    if href and len(title) > 3:
                        job_id = href.split("?")[0]
                        if job_id not in unique:
                            unique[job_id] = {"title": title, "href": href}
                except Exception:
                    continue

            console.print(f"[dim]  {len(unique)} jobs visible[/dim]")
            if not unique:
                console.print("[yellow]No jobs found on this page.[/yellow]")
                break

            for job_id, data in unique.items():
                if apps_done >= max_apps:
                    break

                title = data["title"]
                href = data["href"]
                job_url = href if href.startswith("http") else f"https://id.jobstreet.com{href}"
                clean_url = job_url.split("?")[0]

                if clean_url in applied_history:
                    continue
                if not is_job_valid(title, "", exclude_list):
                    console.print(f"[yellow]  Skip (title filter): {title}[/yellow]")
                    continue

                console.print(f"\n[cyan]→ {title}[/cyan]")

                job_page: Page = await context.new_page()
                try:
                    await job_page.goto(job_url, timeout=45000, wait_until="domcontentloaded")
                    try:
                        await job_page.wait_for_selector('a[data-automation="job-detail-apply"], div[data-automation="jobAdDetails"]', timeout=8000)
                    except Exception:
                        pass
                except Exception as e:
                    console.print(f"  [red]Load failed: {e}[/red]")
                    await job_page.close()
                    continue

                # Scrape metadata for logging and location filtering
                loc_text, sal_text = "Unknown", "Hidden"
                try:
                    loc_el = job_page.locator("[data-automation='job-detail-location']")
                    if await loc_el.count():
                        loc_text = await loc_el.first.inner_text()
                    sal_el = job_page.locator("[data-automation='job-detail-salary']")
                    if await sal_el.count():
                        sal_text = await sal_el.first.inner_text()
                except Exception:
                    pass

                # Enforce strict location check (JobStreet sometimes injects recommended jobs outside the search area)
                if location and location.lower() not in loc_text.lower() and loc_text != "Unknown":
                    console.print(f"  [yellow]Skip (location filter): {loc_text}[/yellow]")
                    await job_page.close()
                    continue

                # Check description keywords
                try:
                    desc_el = job_page.locator("div[data-automation='jobAdDetails']")
                    if await desc_el.count():
                        desc = await desc_el.first.inner_text()
                        if not is_job_valid(title, desc, exclude_list):
                            console.print("  [yellow]Skip (desc filter)[/yellow]")
                            await job_page.close()
                            continue
                except Exception:
                    pass

                # Find Apply button
                try:
                    pages_before = len(context.pages)
                    apply_btn = job_page.locator('a[data-automation="job-detail-apply"]')

                    # Skip external applications
                    if await job_page.locator('a[data-automation="job-detail-apply-external"]').count():
                        console.print("  [dim]Skip (external)[/dim]")
                        await job_page.close()
                        continue

                    if not await apply_btn.count():
                        # Fallback - look for a Quick Apply button that isn't external
                        apply_btn = job_page.locator("button:has-text('Lamaran Cepat'), button:has-text('Apply')")

                    if not await apply_btn.count():
                        console.print("  [dim]Skip (no apply button)[/dim]")
                        await job_page.close()
                        continue

                    btn_text = await apply_btn.first.inner_text()
                    if "situs" in btn_text.lower() or "site" in btn_text.lower():
                        console.print("  [dim]Skip (external site)[/dim]")
                        await job_page.close()
                        continue

                    console.print("  [magenta]Applying...[/magenta]")
                    await safe_click(apply_btn.first)
                    try:
                        await job_page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass

                    # Handle application in new tab vs same page
                    apply_page = context.pages[-1] if len(context.pages) > pages_before else job_page
                    new_tab = apply_page != job_page
                    if new_tab:
                        await apply_page.bring_to_front()

                    job_log = {
                        "title": title,
                        "url": clean_url,
                        "location": loc_text,
                        "salary": sal_text,
                        "questions": []
                    }
                    success = await navigate_form(apply_page, answers_db, title, dry_run, auto_mode, job_log)

                    if success:
                        apps_done += 1
                        run_log["applied_jobs"].append(job_log)
                        applied_history.add(clean_url)
                        log_applied_job(title, clean_url, sal_text, loc_text, dry_run)
                        if max_apps >= 999999:
                            console.print(f"  [cyan]Logged ({apps_done})[/cyan]")
                        else:
                            console.print(f"  [cyan]Logged ({apps_done}/{max_apps})[/cyan]")

                    if new_tab:
                        await apply_page.close()
                    await job_page.close()

                except Exception as e:
                    console.print(f"  [red]Apply error: {e}[/red]")
                    try:
                        await job_page.close()
                    except Exception:
                        pass

            # Paginate
            next_btn = main_page.get_by_role("link", name=re.compile(r"(Selanjutnya|Next)", re.IGNORECASE))
            if await next_btn.count():
                await safe_click(next_btn.first)
                try:
                    await main_page.wait_for_selector('article[data-automation="normalJob"]', state="attached", timeout=10000)
                except Exception:
                    pass
            else:
                console.print("[dim]End of pages.[/dim]")
                break

        console.print(f"\n[bold green]Done! Applied to {apps_done} jobs.[/bold green]")
        
        # Save detailed log 
        import os
        os.makedirs("automaton/logs", exist_ok=True)
        log_path = f"automaton/logs/{run_timestamp}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(run_log, f, indent=4, ensure_ascii=False)
        console.print(f"[bold cyan]Detailed run log saved to: {log_path}[/bold cyan]")
        
        await context.close()

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    console.print("\n[bold cyan]JobStreet Auto-Applier[/bold cyan]\n")

    keyword = Prompt.ask("Job keyword", default="")
    location = Prompt.ask("Location", default="Jakarta")
    extra_excl = Prompt.ask("Extra exclude keywords (comma-separated)", default="dosen, echonomic, principal, christian, christiann, kristen, religious, religion, agama, china, chinese, mandarin, toddler, todly, toddly, tk, kindergarden, bayi, baby. musik, seni, renang, music, singing, sport")
    max_str = Prompt.ask("Max applications (type ALL for no limit)", default="ALL")
    
    console.print("\n[bold]Mode Selection (For new 'How many years' questions)[/bold]")
    console.print("  1. [cyan]Semi-Auto[/cyan] (Waits 2s for manual input before auto-answering)")
    console.print("  2. [magenta]Fully Auto[/magenta] (Instantly answers to keep the scraper running at max speed)")
    mode_raw = Prompt.ask("Choose mode", choices=["1", "2"], default="2")
    auto_mode = "Semi" if mode_raw == "1" else "Fully"
    
    dry = Prompt.ask("Dry run? (Y/n)", default="Y")

    exclude_list = KEYWORDS_TO_EXCLUDE.copy()
    if extra_excl.strip():
        exclude_list += [k.strip().lower() for k in extra_excl.split(",") if k.strip()]

    max_str_clean = max_str.strip().upper()
    if max_str_clean == "ALL":
        max_apps = 999999
        max_display = "ALL"
    else:
        try:
            max_apps = int(max_str)
            max_display = str(max_apps)
        except ValueError:
            max_apps = 999999
            max_display = "ALL"

    is_dry = dry.strip().lower() not in ("n", "no", "false")

    console.print(f"\n[magenta]Keyword:[/magenta] {keyword}  [magenta]Location:[/magenta] {location}")
    console.print(f"[dim]Excludes: {', '.join(exclude_list[:5])}{'...' if len(exclude_list) > 5 else ''}[/dim]")
    console.print(f"[dim]Dry run: {is_dry} | Max: {max_display} | Auto: {auto_mode}[/dim]\n")

    try:
        asyncio.run(run(keyword, location, exclude_list, max_apps, is_dry, auto_mode))
    except KeyboardInterrupt:
        console.print("\n[red]Stopped by user.[/red]")


if __name__ == "__main__":
    main()
