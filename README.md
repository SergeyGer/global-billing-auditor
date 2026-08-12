# Global Billing & Invoice Compliance Auditor (Mini-MVP)

A fintech-focused internal tooling prototype designed to demonstrate automated payroll calculations, multi-country tax estimation, and AI-assisted compliance auditing. 

This project was built autonomously as part of my application for the **Billing Platform Product Manager** role at **Remote.com**. It showcases a tech-native, hands-on PM approach — validating product hypotheses and vertical workflows without consuming core engineering velocity.

---

## 🚀 Key Features

* **Invoice Audit Calculator:** Simulates employer costs, platform compliance fees, and country-specific tax/VAT structures dynamically based on selected country logic (US, UK, Germany) and employment type.
* **AI Invoice Compliance Checker:** Evaluates raw invoice data or vendor text streams against rigid local compliance requirements (e.g., flagging missing W-8BEN forms for US contractors or missing VAT metadata for German entities).
* **Asynchronous Audit Dashboard:** A simulated asynchronous, high-throughput log data table reflecting transactional metrics, status parameters, and data-driven filters.

---

## 🛠️ Tech Stack & Methodology

* **Language & Framework:** Python 3, Streamlit (for rapid user interface and functional deployment).
* **Development Strategy:** 100% built, tested, and debugged using next-generation AI-native tools (**Cursor** and **Claude Code**). 
* **Product Alignment:** Tailored specifically to address Fintech / Billing platform scaling challenges, emphasizing data accuracy, operational compliance, and automated services.

---

## 💻 Local Installation & Setup

To run this application locally on your machine, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd remote-billing-audit
   ```

2. **Install dependencies:**
   Make sure you have Python installed, then run:
   ```bash
   pip install streamlit
   ```

3. **Launch the Streamlit app:**
   ```bash
   streamlit run app.py
   ```
   *The application will automatically open in your default browser at `http://localhost:8501`.*

---

## 👨‍💼 About the Author

**Sergey Gerasimov** — Senior Product Professional & Systems Architect.
* Over 15 years of technical lifecycle and account management experience at **Microsoft** and **Deutsche Bank**.
* Master of Economics (Capital Markets) & foundational background in Cybernetics.
* Core advocate for modern product engineering: combining commercial awareness with hands-on technical prototyping and asynchronous delivery.
