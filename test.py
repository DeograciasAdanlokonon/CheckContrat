from core.openai_engine import OpenaiAnalyse

engine = OpenaiAnalyse()

# Contract example
result = engine.analyse_contract("test-contrat.pdf", "Analyse ce contrat de travail et indique s'il est conforme au droit du travail français.")
print(result)

# Fiche de paie example
result = engine.analyse_fiche(
    fiche_file="12_payslipX.pdf",
    contrat_file="12_contractY.pdf",
    prompt="Vérifie si la fiche de paie correspond bien au contrat et identifie toute anomalie, conformement au droit du travail français.",
    hours=35
)
print(result)
