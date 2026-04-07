import argparse
import os
import time

from util.generation import generate_html
from util.print_functions import section_print
from util.prompts import build_reprompt, choose_prompt
from util.validation import (
	parse_validation_results,
	summarise_validation,
	validate_html,
)

parser = argparse.ArgumentParser(
	description="Generate HTML, validate it, reprompt to fix issues, then validate again."
)
parser.add_argument(
	"--validate-only",
	action="store_true",
	help="Skip generation and only validate an existing HTML file.",
)
parser.add_argument(
	"--local",
	action="store_true",
	help="Use a local W3C validator in Docker instead of the cloud API.",
)

parser.add_argument(
	"--validate-and-regenerate",
	action="store_true",
	help="Validate an existing HTML file, then automatically build a reprompt and re-generate",
)


args = parser.parse_args()

CLOUD_VALIDATOR = "https://validator.w3.org/nu/?out=json"
LOCAL_VALIDATOR = "http://localhost:8888/?out=json"  # requires: docker run -p 8888:8888 validator/validator:latest --port 8888

HTML_DIR = "./html"
HTML_REPROMPT_DIR = "./html/reprompt"
VALIDATION_DIR = "./validation"
VALIDATION_REPROMPT_DIR = "./validation/reprompt"

MODEL_NAME = "qwen3:8b"  # qwen3:8b, gemma3:1b
PROMPTS_PATH = "./prompts/prompts.json"
VALIDATE_ONLY_FILE = "./html/reprompt/generated_2026-03-17_16-25-29.html"

if __name__ == "__main__":
	validator = LOCAL_VALIDATOR if args.local else CLOUD_VALIDATOR
	timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

	if args.validate_only:
		# ── Validate a single existing file, no generation ────────────────────
		os.makedirs(VALIDATION_DIR, exist_ok=True)
		validation_path = f"{VALIDATION_DIR}/validation_{timestamp}.json"
		validate_html(
			html_path=VALIDATE_ONLY_FILE,
			validator=validator,
			validation_output_path=validation_path,
		)
		parse_validation_results(validation_path)

	elif args.validate_and_regenerate:
		# ── Validate existing file, reprompt, re-generate, then validate again ─
		os.makedirs(HTML_REPROMPT_DIR, exist_ok=True)
		os.makedirs(VALIDATION_DIR, exist_ok=True)
		os.makedirs(VALIDATION_REPROMPT_DIR, exist_ok=True)

		# ── Step 1: Validate existing HTML ────────────────────────────────────
		section_print("STEP 1 — Validating existing HTML")

		initial_validation_path = f"{VALIDATION_DIR}/validation_{timestamp}.json"
		validate_html(
			html_path=VALIDATE_ONLY_FILE,
			validator=validator,
			validation_output_path=initial_validation_path,
		)
		parse_validation_results(initial_validation_path)
		before = summarise_validation(initial_validation_path)

		# ── Step 2: Reprompt and re-generate HTML ─────────────────────────────
		section_print("STEP 2 — Re-generating HTML using validation feedback")

		prompt = choose_prompt(PROMPTS_PATH)
		reprompt = build_reprompt(
			original_html_path=VALIDATE_ONLY_FILE,
			validation_path=initial_validation_path,
			original_prompt=prompt,
		)
		reprompted_html_path = f"{HTML_REPROMPT_DIR}/reprompted_{timestamp}.html"
		generate_html(
			model_name=MODEL_NAME, prompt=reprompt, output_path=reprompted_html_path
		)

		# ── Step 3: Validate reprompted HTML ──────────────────────────────────
		section_print("STEP 3 — Validating reprompted HTML")

		reprompted_validation_path = (
			f"{VALIDATION_REPROMPT_DIR}/validation_reprompted_{timestamp}.json"
		)
		validate_html(
			html_path=reprompted_html_path,
			validator=validator,
			validation_output_path=reprompted_validation_path,
		)
		parse_validation_results(reprompted_validation_path)
		after = summarise_validation(reprompted_validation_path)

		# ── Step 4: Before/after comparison ───────────────────────────────────
		section_print("REPROMPT COMPARISON")

		print(f"{'Metric':<12} {'Before':>8} {'After':>8} {'Δ':>8}")
		print(f"{'-' * 40}")
		for key in ("errors", "warnings", "infos"):
			delta = after[key] - before[key]
			sign = "+" if delta > 0 else ""
			print(
				f"{key.capitalize():<12} {before[key]:>8} {after[key]:>8} {sign + str(delta):>8}"
			)
		print(f"{'=' * 50}\n")

	else:
		os.makedirs(HTML_DIR, exist_ok=True)
		os.makedirs(HTML_REPROMPT_DIR, exist_ok=True)
		os.makedirs(VALIDATION_DIR, exist_ok=True)
		os.makedirs(VALIDATION_REPROMPT_DIR, exist_ok=True)

		prompt = choose_prompt(PROMPTS_PATH)

		# ── Step 1: Generate initial HTML ─────────────────────────────────────
		section_print("STEP 1 — Generating initial HTML")

		initial_html_path = f"{HTML_DIR}/generated_{timestamp}.html"
		generate_html(
			model_name=MODEL_NAME, prompt=prompt, output_path=initial_html_path
		)

		# ── Step 2: Validate initial HTML ─────────────────────────────────────
		section_print("STEP 2 — Validating initial HTML")

		initial_validation_path = f"{VALIDATION_DIR}/validation_{timestamp}.json"
		validate_html(
			html_path=initial_html_path,
			validator=validator,
			validation_output_path=initial_validation_path,
		)
		parse_validation_results(initial_validation_path)
		before = summarise_validation(initial_validation_path)

		# ── Step 3: Reprompt and re-generate HTML ─────────────────────────────
		section_print("STEP 3 — Re-generating HTML using validation feedback")

		reprompt = build_reprompt(
			original_html_path=initial_html_path,
			validation_path=initial_validation_path,
			original_prompt=prompt,
		)
		reprompted_html_path = f"{HTML_REPROMPT_DIR}/reprompted_{timestamp}.html"
		generate_html(
			model_name=MODEL_NAME, prompt=reprompt, output_path=reprompted_html_path
		)

		# ── Step 4: Validate reprompted HTML ──────────────────────────────────
		section_print("STEP 4 — Validating reprompted HTML")

		reprompted_validation_path = (
			f"{VALIDATION_REPROMPT_DIR}/validation_reprompted_{timestamp}.json"
		)
		validate_html(
			html_path=reprompted_html_path,
			validator=validator,
			validation_output_path=reprompted_validation_path,
		)
		parse_validation_results(reprompted_validation_path)
		after = summarise_validation(reprompted_validation_path)

		# ── Step 5: Before/after comparison ───────────────────────────────────
		section_print("REPROMPT COMPARISON")

		print(f"{'Metric':<12} {'Before':>8} {'After':>8} {'Δ':>8}")
		print(f"{'-' * 40}")
		for key in ("errors", "warnings", "infos"):
			delta = after[key] - before[key]
			sign = "+" if delta > 0 else ""
			print(
				f"{key.capitalize():<12} {before[key]:>8} {after[key]:>8} {sign + str(delta):>8}"
			)
		print(f"{'=' * 50}\n")
