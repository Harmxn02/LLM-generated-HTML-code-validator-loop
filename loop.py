import argparse
import json
import os
import sys
import time

from ollama_api import (
	choose_prompt,
	generate_html,
	parse_validation_results,
	validate_html,
)

# Temporarily clear argv so that ollama_api's module-level argparse.parse_args()
# doesn't choke on this script's own arguments when the module is imported.
_original_argv = sys.argv[:]
sys.argv = sys.argv[:1]


sys.argv = _original_argv

parser = argparse.ArgumentParser(
	description="Generate HTML, validate it, reprompt to fix issues, then validate again."
)
parser.add_argument(
	"--local",
	action="store_true",
	help="Use a local W3C validator in Docker instead of the cloud API.",
)
args = parser.parse_args()

HTML_DIR = "./html/reprompt"
VALIDATION_DIR = "./validation/reprompt"

os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(VALIDATION_DIR, exist_ok=True)


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

	if issue_lines:
		issues_text = "\n".join(issue_lines)
	else:
		issues_text = "No errors or warnings were found."

	reprompt = (
		f"The following HTML was originally generated for this request:\n"
		f"{original_prompt}\n\n"
		f"Here is the generated HTML:\n"
		f"{html_content}\n\n"
		f"The W3C HTML validator reported these issues:\n"
		f"{issues_text}\n\n"
		f"Please fix every issue listed above and return only the corrected, "
		f"complete HTML document. Do not include any explanation or markdown fences."
	)
	return reprompt


def summarise_validation(validation_path: str) -> dict:
	"""Return a dict with error, warning, and info counts from a validation result file."""
	with open(validation_path, "r", encoding="utf-8") as f:
		result = json.load(f)

	messages = result.get("messages", [])
	return {
		"errors": sum(1 for m in messages if m["type"] == "error"),
		"warnings": sum(
			1 for m in messages if m["type"] == "info" and m.get("subType") == "warning"
		),
		"infos": sum(
			1 for m in messages if m["type"] == "info" and m.get("subType") != "warning"
		),
	}


if __name__ == "__main__":
	cloud_validator = "https://validator.w3.org/nu/?out=json"
	local_validator = "http://localhost:8888/?out=json"
	validator = local_validator if args.local else cloud_validator

	model_name = "gemma3:1b"  # qwen3:8b, gemma3:1b
	timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

	# ── Step 1: Choose a prompt and generate the initial HTML ──────────────────
	prompt = choose_prompt("./prompts/prompts.json")
	print(f"\n{'=' * 50}")
	print("STEP 1 — Generating initial HTML")
	print(f"{'=' * 50}\n")

	initial_html_path = f"{HTML_DIR}/generated_{timestamp}.html"
	generate_html(model_name=model_name, prompt=prompt, output_path=initial_html_path)

	# ── Step 2: Validate the initial HTML ─────────────────────────────────────
	print(f"\n{'=' * 50}")
	print("STEP 2 — Validating initial HTML")
	print(f"{'=' * 50}\n")

	initial_validation_path = f"{VALIDATION_DIR}/validation_{timestamp}.json"
	validate_html(
		html_path=initial_html_path,
		validator=validator,
		validation_output_path=initial_validation_path,
	)
	parse_validation_results(initial_validation_path)
	before = summarise_validation(initial_validation_path)

	# ── Step 3: Build the reprompt and re-generate HTML ───────────────────────
	print(f"\n{'=' * 50}")
	print("STEP 3 — Re-generating HTML using validation feedback")
	print(f"{'=' * 50}\n")

	reprompt = build_reprompt(
		original_html_path=initial_html_path,
		validation_path=initial_validation_path,
		original_prompt=prompt,
	)
	reprompted_html_path = f"{HTML_DIR}/reprompted_{timestamp}.html"
	generate_html(
		model_name=model_name, prompt=reprompt, output_path=reprompted_html_path
	)

	# ── Step 4: Validate the reprompted HTML ──────────────────────────────────
	print(f"\n{'=' * 50}")
	print("STEP 4 — Validating reprompted HTML")
	print(f"{'=' * 50}\n")

	reprompted_validation_path = (
		f"{VALIDATION_DIR}/validation_reprompted_{timestamp}.json"
	)
	validate_html(
		html_path=reprompted_html_path,
		validator=validator,
		validation_output_path=reprompted_validation_path,
	)
	parse_validation_results(reprompted_validation_path)
	after = summarise_validation(reprompted_validation_path)

	# ── Step 5: Print a before/after comparison ───────────────────────────────
	print(f"\n{'=' * 50}")
	print("REPROMPT COMPARISON")
	print(f"{'=' * 50}")
	print(f"{'Metric':<12} {'Before':>8} {'After':>8} {'Δ':>8}")
	print(f"{'-' * 40}")
	for key in ("errors", "warnings", "infos"):
		delta = after[key] - before[key]
		sign = "+" if delta > 0 else ""
		print(
			f"{key.capitalize():<12} {before[key]:>8} {after[key]:>8} {sign + str(delta):>8}"
		)
	print(f"{'=' * 50}\n")
