import os
import re
from typing import List, Dict

from flask import Flask, jsonify, render_template, request
import google.generativeai as genai

# Configuration
MAX_CODE_CHARS = 4000
CONTROL_KEYWORDS = [
    "START",
    "PROCESS:",
    "LOOP:",
    "DECISION:",
    "YES ->",
    "NO ->",
    "END",
]
CONTROL_KEYWORD_PATTERN = re.compile(r"(START|PROCESS:|LOOP:|DECISION:|YES ->|NO ->|END)")

GEMINI_PROMPT_TEMPLATE = """You are a software analysis assistant.

Task:
Extract the control flow of the given code.

STRICT RULES:
- Output ONLY control-flow steps.
- Use ONLY the keywords listed below.
- Do NOT draw any flowchart.
- Do NOT use ASCII art.
- Do NOT explain anything.

OUTPUT FORMAT:
Each step MUST start with one of these keywords:

START
PROCESS:
LOOP:
DECISION:
YES ->
NO ->
END

CODE:
<<<
{USER_CODE}
>>>"""


def configure_gemini() -> genai.GenerativeModel:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-pro")
    return genai.GenerativeModel(model_name)


# Initialize Flask app and Gemini model lazily
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64KB request limit

_gemini_model = None


def get_gemini_model() -> genai.GenerativeModel:
    global _gemini_model
    if _gemini_model is None:
        _gemini_model = configure_gemini()
    return _gemini_model


def callGemini(user_code: str) -> str:
    """Call Gemini to extract control-flow logic from user code.

    This function is the ONLY place we use Gemini.
    """
    model = get_gemini_model()
    prompt = GEMINI_PROMPT_TEMPLATE.format(USER_CODE=user_code)

    try:
        response = model.generate_content(prompt)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    text = getattr(response, "text", None)
    if not text:
        # Some SDK versions use .candidates; handle defensively.
        try:
            candidates = getattr(response, "candidates", []) or []
            if candidates:
                text = getattr(candidates[0], "content", {}).get("parts", [{}])[0].get("text", "")
        except Exception:  # noqa: BLE001
            text = None

    if not text:
        raise RuntimeError("Gemini returned an empty response.")

    return text.strip()


def normalizeControlFlow(raw_output: str) -> List[Dict[str, str]]:
    """Normalize Gemini output into an ordered list of control-flow steps.

    Each step is a dict with keys: type (START, PROCESS, LOOP, DECISION, YES, NO, END) and text.
    """
    if not raw_output or not raw_output.strip():
        raise ValueError("Empty control-flow output from Gemini.")

    text = raw_output.replace("\r", " ")
    # Ensure keywords are detectable regardless of newlines or extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    matches = list(CONTROL_KEYWORD_PATTERN.finditer(text))
    if not matches:
        raise ValueError("No valid control-flow keywords found in Gemini output.")

    steps: List[Dict[str, str]] = []

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        segment = text[start:end].strip()

        keyword = match.group(0)
        # Extract the rest of the segment after the keyword
        remainder = segment[len(keyword) :].strip(" -:>")

        if keyword == "START":
            step_type = "START"
        elif keyword == "PROCESS:":
            step_type = "PROCESS"
        elif keyword == "LOOP:":
            step_type = "LOOP"
        elif keyword == "DECISION:":
            step_type = "DECISION"
        elif keyword == "YES ->":
            step_type = "YES"
        elif keyword == "NO ->":
            step_type = "NO"
        elif keyword == "END":
            step_type = "END"
        else:
            # Fallback should never occur due to regex pattern
            continue

        steps.append({"type": step_type, "text": remainder})

    if not steps:
        raise ValueError("Failed to parse any control-flow steps from Gemini output.")

    return steps


