<!-- markdownlint-disable MD010 -->

# LLM Generated HTML Code Validator Loop

## Voorbeeld van feedback-loop die (gedeeltelijk) werkt

De code die initieel gegenereerd werd, bevatte 14 errors en 1 warning. Na het toepasses van de feedback-loop, resteren er nog `maar' 5 errors en 0 warnings. De meeste errors zijn na 1 feedback-loop opgelost.

- model: `qwen3:8b` using `ollama serve`
- validator: `docker run -it --rm -p 8888:8888 ghcr.io/validator/validator:latest`
- run: `python loop.py --local`
- reprompt logica:

    ```python
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
    ```

> [!NOTE]
> Twee simpele trial-runs met `gemma3:1b` toonde geen verbetering, maar de test met bovenstaande resultaten gebruikte `qwen3:8b`. Ik kan nog niet met zekerheid zeggen waardoor dit verschil komt, wegens het beperkte aantal runs.

```bash
PS C:\Users\Harman\<project_path>\LLM Validator> python loop.py --local

==================================================
STEP 1 — Generating initial HTML
==================================================


HTML saved to ./html/reprompt/generated_2026-03-17_15-58-15.html

==================================================
STEP 2 — Validating initial HTML
==================================================

Validation results saved to ./validation/reprompt/validation_2026-03-17_15-58-15.json
==================================================
Errors:   14
Warnings: 1
Info:     0
==================================================

[ERROR] Line 1, Col 7: Non-space characters found without seeing a doctype first. Expected “<!DOCTYPE html>”.
[ERROR] Line 1, Col 7: Element “head” is missing a required instance of child element “title”.
[ERROR] Line 2, Col 15: Stray doctype.
[ERROR] Line 3, Col 6: Stray start tag “html”.
[ERROR] Line 4, Col 6: Stray start tag “head”.
[ERROR] Line 5, Col 9: Element “title” not allowed as child of element “body” in this context. (Suppressing further errors from this subtree.)
[ERROR] Line 6, Col 24: Attribute “charset” not allowed on element “meta” at this point.
[ERROR] Line 6, Col 24: Element “meta” is missing one or more of the following attributes: “content”, “itemprop”, “property”.
[ERROR] Line 7, Col 72: Attribute “name” not allowed on element “meta” at this point.
[ERROR] Line 7, Col 72: Element “meta” is missing one or more of the following attributes: “itemprop”, “property”.
[ERROR] Line 8, Col 9: Element “style” not allowed as child of element “body” in this context. (Suppressing further errors from this subtree.)
[ERROR] Line 57, Col 7: Stray end tag “head”.
[ERROR] Line 58, Col 6: Start tag “body” seen but an element of the same type was already open.
[ERROR] Line 101, Col 3: Non-space character in page trailer.
[WARNING] Line 1, Col 7: This document appears to be written in English. Consider adding “lang="en"” (or variant) to the “html” start tag.

==================================================
STEP 3 — Re-generating HTML using validation feedback
==================================================


HTML saved to ./html/reprompt/reprompted_2026-03-17_15-58-15.html

==================================================
STEP 4 — Validating reprompted HTML
==================================================

Validation results saved to ./validation/reprompt/validation_reprompted_2026-03-17_15-58-15.json
==================================================
Errors:   5
Warnings: 0
Info:     0
==================================================

[ERROR] Line 1, Col 7: Non-space characters found without seeing a doctype first. Expected “<!DOCTYPE html>”.
[ERROR] Line 1, Col 7: Element “head” is missing a required instance of child element “title”.
[ERROR] Line 2, Col 15: Stray doctype.
[ERROR] Line 3, Col 16: Stray start tag “html”.
[ERROR] Line 3, Col 16: Cannot recover after last error. Any further errors will be ignored.

==================================================
REPROMPT COMPARISON
==================================================
Metric         Before    After        Δ
----------------------------------------
Errors             14        5       -9
Warnings            1        0       -1
Infos               0        0        0
==================================================

PS C:\Users\Harman\<project_path>\LLM Validator>
```
