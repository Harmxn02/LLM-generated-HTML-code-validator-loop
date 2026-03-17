import json
import random
import time

import requests


def choose_prompt(file_path: str = "prompts.json"):
	"""Load prompts from a JSON file and return a randomly selected one."""
	with open(file_path, "r") as f:
		all_data = json.load(f)
	prompts = all_data["prompts"]
	prompt_to_use = random.choice(prompts)
	return prompt_to_use


def setup_payload(model_name: str, api_url: str, prompt: str):
	"""Construct and return the API URL and request payload for the Ollama chat endpoint."""
	url = api_url if api_url else ValueError("`api_url` is required")
	payload = {
		"model": model_name if model_name else ValueError("`model_name` is required"),
		"messages": [
			{
				"role": "user",
				"content": prompt if prompt else ValueError("`prompt` is required"),
			}
		],
	}
	return url, payload


def parse_response(response, output_path: str):
	"""Stream and parse an Ollama API response, printing content and saving it as an HTML file."""
	if response.status_code == 200:
		html_output = ""
		for line in response.iter_lines(decode_unicode=True):
			if line:
				try:
					json_data = json.loads(line)
					if "message" in json_data and "content" in json_data["message"]:
						print(json_data["message"]["content"], end="")
						html_output += json_data["message"]["content"]
				except json.JSONDecodeError:
					print(f"Failed to parse line: {line}")

		with open(output_path, "w", encoding="utf-8") as f:
			f.write(html_output)
		print(f"HTML saved to {output_path}")
	else:
		print(
			f"Failed to get response from Ollama. Status code: {response.status_code}"
		)


def validate_html(
	html_path: str, validation_output_path: str = "validation_result.json"
):
	"""Submit an HTML file to the W3C validator and save the JSON results to disk."""
	with open(html_path, "rb") as f:
		html_content = f.read()

	response = requests.post(
		"https://validator.w3.org/nu/?out=json",
		headers={
			"Content-Type": "text/html; charset=utf-8",
			"User-Agent": "Mozilla/5.0",
		},
		data=html_content,
	)

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
	prompt = choose_prompt("./prompts/prompts.json")

	# qwen3:8b
	url, payload = setup_payload(
		model_name="gemma3:1b",
		api_url="http://localhost:11434/api/chat",
		prompt=prompt,
	)
	current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
	output_path = f"./html/generated_{current_time}.html"

	# API CALL
	response = requests.post(url, json=payload, stream=True)
	parse_response(response, output_path)

	# VALIDATION
	validation_path = validate_html(output_path)
	parse_validation_results(validation_path)
