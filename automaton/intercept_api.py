import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

QUESTIONS_FILE = "automaton/company_questions.md"
API_DUMP_FILE = "automaton/jobstreet_questions_api_dump.json"

def load_existing_questions() -> set:
    if not os.path.exists(QUESTIONS_FILE):
        return set()
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    questions = set()
    import re
    for match in re.finditer(r"### Question:\s*(.+)", content):
        questions.add(match.group(1).strip())
    return questions

def append_question(q_text, q_type, options=None):
    with open(QUESTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(f"### Question: {q_text}\n")
        f.write(f"### Type: {q_type}\n")
        if options:
            f.write(f"### Options: {', '.join(options)}\n")
        f.write("**Answer:** \n\n---\n\n")

# This callback intercepts ALL network traffic to find where jobstreet gets its questionnaire schema
async def handle_response(response):
    try:
        url = response.url
        # Look for typical API endpoints that serve questionnaire data (e.g. GraphQL, /api/applications, /questions)
        if "graphql" in url.lower() or "application" in url.lower() or "question" in url.lower() or "api.seek" in url.lower():
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                json_data = await response.json()
                
                # We dump all suspicious JSON to investigate the schema
                with open(API_DUMP_FILE, "a", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n")
                    json.dump(json_data, f, indent=2)
                    f.write("\n\n" + "="*80 + "\n\n")
                    
                # We specifically look for question arrays/structs inside the JSON
                _extract_questions_from_json(json_data)
    except Exception as e:
        pass # Ignore errors on non-json or incomplete responses

def _extract_questions_from_json(data, temp_existing=None):
    if temp_existing is None:
        temp_existing = load_existing_questions()
        
    if isinstance(data, dict):
        # Look for common question keys
        if "questionText" in data or "text" in data and "questionType" in data or "question" in data:
            q_text = data.get("questionText") or data.get("text") or data.get("question")
            
            if q_text and isinstance(q_text, str) and q_text not in temp_existing:
                print(f"[API] Found new question: {q_text}")
                temp_existing.add(q_text)
                
                q_type = data.get("questionType", data.get("type", "Unknown"))
                options = []
                # Look for choices/options array
                for key in ["choices", "options", "answers", "allowedValues"]:
                    if key in data and isinstance(data[key], list):
                        for opt in data[key]:
                            if isinstance(opt, dict) and "label" in opt:
                                options.append(opt["label"])
                            elif isinstance(opt, dict) and "text" in opt:
                                options.append(opt["text"])
                            elif isinstance(opt, str):
                                options.append(opt)
                
                append_question(q_text, q_type, options if options else None)
        
        for key, value in data.items():
            _extract_questions_from_json(value, temp_existing)
            
    elif isinstance(data, list):
        for item in data:
            _extract_questions_from_json(item, temp_existing)

async def investigate_source(job_url: str):
    print("Start tracing all API requests to locate the source of all questions...")
    # Clean the dump file
    with open(API_DUMP_FILE, "w", encoding="utf-8") as f:
        f.write("")
        
    async with async_playwright() as p:
        # User needs to be logged in to see applications, so we might need a persistent context
        # but for now we'll just open a browser and wait for user to interact
        browser = await p.chromium.launch(headless=False, slow_mo=50) 
        context = await browser.new_context()
        page = await context.new_page()
        
        # Intercept ALL responses to find the API source
        page.on("response", handle_response)
        
        print(f"Navigating to {job_url}")
        await page.goto(job_url)
        
        print("Please log in (if necessary) and click 'Apply'.")
        print("The script is now silently intercepting all API traffic in the background to find the raw Question Schema.")
        print("Once the application form is fully loaded on the screen, wait 5 seconds, then close the browser window.")
        
        # Wait indefinitely until the page is closed by the user
        try:
            await page.wait_for_event("close", timeout=0)
        except Exception:
            pass
            
        print("Browser closed. Finished tracing APIs.")
        print(f"Check {API_DUMP_FILE} for raw JSON data dumps.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python intercept_api.py <job_url>")
    else:
        asyncio.run(investigate_source(sys.argv[1]))
