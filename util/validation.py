import json
import time

import requests


def validate_html(
	html_path: str,
	validator: str,
	validation_output_path: str = "validation_result.json",
) -> str:
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


def parse_validation_results(filepath: str) -> None:
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
