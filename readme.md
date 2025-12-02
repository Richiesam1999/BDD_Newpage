BDD Test Generator 🤖
An AI-powered tool that automatically generates Gherkin BDD test scenarios for websites with hover and popup interactions.
🎯 Features

Dynamic Element Detection: Automatically finds hoverable elements and popup triggers without hardcoded selectors
AI-Powered Scenario Generation: Uses Ollama (local LLM) to create human-readable Gherkin scenarios
Zero Configuration: Works on any modern website out of the box
Smart Caching: Caches analysis results to speed up repeat runs
Natural Language: Generates tests using natural descriptions, not technical selectors

🏗️ Architecture
User Input (URL)
    ↓
Browser Automation (Playwright)
    ↓
Element Detection (CSS, ARIA, JS analysis)
    ↓
Interaction Simulation
    ↓
AI Analysis (Ollama + LangGraph)
    ↓
Gherkin Generation
    ↓
.feature Files


📋 Prerequisites
System Requirements

Python 3.9+
8GB RAM minimum (for running Ollama)
Ollama installed and running

Install Ollama
macOS/Linux:
bashcurl -fsSL https://ollama.com/install.sh | sh
Windows:
Download from https://ollama.com/download
Start Ollama:
bashollama serve
Pull the AI model:
bashollama pull llama3.1
# or
ollama pull mistral
🚀 Quick Start
1. Clone the Repository
bashgit clone https://github.com/Richiesam1999/BDD_Newpage/tree/master
cd bdd-test-generator
2. Create Virtual Environment
bashpython -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
3. Install Dependencies
bashpip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
4. Verify Ollama is Running
bash# Check Ollama status
curl http://localhost:11434/api/tags

# Should return JSON with available models
5. Run the Generator
bash# Basic usage
python main.py https://www.tivdak.com/patient-stories/

# With options
python main.py https://www.nike.com --output nike_tests --verbose

# Show browser window (for debugging)
python main.py https://www.apple.com --show-browser


📖 Usage Examples
Example : Generate Tests for Tivdak Website
bashpython main.py https://www.tivdak.com/patient-stories/