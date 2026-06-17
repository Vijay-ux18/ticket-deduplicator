# DedupeAI — Smart Support Ticket Deduplicator (PS-08)

DedupeAI is an enterprise-grade operational prototype engineered to eliminate system alert fatigue for IT Production Support teams. The application implements a high-performance 4-stage pipeline that automatically ingest support incidents, executes a localized vector similarity search against historical ticket records, and runs a structured AI verification gate to detect, link, and flag duplicate tickets.

## 👥 Team Information
* **Name:** [S.Vijay Bhaskar Reddy]


## 🛠️ Tools & Technologies Used
* **Operating System Platform:** Ubuntu 26.04 LTS (Fully Tested & Validated)
* **Programming Environment:** Python 3.10+ (Isolated Virtual Environment)
* **Frontend Web Framework:** Streamlit (>= 1.35.0)
* **Data Processing Layer:** Pandas (>= 3.0.0)
* **Vector Mathematics & Machine Learning Engine:** Scikit-Learn (>= 1.5.0)
* **Core Relational Storage:** SQLite Engine (Serverless Local Database File)
* **AI Model Capability Provider:** Google Gemini API (Free Tier `gemini-1.5-flash`)
* **Automated Testing Suite:** Pytest (>= 8.2.2)

## 🏗️ Architecture Overview
DedupeAI is structured sequentially across the four core stages defined by the hackathon criteria:
1. **Input Stage:** Accepts raw text blocks through a custom single-page Streamlit text area, or via quick-inject preset buttons simulating production incident states.
2. **Processing Stage:** Programmatically reads a serverless local SQLite instance containing 15 high-fidelity historical support records. It converts string arrays into TF-IDF vector matrices via Scikit-Learn and computes exact Cosine Similarity weights.
3. **AI Layer:** Packages the input ticket alongside the top 3 highest-ranking database rows into a deterministic system prompt template, forcing a valid, structured JSON output block from the Gemini API.
4. **Output Stage:** Renders an interactive triage status board directly on screen, updates metrics, logs metadata files to local disk paths, and generates a downloadable Markdown triage report.

## 💻 Environment Setup & Run Instructions
Execute these commands sequentially on your Ubuntu 26.04 terminal to launch the prototype:

```bash
# 1. Clone or navigate directly to the root project directory workspace
cd ticket-deduplicator

# 2. Instantiate an isolated virtual environment shell
python3 -m venv venv
source venv/bin/activate

# 3. Securely upgrade tool installers and deploy pinned cutting-edge requirements
pip install --upgrade pip
pip install -r requirements.txt

# 4. (Optional) Inject your Gemini Free Tier authorization credentials
export GEMINI_API_KEY="your_actual_free_tier_api_key_here"

# 5. Launch the automated happy-path unit test engine
pytest tests/test_basic.py -v

# 6. Fire up the local Streamlit application server instance
streamlit run app.py
