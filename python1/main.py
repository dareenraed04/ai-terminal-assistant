import os
from google import genai
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

console = Console()

# قراءة مفتاح الـ API بشكل آمن من النظام
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    console.print("[bold red]Error: GEMINI_API_KEY is missing! Please check your .env file.[/bold red]")
    exit(1)

client = genai.Client(
    api_key=API_KEY,
    http_options={"timeout": 60000}
)

SYSTEM_PROMPT = """
You are an expert Linux/Windows CLI and Git assistant.
When the user describes a task, respond concisely in Markdown with:
1. **Command:** The exact terminal command inside a bash code block.
2. **Explanation:** Brief bullet points explaining the command and its flags.
3. **Warning:** Only if the command is destructive (e.g., rm, overwrite, kill).
"""

def ask_cli_assistant(user_query: str) -> str:
    models_to_try = ["gemini-3.8-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
    
    try:
        dynamic_models = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
        ]
        for dm in dynamic_models:
            if dm not in models_to_try:
                models_to_try.insert(0, dm)
    except Exception:
        pass

    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                ),
            )
            return response.text
        except Exception as e:
            last_error = e
            continue
            
    return f"**⚠️ خطأ في الاتصال:** {last_error}"

def main():
    console.print(
        Panel.fit(
            f"[bold green]🤖 AI Terminal Command Assistant[/bold green]\n"
            f"[dim]Smart Multi-Model Fallback Active | Type 'exit' to quit.[/dim]",
            border_style="green",
        )
    )

    while True:
        try:
            query = console.input("\n[bold yellow]❯ What do you need?[/bold yellow] ").strip()
            if not query:
                continue
            if query.lower() in {"exit", "quit"}:
                console.print("[cyan]Goodbye! 👋[/cyan]")
                break

            with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                answer = ask_cli_assistant(query)

            console.print(
                Panel(
                    Markdown(answer),
                    title="[bold blue]Suggested Command[/bold blue]",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        except KeyboardInterrupt:
            console.print("\n[cyan]Goodbye! 👋[/cyan]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()