# VeriResume AI: Advanced AI-Powered Fake Resume Analyser and Detection System

A full-stack, enterprise-grade AI system developed as an advanced college capstone project. VeriResume AI analyzes candidate resumes (PDF and DOCX), extracts biographical and professional entities, evaluates timeline consistency using deterministic rule heuristics, applies a machine learning classification engine (TF-IDF + Logistic Regression) with feature-level explainability, and generates actionable credibility reports and interview verification checklists.

---

## Key Highlights & Core Features

- **Modern Recruiter Dashboard with Interactive Charts**: Built with Chart.js, featuring real-time risk distribution doughnut charts, review pipeline tracking, candidate volume metrics, and instant action feeds.
- **Drag-and-Drop & Batch Upload**: Multi-file drag-and-drop dropzone supporting PDF (`.pdf`) and Microsoft Word (`.docx`), multi-resume batch processing, and direct raw text analysis.
- **Deep Entity & Timeline Extraction**: Automatically parses candidate names, contact details, LinkedIn/GitHub profiles, categorized technical skills, degree sequences, and career tenures using PyMuPDF and python-docx.
- **Deterministic Rule Engine (55% Weight)**:
  - **Chronological Inversion**: Flags positions where tenure end date precedes start date (e.g. 2025–2021).
  - **Future Date Anomalies**: Identifies employment or graduation dates set in future calendar cycles.
  - **Degree Sequence Mismatches**: Flags postgraduate degrees completed prior to undergraduate degrees.
  - **Overlapping Tenures**: Detects multiple simultaneous full-time positions spanning concurrent years.
  - **Keyword Stuffing & SEO Spam**: Detects ATS-gaming where technical buzzwords constitute an abnormal percentage of total resume text.
  - **Duplicate Content**: Identifies verbatim copy-paste sentence and bullet point repetitions.
  - **Premature Executive Titles**: Flags executive roles (CTO, VP of Engineering) held with minimal career tenure.
  - **Extreme Metric Claims**: Detects inflated claims (e.g., "Led team of 1,500 engineers at age 21", "managed $500M budget as intern").
  - **Technology Anachronisms**: Flags claimed experience exceeding the existence of the technology (e.g., "15 years experience in Kubernetes" when Kubernetes was created in 2014).
- **Machine Learning Detection (45% Weight)**:
  - Sublinear TF-IDF n-gram vectorizer (unigrams and bigrams, 1,500 features).
  - Calibrated Logistic Regression model with continuous probability output.
  - **Feature-Level Explainability**: Attributions reveal exact n-grams and vocabulary that pushed scores toward Suspicious or Genuine.
- **Hybrid Scoring & Explainability**:
  - Transparent formula: `Risk Score = (0.55 * Rule Penalty) + (0.45 * ML Probability)`.
  - Credibility Index: `100 - Risk Score`.
  - Triage Categorization:
    - **Low Risk (0–35)**: Credible, standard recruitment progression.
    - **Moderate Review (36–69)**: Minor inconsistencies; targeted verification recommended.
    - **High Suspicion (70–100)**: Major date conflicts or synthetic text patterns; manual audit required.
- **AI Executive Summaries & Verification Questions**: Generates recruiter briefs and customized interview questions specifically tailored to the detected anomalies.
- **Job Description (JD) Matcher & Skill Gap Analysis**:
  - Analyzes candidate fit against target JDs using TF-IDF cosine similarity and skill taxonomy intersection.
  - Visual display of matched competencies (green pills) and missing skills / skill gap (red pills).
  - Pre-packaged with 4 industry JD templates (Full Stack, Data Science, Cloud DevOps, Product Management).
- **Downloadable PDF Audit Reports**: Generates professional PDF reports via ReportLab containing candidate metadata, risk meters, detected anomaly tables with quoted evidence, and interview checklists.
- **Recruiter Workflow & History**: Search, multi-criteria filtering, audit trail, recruiter notes, status updating (`Pending Review`, `Under Review`, `Verified Credible`, `Confirmed Discrepancies`), and CSV export.
- **Privacy & Security Controls**: One-click **PII Masking** toggle (masks names, emails, phones, and locations for blind reviews), local SQLite storage, safe filename sanitization.
- **Synthetic Demo Resumes & 1-Click "Try Demo"**: 4 pre-built realistic and anomalous resumes ready to test with zero file prep.
- **Automated Test Suite**: 26 comprehensive pytest unit and integration tests covering all parsing, rules, ML inference, JD matching, and Flask routes.

---

## Critical Ethical Guardrail & AI Principles

