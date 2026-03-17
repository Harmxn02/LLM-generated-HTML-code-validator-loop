import json

import requests

with open("./html/generated_2026-03-17_13-08-57.html", "rb") as f:
	html_content = f.read()

response = requests.post(
	"https://validator.w3.org/nu/?out=json",
	headers={"Content-Type": "text/html; charset=utf-8", "User-Agent": "Mozilla/5.0"},
	data=html_content,
)

result = response.json()

with open("validation_result.json", "w") as f:
	json.dump(result, f, indent=4)

print("Validation results saved to validation_result.json")


def parse_validation_results(filepath):
	"""
	Load and parse a W3C validation JSON result file, printing a
	summary of errors, warnings, and info messages found.
	"""
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


parse_validation_results("validation_result.json")
