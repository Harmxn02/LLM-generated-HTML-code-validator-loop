import argparse
import json
import random
import time

import ollama
import requests

parser = argparse.ArgumentParser(description="Generate and validate HTML using Ollama.")
parser.add_argument(
	"--validate-only",  # python ollama_api.py --validate-only
	action="store_true",
	help="Skip generation and only validate an existing HTML file.",
)
parser.add_argument(
	"--local",  # python ollama_api.py --local
	action="store_true",
	help="Use a local W3C validator in Docker instead of the cloud API.",
)
args = parser.parse_args()


def choose_prompt(file_path: str = "prompts.json"):
	"""Load prompts from a JSON file and return a randomly selected one."""
	with open(file_path, "r") as f:
		all_data = json.load(f)
	prompts = all_data["prompts"]
	prompt_to_use = random.choice(prompts)
	return prompt_to_use


def generate_html(model_name: str, prompt: str, output_path: str):
	"""Stream a response from a local Ollama model and save the output as an HTML file"""
	html_output = ""

	stream = ollama.chat(
		model=model_name,
		messages=[{"role": "user", "content": prompt}],
		stream=True,
	)

	for chunk in stream:
		content = chunk.get("message", {}).get("content", "")
		print(content, end="", flush=True)
		html_output += content

	with open(output_path, "w", encoding="utf-8") as f:
		f.write(html_output)
	print(f"\nHTML saved to {output_path}")


def validate_html(
	html_path: str,
	validator: str,
	validation_output_path: str = "validation_result.json",
):
	"""Submit an HTML file to the W3C validator and save the JSON results to disk."""
	with open(html_path, "rb") as f:
		html_content = f.read()

	while True:
		response = requests.post(
			validator,
			headers={
				"Content-Type": "text/html; charset=utf-8",
				"User-Agent": "Mozilla/5.0",
			},
			data=html_content,
		)

		if response.status_code == 200:
			break

		print(f"Request failed with status code {response.status_code}.")
		for i in range(5, 0, -1):
			print(f"Retrying in {i} seconds", end="\r", flush=True)
			time.sleep(1)
		print()

	result = response.json()

	with open(validation_output_path, "w") as f:
		json.dump(result, f, indent=4)

	print(f"Validation results saved to {validation_output_path}")
	return validation_output_path


def parse_validation_results(filepath: str):
	"""Load and parse a W3C validation JSON result file, printing a summary of errors, warnings, and info messages found."""
	with open(filepath) as f:
		result = json.load(f)

	messages = result.get("messages", [])

	errors = [m for m in messages if m["type"] == "error"]
	warnings = [
		m for m in messages if m["type"] == "info" and m.get("subType") == "warning"
	]
	infos = [
		m for m in messages if m["type"] == "info" and m.get("subType") != "warning"
	]

	print(f"{'=' * 50}")
	print(f"Errors:   {len(errors)}")
	print(f"Warnings: {len(warnings)}")
	print(f"Info:     {len(infos)}")
	print(f"{'=' * 50}\n")

	for category, label in [(errors, "ERROR"), (warnings, "WARNING"), (infos, "INFO")]:
		for msg in category:
			line = msg.get("lastLine", "?")
			col = msg.get("lastColumn", "?")
			print(f"[{label}] Line {line}, Col {col}: {msg['message']}")


if __name__ == "__main__":
	cloud_validator = "https://validator.w3.org/nu/?out=json"
	local_validator = "http://localhost:8888/?out=json"  # requires Docker container: `docker run -p 8888:8888 validator/validator:latest --port 8888`
	validator = ""

	if args.local:
		validator = local_validator
	else:
		validator = cloud_validator

	if not args.validate_only:
		prompt = choose_prompt("./prompts/prompts.json")

		current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
		output_path = f"./html/generated_{current_time}.html"

		# HTML Generation
		generate_html(
			model_name="gemma3:1b",  # qwen3:8b, gemma3:1b
			prompt=prompt,
			output_path=output_path,
		)

		# HTML Validation
		validation_path = validate_html(html_path=output_path, validator=validator)
		parse_validation_results(validation_path)

	else:
		file_to_validate = "./html/generated_2026-03-17_13-21-29.html"
		validation_path = validate_html(html_path=file_to_validate, validator=validator)
		parse_validation_results(validation_path)
