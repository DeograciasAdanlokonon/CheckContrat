from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib import colors
import json
import openai
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

# Adjust according to your project
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input-files"
OUTPUT_DIR = BASE_DIR / "output-files"

# Make sure output folder exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Initialize the OpenAI client
client = openai.OpenAI()

class OpenaiAnalyse:
    """
    Handles AI-powered analysis for contracts and payslips using OpenAI models.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def _generate_token(self) -> str:
        """Generate a short, URL-safe random token."""
        return secrets.token_urlsafe(8)

    def _read_file(self, filename: str) -> str:
        """
        Read the uploaded file (pdf or docx) and extract its text.
        You can improve extraction using libraries like PyPDF2 or python-docx.
        """
        filepath = INPUT_DIR / filename
        ext = filepath.suffix.lower()

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if ext == ".pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(str(filepath))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == ".docx":
            import docx
            doc = docx.Document(str(filepath))
            text = "\n".join(p.text for p in doc.paragraphs)
        else:
            raise ValueError("Unsupported file type. Must be PDF or DOCX.")

        return text.strip()

    def _generate_report_file(self, analysis_result: dict) -> str:
        """
        Save the AI analysis as a PDF report in output-files/ and return its filename.
        The PDF includes: title, result status, detailed explanation, and timestamp.
        """
        filename = f"report_{self._generate_token()}.pdf"
        output_path = OUTPUT_DIR / filename

        # Extract data safely
        result_text = analysis_result.get("result", "Non conforme")
        detail_text = analysis_result.get("detail", "Aucun détail fourni.")
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M")

        # PDF document setup
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("<b>Rapport d’analyse - CheckTonContrat</b>", styles["Title"]))
        story.append(Spacer(1, 0.5 * cm))

        # Result section
        color = colors.green if "conforme" in result_text.lower() else colors.red
        result_html = f"<font color='{color.hexval()}'><b>Résultat :</b> {result_text}</font>"
        story.append(Paragraph(result_html, styles["Heading2"]))
        story.append(Spacer(1, 0.3 * cm))

        # Detail section
        story.append(Paragraph("<b>Détails de l’analyse :</b>", styles["Heading3"]))
        story.append(Paragraph(detail_text.replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 0.5 * cm))

        # Timestamp
        story.append(Paragraph(f"<font size='9' color='gray'>Généré le {timestamp}</font>", styles["Normal"]))

        # Build PDF
        doc.build(story)

        return filename


    def _analyse_text(self, prompt: str, text: str) -> dict:
        """
        Send prompt + text to the OpenAI model and parse the structured response.
        """
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Tu es un expert juridique spécialisé en droit du travail français."},
                {"role": "user", "content": f"{prompt}\n\n---\n\n{text}"}
            ],
            temperature=0.3
        )

        ai_message = response.choices[0].message.content.strip()

        # Try to parse JSON structure if model returns structured data
        try:
            result_data = json.loads(ai_message)
        except json.JSONDecodeError:
            # fallback: simple heuristic extraction
            lower_msg = ai_message.lower()
            result = "Conforme" if "conforme" in lower_msg and "non" not in lower_msg else "Non conforme"
            result_data = {
                "result": result,
                "detail": ai_message
            }

        return result_data

    # ------------------------
    # MODULE 1 — CONTRAT
    # ------------------------
    def analyse_contract(self, file: str, prompt: str) -> dict:
        """
        Analyse a single contract file using OpenAI.
        """
        text = self._read_file(file)
        ai_result = self._analyse_text(prompt, text)

        report_file = self._generate_report_file(ai_result)
        return {
            "result": ai_result.get("result", "Non conforme"),
            "detail": ai_result.get("detail", ""),
            "report_file": report_file,
        }

    # ------------------------
    # MODULE 2 — FICHE DE PAIE
    # ------------------------
    def analyse_fiche(self, fiche_file: str, contrat_file: str, prompt: str, hours: int = None) -> dict:
        """
        Analyse a payslip and contract pair using OpenAI.
        """
        fiche_text = self._read_file(fiche_file)
        contrat_text = self._read_file(contrat_file)

        combined_text = f"Contrat de travail:\n{contrat_text}\n\nFiche de paie:\n{fiche_text}"
        if hours is not None:
            combined_text += f"\n\nNombre d'heures travaillées déclarées: {hours}"

        ai_result = self._analyse_text(prompt, combined_text)
        report_file = self._generate_report_file(ai_result)

        return {
            "result": ai_result.get("result", "Non conforme"),
            "detail": ai_result.get("detail", ""),
            "report_file": report_file,
        }