> **IMPORTANT ETHICAL DIRECTIVE:**
> **An automated score must NEVER be used to declare a resume fake or unilaterally disqualify a candidate.**
>
> VeriResume AI is engineered strictly as a **decision-support triage tool**. In human recruitment, non-standard career trajectories, typographical oversights, international calendar conventions (e.g., DD/MM vs MM/DD), and genuine freelance moonlighting can trigger flags. 
> 
> Automated risk scores serve to prioritize manual background checks and suggest specific clarifying questions for human recruiters during phone screenings. The system also includes an anonymous PII masking switch to mitigate unconscious human bias.

---

## System Architecture

```
[Resume File: PDF / DOCX] ───> [PyMuPDF / python-docx Text Extractor]
                                           │
                                           ▼
                                [Entity & Timeline Extractor]
                                (Name, Contact, Education, Roles, Skills)
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       [Deterministic Rule Engine]                    [Machine Learning Engine]
        - Chronological Inversion                      - TF-IDF N-Grams (1-2)
        - Future Dates / Distant Dates                 - Logistic Regression Classifier
        - Degree Sequence Order                        - Feature Attribution Weights
        - Buzzword Stuffing Density                    - Anomaly Probability (0-100%)
        - Verbatim Duplicate Bullets
        - Premature Executive Titles
        - Extreme Metric Claims
        - Technology Anachronisms
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                             [Hybrid Risk Analyzer]
                   Composite Score = 0.55 * Rule + 0.45 * ML
                   Credibility Index = 100 - Composite Score
                   Triage: Low Risk | Moderate | High Suspicion
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       [AI Explainer & Questions]                     [Job Description Matcher]
        - Executive Summary Narrative                  - TF-IDF Cosine Similarity
        - Tailored Verification Questions              - Skill Set Intersection
                                                       - Missing Skill Gap Analysis
                                           │
                                           ▼
                             [Storage & Presentation]
        - SQLite Database (resumes, audits, jd_evaluations)
        - Modern Responsive Web UI (Bootstrap 5, Chart.js)
        - ReportLab PDF Audit Report Generator & CSV Export
```

---

## Directory Structure

```
FakeResumeDetection/
├── app.py                      # Flask web application & REST APIs
├── config.py                   # Central configuration & risk thresholds
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation & setup guide
├── core/
│   ├── __init__.py
│   ├── parser.py               # PyMuPDF & docx text/entity extraction & skill taxonomy
│   ├── rule_engine.py          # Deterministic rule checks (dates, buzzwords, claims)
│   ├── ml_engine.py            # TF-IDF + Logistic Regression inference & feature explainability
│   ├── hybrid_analyzer.py      # Weighted composite scoring & triage categorization
│   ├── ai_explainer.py         # AI executive summary & verification questions generator
│   ├── jd_matcher.py           # Job Description matching & skill-gap analyzer
│   ├── report_generator.py     # ReportLab professional PDF audit report generator
│   └── database.py             # SQLite schema, queries, status tracking & audit log
├── data/
│   ├── training_data.py        # Curated synthetic training dataset with labeled personas
│   └── resumes.db              # SQLite database (auto-created on first run)
├── models/
│   ├── train_model.py          # Script to train and persist the ML model
│   ├── tfidf_vectorizer.pkl    # Serialized Scikit-learn TF-IDF vectorizer
│   └── resume_classifier.pkl   # Serialized Scikit-learn Logistic Regression classifier
├── demo_resumes/
│   ├── create_demo_files.py    # Generator script for demo benchmark files
│   ├── alex_morgan_genuine_fullstack.pdf   # Demo 1: Verified authentic profile
│   ├── david_chen_date_anomalies.pdf       # Demo 2: Inverted dates & degree anomalies
│   ├── sarah_connor_buzzword_stuffed.docx  # Demo 3: Buzzword stuffing & duplicates
│   └── jordan_taylor_junior_inflated.pdf   # Demo 4: Junior claiming CTO title
├── static/
│   ├── css/
│   │   └── style.css           # Modern recruiter UI styling & dark/light accents
│   └── js/
│       └── app.js              # Drag-and-drop, batch upload, & progress animation
├── templates/
│   ├── base.html               # Base layout with navbar & ethical guardrail banner
│   ├── dashboard.html          # Recruiter dashboard with metrics & Chart.js charts
│   ├── scan.html               # Upload dropzone, text paste & demo selector
│   ├── analysis_result.html    # Profile audit, timeline, explainability & JD match
│   ├── history.html            # Searchable & filterable history table with CSV export
│   ├── jd_matching.html        # Dedicated JD matcher with presets
│   └── about.html              # College project viva documentation & methodology
├── tests/
│   ├── __init__.py
│   ├── test_parser.py          # Unit tests for text & entity extraction
│   ├── test_rules.py           # Unit tests for 8 deterministic rules
│   ├── test_ml_model.py        # Unit tests for ML inference & hybrid scoring
│   ├── test_jd_matcher.py      # Unit tests for skill gap & cosine similarity
│   └── test_app.py             # Integration tests for Flask routes & exports
└── uploads/                    # Secure local storage for uploaded resumes
```

