import asyncio
import os
import re
from typing import Optional, List, Dict, Set
from rich.console import Console
from rich.prompt import Prompt
from playwright.async_api import async_playwright

console = Console()
QUESTIONS_FILE = "automaton/company_questions.md"

def load_existing_questions() -> Set[str]:
    """Load all existing questions from the markdown file."""
    if not os.path.exists(QUESTIONS_FILE):
        return set()
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    questions = set()
    for match in re.finditer(r"### Question:\s*(.+)", content):
        questions.add(match.group(1).strip())
    return questions

def append_question(q_text: str, q_type: str, answer: str = "", options: Optional[List[str]] = None):
    """Append a new question and its mapped answer to the markdown file."""
    with open(QUESTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(f"### Question: {q_text}\n")
        f.write(f"### Type: {q_type}\n")
        if options:
            f.write(f"### Options: {' | '.join(options)}\n")
        f.write(f"**Answer:** {answer}\n\n---\n\n")

async def parse_question_block(q_block) -> Optional[Dict]:
    """Extract question text, type, and options from a UI block."""
    try:
        q_text = await q_block.inner_text()
        q_text = q_text.replace('*', '').strip()
        
        # Ignore filter buttons or tiny UI elements
        if len(q_text) < 5 or "Tampilkan filter" in q_text or "Sembunyikan" in q_text or "Cari" in q_text:
            return None
            
        q_type = "Text"
        options = []
        
        # Navigate up the DOM tree to find the input elements (similar heuristic to apply_jobs.py)
        wrapper = await q_block.evaluate_handle('''el => {
            let p = el.parentElement;
            if (p && p.parentElement) p = p.parentElement;
            if (p && p.parentElement) p = p.parentElement;
            return p;
        }''')
        
        # Check if dropdown
        select = await wrapper.query_selector("select")
        if select:
            q_type = "Dropdown"
            opts = await select.query_selector_all("option")
            for o in opts:
                t = await o.inner_text()
                if t.strip() and "select" not in t.lower() and "pilih" not in t.lower():
                    options.append(t.strip())
        else:
            # Check Radio/Checkbox
            radios = await wrapper.query_selector_all("input[type='radio'], input[type='checkbox']")
            if radios:
                q_type = "Choice"
                labels = await wrapper.query_selector_all("label")
                for l in labels:
                    t = await l.inner_text()
                    if t.strip():
                        options.append(t.strip())

        return {
            "text": q_text,
            "type": q_type,
            "options": options
        }
    except Exception:
        # Silently ignore stale element exceptions when rapid DOM changes occur
        return None

async def prompt_user_for_answer(question_data: Dict) -> str:
    """Interactively prompt the user for an answer via the CLI."""
    console.print(f"\n[bold cyan]New Question Detected:[/bold cyan] {question_data['text']}")
    console.print(f"[dim]Type: {question_data['type']}[/dim]")
    
    q_type = question_data["type"]
    options = question_data["options"]
    
    if q_type in ["Dropdown", "Choice"] and options:
        console.print("Options:")
        for idx, opt in enumerate(options):
            console.print(f"  {idx + 1}. {opt}")
            
        choice_idx = await asyncio.to_thread(Prompt.ask, "Select option number (or type exact text)", default="1")
        try:
            idx = int(choice_idx) - 1
            if 0 <= idx < len(options):
                return options[idx]
            else:
                return choice_idx
        except ValueError:
            return choice_idx  # Return raw text if not a number
    else:
        # Default text input
        answer = await asyncio.to_thread(Prompt.ask, "Enter your answer")
        return answer.strip()

async def extract_questions():
    existing_questions = load_existing_questions()
    console.print(f"[green]Loaded {len(existing_questions)} existing questions from {QUESTIONS_FILE}.[/green]")
    
    console.print("[cyan]Connecting to your running Chrome browser...[/cyan]")
    console.print("Make sure Chrome is running with remote debugging enabled:")
    console.print('Example: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
    
    async with async_playwright() as p:
        try:
            # Connect to existing Chrome over CDP
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            console.print("[bold green]Successfully connected to Chrome![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Failed to connect to Chrome: {e}[/bold red]")
            console.print("Please ensure you have started Chrome with --remote-debugging-port=9222")
            return

        contexts = browser.contexts
        if not contexts:
            console.print("[yellow]No browser contexts found. Make sure Chrome is open.[/yellow]")
            return
            
        context = contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate to JobStreet 
        console.print("[cyan]Switching current tab to JobStreet...[/cyan]")
        await page.goto("https://id.jobstreet.com/")

        console.print("\n[bold]Browser is connected and on JobStreet.[/bold]")
        console.print("Please manually navigate to ANY job and click 'Apply' (Lamaran Cepat).")
        console.print("Once the questionnaire appears, I will detect and prompt you for any new questions.")
        console.print("[yellow]Waiting for questionnaire... (Press Ctrl+C to abort at any time)[/yellow]\n")
        
        try:
            while True:
                await page.wait_for_timeout(2000)
                
                # Look for question blocks based on typical JobStreet form structure
                form_locator = page.locator("form, div[role='dialog']")
                if await form_locator.count() > 0:
                    q_blocks = await form_locator.first.locator("label, [elementtiming='Question Text']").element_handles()
                else:
                    q_blocks = await page.locator("label, [elementtiming='Question Text']").element_handles()
                
                if len(q_blocks) > 0:
                    for q_block in q_blocks:
                        q_data = await parse_question_block(q_block)
                        
                        if q_data and q_data["text"] not in existing_questions:
                            answer = await prompt_user_for_answer(q_data)
                            
                            console.print(f"[green]Saving mapped answer for '{q_data['text']}' -> '{answer}'[/green]")
                            append_question(
                                q_text=q_data["text"],
                                q_type=q_data["type"],
                                answer=answer,
                                options=q_data["options"] if q_data["options"] else None
                            )
                            existing_questions.add(q_data["text"])
                            
        except asyncio.CancelledError:
            console.print("\n[yellow]Extraction stopped.[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Extraction interrupted by user.[/yellow]")
        except Exception as e:
            # Continue polling even on some errors
            pass

        console.print("[cyan]Disconnecting from browser...[/cyan]")
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(extract_questions())
    except KeyboardInterrupt:
        console.print("\n[red]Process interrupted by user.[/red]")