def renderAsciiFlowchart(steps: List[Dict[str, str]]) -> str:
    """Render a deterministic ASCII flowchart from normalized steps.

    Rendering rules:
    - Vertical, linear format.
    - Shapes:
      ( START ) / ( END )
      [ process ]
      < condition ? >
    - Branches:
      |-- Yes -->
      |-- No  -->
    - Loops:
      |-- loop back to < condition ? >
    """
    lines: List[str] = []

    def add_connector() -> None:
        """Append a vertical connector and a down-arrow for clarity."""
        lines.append("   |")
        lines.append("   v")

    # Add explicit START if not present
    explicit_start = any(step["type"] == "START" for step in steps)
    if not explicit_start:
        lines.append("( START )")
        if steps:
            add_connector()

    i = 0
    n = len(steps)

    while i < n:
        step = steps[i]
        step_type = step["type"]
        text = step["text"] or ""

        if step_type == "START":
            lines.append("( START )")
            if i < n - 1:
                add_connector()
        elif step_type == "PROCESS":
            label = text if text else "process"
            lines.append(f"[ {label} ]")
            # Only add connector if not last step and next is not END
            if i < n - 1 and steps[i + 1]["type"] != "END":
                add_connector()
        elif step_type == "DECISION":
            condition = text if text else "condition ?"
            if not condition.endswith("?"):
                condition = f"{condition} ?"
            lines.append(f"< {condition} >")

            # Look ahead for immediate YES/NO branches
            j = i + 1
            yes_rendered = False
            no_rendered = False
            while j < n and steps[j]["type"] in {"YES", "NO"}:
                branch = steps[j]
                branch_label = branch["text"] if branch["text"] else ""

                # If the branch is immediately followed by a PROCESS step,
                # render them together on a single line for a smoother layout.
                k = j + 1
                combined_process_label = None
                if k < n and steps[k]["type"] == "PROCESS":
                    combined_process_label = steps[k]["text"] or "process"

                # Skip redundant empty branches of the same type (e.g. a
                # second bare "YES ->" with no text and no process), since
                # they add noise without conveying extra information.
                if (
                    branch["type"] == "YES"
                    and yes_rendered
                    and combined_process_label is None
                    and not branch_label
                ) or (
                    branch["type"] == "NO"
                    and no_rendered
                    and combined_process_label is None
                    and not branch_label
                ):
                    j += 1
                    continue

                if branch["type"] == "YES":
                    if combined_process_label is not None:
                        lines.append(f"|-- Yes --> [ {combined_process_label} ]")
                        yes_rendered = True
                        j = k + 1
                        continue
                    lines.append(f"|-- Yes --> {branch_label}".rstrip())
                    yes_rendered = True
                else:
                    # Pad 'No' spacing to keep arrows aligned
                    if combined_process_label is not None:
                        lines.append(f"|-- No  --> [ {combined_process_label} ]")
                        no_rendered = True
                        j = k + 1
                        continue
                    lines.append(f"|-- No  --> {branch_label}".rstrip())
                    no_rendered = True

                j += 1

            # If we rendered any explicit YES/NO branches, reconnect back
            # to the main vertical flow only if there are more steps.
            if yes_rendered or no_rendered:
                if j < n:
                    add_connector()
                i = j - 1  # -1 because loop will increment
            else:
                # No YES/NO found directly after; keep linear
                if i < n - 1 and steps[i + 1]["type"] != "END":
                    add_connector()
        elif step_type == "YES":
            # YES not attached to an immediately preceding DECISION
            label = step["text"] if step["text"] else ""
            lines.append(f"|-- Yes --> {label}".rstrip())
            if i < n - 1 and steps[i + 1]["type"] != "END":
                add_connector()
        elif step_type == "NO":
            label = step["text"] if step["text"] else ""
            lines.append(f"|-- No  --> {label}".rstrip())
            if i < n - 1 and steps[i + 1]["type"] != "END":
                add_connector()
        elif step_type == "LOOP":
            label = text if text else "loop condition ?"
            if not label.endswith("?"):
                label = f"{label} ?"
            lines.append(f"+--- LOOP: {label} ---+")
            # Look ahead to see if next step is a DECISION (nested inside loop)
            if i < n - 1 and steps[i + 1]["type"] not in {"END"}:
                add_connector()
        elif step_type == "END":
            lines.append("( END )")
        else:
            # Unknown type; skip to keep renderer deterministic
            pass

        i += 1

    # Ensure we end with END if not explicit
    if not any(step["type"] == "END" for step in steps):
        lines.append("( END )")

    return "\n".join(lines)


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/flowchart", methods=["POST"])
def generate_flowchart():
    if not request.is_json:
        return jsonify({"error": "Expected JSON body."}), 400

    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")

    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "'code' must be a non-empty string."}), 400

    if len(code) > MAX_CODE_CHARS:
        return jsonify({"error": f"Code is too long. Maximum {MAX_CODE_CHARS} characters allowed."}), 400

    try:
        raw_output = callGemini(code)
        steps = normalizeControlFlow(raw_output)
        ascii_chart = renderAsciiFlowchart(steps)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({
        "ascii": ascii_chart,
        "steps": steps,
    })


if __name__ == "__main__":
    # Local development server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
