import json
import random


def choose_prompt(file_path: str = "prompts.json") -> str:
	"""Load prompts from a JSON file and return a randomly selected one."""
	with open(file_path, "r") as f:
		all_data = json.load(f)
	return random.choice(all_data["prompts"])


def build_reprompt(
	original_html_path: str, validation_path: str, original_prompt: str
) -> str:
	"""Construct a follow-up prompt that asks the model to fix the HTML based on W3C validation results.

	Reads the previously generated HTML and the saved validation JSON, collects all
	errors and warnings, and combines them with the original prompt into a single
	instruction string that can be passed directly to generate_html.
	"""
	with open(original_html_path, "r", encoding="utf-8") as f:
		html_content = f.read()

	with open(validation_path, "r", encoding="utf-8") as f:
		validation_result = json.load(f)

	messages = validation_result.get("messages", [])
	errors = [m for m in messages if m["type"] == "error"]
	warnings = [
		m for m in messages if m["type"] == "info" and m.get("subType") == "warning"
	]

	issue_lines = []
	for m in errors + warnings:
		line = m.get("lastLine", "?")
		col = m.get("lastColumn", "?")
		label = "ERROR" if m["type"] == "error" else "WARNING"
		issue_lines.append(f"[{label}] Line {line}, Col {col}: {m['message']}")

	issues_text = (
		"\n".join(issue_lines) if issue_lines else "No errors or warnings were found."
	)

	return (
		f"The following HTML was originally generated for this request:\n"
		f"{original_prompt}\n\n"
		f"Here is the generated HTML:\n"
		f"{html_content}\n\n"
		f"The W3C HTML validator reported these issues:\n"
		f"{issues_text}\n\n"
		f"Please fix every issue listed above and return only the corrected, "
		f"complete HTML document. Do not include any explanation or markdown fences."
	)
