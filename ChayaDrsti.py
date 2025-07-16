import gradio as gr
import fitz  # PyMuPDF
from docx import Document
import os
import google.generativeai as genai

# ─── Configuration ─────────────────────────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

APP_TITLE = "👁️‍🗨️ Chāyādr̥ṣṭi (छायादृष्टि) – Skill Insight and Career Pathway"
APP_DESCRIPTION = (
    "Chāyādr̥ṣṭi – the vision that sees through shadows. This AI-powered tool, envisioned by Dr. Partha Majumdar, "
    "reveals the skills within your résumé, recommends a fitting career path, highlights your growth edges, and "
    "offers thoughtful guidance to align your potential with your purpose."
)

paypal_url = os.getenv("PAYPAL_URL", "https://www.paypal.com/donate/dummy-link")

# ─── Utilities ──────────────────────────────────────────────────────────────────
def extract_text_from_file(file_path):
    if file_path.endswith(".pdf"):
        with fitz.open(file_path) as doc:
            return "\n".join(page.get_text() for page in doc)
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def make_prompt(text):
    return f"""
You are a career advisor.

Below is a candidate’s resume text:

{text}

Please respond with:
1. A clean, comma-separated list of all technical and non-technical skills found.
2. The most suitable job role for the candidate and a short justification.
3. A list of skills the candidate still needs to acquire to qualify for the above role.
4. A brief 2–3 sentence career guidance based on the current and missing skills.

Format the response strictly as:
[SKILLS]
...
[RECOMMENDED_ROLE]
...
[SKILL_GAP]
...
[CAREER_GUIDANCE]
...
"""

def parse_response(text):
    sections = {"[SKILLS]": "", "[RECOMMENDED_ROLE]": "", "[SKILL_GAP]": "", "[CAREER_GUIDANCE]": ""}
    current_section = None

    for line in text.splitlines():
        line = line.strip()
        if line in sections:
            current_section = line
        elif current_section:
            sections[current_section] += line + "\n"

    return (
        sections["[SKILLS]"].strip(),
        sections["[RECOMMENDED_ROLE]"].strip(),
        sections["[SKILL_GAP]"].strip(),
        sections["[CAREER_GUIDANCE]"].strip(),
    )

def analyze_resume(file):
    if file is None:
        return "No file uploaded", "", "", ""

    raw_text = extract_text_from_file(file.name)
    if not raw_text.strip():
        return "No readable text found in the file", "", "", ""

    prompt = make_prompt(raw_text)
    response = model.generate_content(prompt)
    return parse_response(response.text)

# ─── Gradio UI ──────────────────────────────────────────────────────────────────
with gr.Blocks() as app:
    gr.HTML(f"""
        <div style='text-align: center; margin-bottom: 30px;'>
            <p style='font-size: 40px; font-weight: bold;'>{APP_TITLE}</p>
            <p style='font-size: 16px; line-height: 1.6; max-width: 900px; margin: auto;'>
                {APP_DESCRIPTION}
            </p>
        </div>
    """)

    with gr.Row():
        file_input = gr.File(label="📄 Upload Resume (PDF or DOCX)", type="filepath")
        analyze_btn = gr.Button("🔍 Analyze Resume")

    with gr.Row():
        skills_box = gr.Textbox(label="📌 Skills Extracted", lines=6, autoscroll=True, interactive=False)
        role_box = gr.Textbox(label="💼 Recommended Job Role", lines=6, autoscroll=True, interactive=False)

    with gr.Row():
        gap_box = gr.Textbox(label="🧱 Skill Gap", lines=6, autoscroll=True, interactive=False)
        advice_box = gr.Textbox(label="📈 Career Guidance", lines=6, autoscroll=True, interactive=False)

    analyze_btn.click(fn=analyze_resume, inputs=file_input,
                      outputs=[skills_box, role_box, gap_box, advice_box])

    gr.HTML(f"""
        <div style="text-align:center; margin-top: 30px;">
            <a href="{paypal_url}" target="_blank">
                <button style="background-color:#0070ba;color:white;border:none;padding:10px 20px;
                font-size:16px;border-radius:5px;cursor:pointer;">
                    ❤️ Support Chāyādr̥ṣṭi via PayPal
                </button>
            </a>
        </div>
    """)

# Optional: app.launch() if you want it to run outside __main__
if __name__ == "__main__":
    # Determine if running on Hugging Face Spaces
    on_spaces = os.environ.get("SPACE_ID") is not None

    # Launch the app conditionally
    app.launch(share=not on_spaces)