---

## Windows Setup & Installation Instructions

Follow these step-by-step instructions in Windows PowerShell or Command Prompt.

### 1. Prerequisites
- Python 3.10+ (Tested and verified on **Python 3.14.0**).
- Git (optional).

### 2. Open Command Prompt / PowerShell in Project Directory
```powershell
cd c:\Users\hp\OneDrive\Desktop\FakeResumeDetection
```

### 3. (Optional) Create and Activate a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If you encounter execution policy restrictions in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Generate Demo Resumes & Train Model (Pre-run step)
The project comes with automated generators:
```powershell
# Generate the 4 synthetic demo resumes (PDF and DOCX)
python demo_resumes/create_demo_files.py

# Train and serialize the TF-IDF and Logistic Regression models
python models/train_model.py
```

### 6. Run the Automated Test Suite
Verify that all 26 tests pass:
```powershell
python -m pytest tests/
```

### 7. Launch the Web Application
```powershell
python app.py
```

### 8. Access the System
Open your web browser and navigate to:
**`http://127.0.0.1:5000`**

---

## How to Test the System in 30 Seconds

1. On the Dashboard (`http://127.0.0.1:5000`), look at the top navigation bar or the **"Quick 1-Click Synthetic Demo Scenarios"** box.
2. Click **"Test Genuine Profile" (Alex Morgan)**:
   - Observe a clean timeline, 0 rule flags, low ML anomaly score, and an overall **Low Risk** badge.
3. Click **"Test Date Anomalies" (David Chen)**:
   - Notice the high-severity flags: *Chronological Inversion in Work Tenure*, *Employment Starts in the Future*, and *Master Degree Completed Before Bachelor Degree*.
   - View the red visual timeline warnings and customized interview verification questions.
4. Click **"Test Buzzword Stuffing" (Sarah Connor)**:
   - Notice *Excessive Buzzword Stuffing*, *Repeated Bullet Points*, and *Unverifiable Metric Claim* ("Invented Kubernetes").
5. Click **"Test Inflated Seniority" (Jordan Taylor)**:
   - Notice *Executive Title with Minimal Career History* (claiming CTO as a 2023 graduate leading 1,500 engineers).
6. Click **"Export PDF Audit"** on any candidate profile to download a formal ReportLab PDF audit document.
7. Click the **"Mask PII (Anonymous Review)"** toggle switch on the candidate audit page to immediately mask personal data for unbiased technical screening.
8. Test the **Job Description Matcher**: Select a candidate, choose a preset (e.g. "Full Stack Software Engineer"), and observe matched skills (green pills) versus skill gaps (red pills).

---

## College Project Viva & Evaluation Questions

### Q1: Why use a hybrid approach (Rules + ML) instead of ML alone?
**Answer:** Machine learning models (like TF-IDF + Logistic Regression) are statistical pattern matchers. They excel at recognizing broad linguistic tone, keyword repetition, and synthetic phrasing, but they cannot perform strict arithmetic checks (such as verifying if `2025 > 2021` or checking if a Master's degree year occurred before a Bachelor's degree year). Combining deterministic symbolic rules (55% weight) with ML classification (45% weight) gives 100% precision on mathematical anomalies while maintaining statistical adaptability for textual anomalies.

### Q2: Why Logistic Regression over a Deep Neural Network?
**Answer:** In recruitment compliance (EEOC, GDPR), **model explainability is a legal and ethical requirement**. Deep neural networks operate as black boxes. Logistic Regression with TF-IDF provides exact mathematical transparency: each token's contribution weight ($\beta_i \cdot x_i$) can be computed directly, showing recruiters precisely which words influenced the score.

### Q3: How is candidate privacy protected?
**Answer:** All resume files and database entries are stored locally on the server in SQLite without transmitting data to external third-party cloud APIs. The UI includes an instant PII Masking toggle to anonymize names, phone numbers, and addresses to protect privacy and mitigate demographic bias.

---

## License & Academic Disclaimer

Developed for academic demonstration and research purposes. Dataset samples are synthetic and engineered to benchmark automated resume anomaly detection algorithms.
