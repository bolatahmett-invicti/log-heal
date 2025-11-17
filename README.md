# 🩺 LogHeal - AI-Powered Error Recovery System

**LogHeal** is a multi-agent AI system that analyzes ELK (Elasticsearch) logs and automatically generates code fixes. It features a modern Streamlit web interface for log selection, AI analysis, and visual code change review.

## ✨ Key Features

- **🌐 Modern Web Interface**: Streamlit-based, user-friendly UI
- **🔍 Smart Log Filtering**: Real-time error log retrieval from ELK
- **🧠 RAG-Based Code Analysis**: File and class indexing for large codebases
- **🤖 Multi-Agent AI**: Automated problem solving with 5 specialized agents
- **📊 Code Diff Viewer**: Compare original and fixed code side-by-side
- **🌿 Git Integration**: Automatic branch creation and commit
- **⚡ OpenAI GPT-4o**: Powerful language model for code generation

## 🏗️ Architecture

```
┌─────────────────────┐
│   Streamlit Web UI  │  👤 User Interface
│  - Log list         │     • Log cards
│  - Log selection    │     • Full log content
│  - Code diff viewer │     • 3-tab code view
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────┐
│   ELK Connector     │────▶│  Log Filter      │
│   - Real ELK        │     │  Agent           │
│   - Mock Data       │     │  (Optional)      │
└─────────────────────┘     └────────┬─────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
         ┌─────────────────┐              ┌─────────────────┐
         │ Log Analyzer    │              │ CodebaseProvider│
         │ Agent           │              │ (RAG Indexing)  │
         │ • Parse logs    │              │ • File index    │
         │ • Extract error │              │ • Class index   │
         └────────┬────────┘              └────────┬────────┘
                  │                                 │
                  ▼                                 ▼
         ┌─────────────────┐              ┌─────────────────┐
         │ Error Locator   │◀─────────────│  RAG Search     │
         │ Agent           │              │  • Relevant     │
         │ • Find location │              │    files        │
         │ • Root cause    │              │  • Stack trace  │
         └────────┬────────┘              │    matching     │
                  │                       └─────────────────┘
                  ▼
         ┌─────────────────┐
         │ Solution        │
         │ Architect Agent │
         │ • Design fix    │
         │ • Best practice │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Code Generator  │
         │ Agent           │
         │ • Write code    │
         │ • Apply fix     │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Git Manager     │
         │ Agent           │
         │ • Create branch │
         │ • Commit change │
         └─────────────────┘
```

## 📋 Requirements

- **Python 3.13+**
- **Git** (for branch and commit operations)
- **OpenAI API Key** (for GPT-4o model)
- **Elasticsearch 8.x** (optional - mock data available)


## 🚀 Quick Start

### 1. Installation

```powershell
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Set API Key

```powershell
# Set your OpenAI API key as an environment variable
$env:OPENAI_API_KEY = "sk-proj-..."
```

### 3. Launch the Web Interface

```powershell
streamlit run app.py
```

Your browser will automatically open at `http://localhost:8501`.

## 🖥️ Using the Web Interface

### Step 1: ELK Settings
From the left sidebar:
- Test with **mock data** (sample logs)
- Enter host, port, and user info for **real ELK**
- Set **time range** (30-1440 minutes)

### Step 2: Codebase Settings
- Specify your project path (e.g., `C:\Projects\MyApp`)
- RAG will automatically index your codebase

### Step 3: Fetch Logs
- Click **"🔄 Refresh Logs"** or **"🚀 Fetch Logs and Start"**
- Logs will be listed as cards on the left

### Step 4: Log Analysis
- Select a log card
- View detailed JSON with **"📄 Full Log Content"**
- Click **"🔧 Analyze"**
- AI agents will process (15-60 seconds)

### Step 5: Review Results
- **Analysis Results**: Branch name, changed files
- **Code Changes**: 3-tab view
  - 🔍 **Diff**: Changes in diff format
  - 📝 **Original**: Old code
  - ✅ **Fixed**: New code

## 💻 Command Line Usage (Legacy)

CLI is still supported:

```powershell
# Test with mock data
python cli.py --mock

# Use with real ELK
python cli.py --elk-host localhost --elk-port 9200 --time-range 120

# Custom repository
python cli.py --mock --repo-path C:\path\to\your\project
```

## 📊 Example Output

```
================================================================================
🤖 Multi-Agent Log Fix System Started
================================================================================

[2025-11-17 10:30:45] [LogAnalyzer] Analyzing ELK logs...
    - Suggests architecture patterns

## 🔄 Agent Workflow Details

### 1️⃣ Log Filter Agent (Optional)
- Filters specific error types
- Extracts relevant errors
- Reduces noise

### 2️⃣ Log Analyzer Agent
- Parses ELK logs
- Extracts error type and message
- Analyzes stack trace
- Determines severity level
- Collects timestamp and service info

### 3️⃣ Error Locator Agent (RAG Supported)
- Uses **CodebaseProvider** for file/class index
- Finds relevant files from stack trace
- Pinpoints error location
- Performs root cause analysis
- Collects relevant code snippets

### 4️⃣ Solution Architect Agent
- Deeply analyzes the error
- Designs solutions following best practices
- Lists files to be changed
- Suggests architecture patterns
- Defines test strategies

### 5️⃣ Code Generator Agent
- Implements the solution in code
- Preserves existing code style
- Validates syntax
- Generates fixes for each file
- Reports code changes to the UI via callback

### 6️⃣ Git Manager Agent
- Creates unique branch (`fix/error-type-timestamp`)
- Writes changes to files
- Skips folders like `.venv`, `node_modules`
- Commits automatically
- Prepares detailed commit messages
- Prevents empty commits

## 🛠️ Development

### Adding a New Agent

```python
from orchestrator import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__('MyCustomAgent')
    
    async def my_task(self, input_data):
        prompt = f'My custom prompt: {input_data}'
        response = await self.call_claude(prompt)
        return response
```

### Using the Config File

```python
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

from orchestrator import CodebaseProvider
agent_config = config['agents']['log_analyzer']
```

## 📝 Best Practices

1. **Start in Test Mode**: Use `--mock` for your first run
2. **Small Time Range**: Start with 15-30 minutes
3. **Manual Review**: Always review the created branch
4. **Run Tests**: Check tests before auto-pushing
5. **Expand Slowly**: Increase automation as you gain trust

## 🔒 Security

- Store API keys in environment variables
- Do not write ELK passwords in config files
- Auto-push is disabled by default
- All changes require review

## 🐛 Troubleshooting

### "Elasticsearch connection error"
```powershell
# Check if ELK service is running
curl http://localhost:9200

# Check firewall rules
# Verify ELK host/port settings
```

### "OpenAI API error"
```powershell
# Check if API key is set correctly
echo $env:OPENAI_API_KEY

# Set again
$env:OPENAI_API_KEY = "sk-proj-..."
```

### "Git commit error"
```powershell
# Set git user info
cd C:\path\to\your\project
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### "Logs not listed"
- Restart Streamlit (Ctrl+C, then `streamlit run app.py`)
- Clear browser cache (Ctrl+F5)
- Enable "Always rerun" option

### ".venv files being fixed"
- This is resolved! Only project files are processed now
- The `excluded_dirs` list excludes virtual environments

## 📈 Roadmap

### v1.1 (Current)
- ✅ Streamlit web interface
- ✅ RAG-based code analysis
- ✅ OpenAI GPT-4o integration
- ✅ Code diff viewer
- ✅ Virtual environment filtering

### v1.2 (Planned)
- [ ] **Bulk operations**: Select and analyze multiple logs
- [ ] **Log history**: Analysis history and suggestion replay
- [ ] **Code review**: AI-assisted code review
- [ ] **Undo/Rollback**: Branch deletion and revert

### v2.0 (Future)
- [ ] **GitHub/GitLab integration**: Automatic PR creation
- [ ] **Slack/Teams notifications**: Real-time alerts
- [ ] **Test generation**: Automatic unit test writing
- [ ] **Multi-repository**: Microservice support
- [ ] **CI/CD pipeline**: Jenkins/GitHub Actions integration
- [ ] **Metrics dashboard**: Fix success rates, trend analysis

## 🧪 Testing & Development

### Adding a New Agent

```python
from orchestrator import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__('MyCustomAgent')
    
    async def analyze(self, input_data: str) -> dict:
        prompt = f'Analyze this: {input_data}'
        response = await self.call_openai(prompt)
        return json.loads(response)
```

### RAG Index Check

```python
from orchestrator import CodebaseProvider

provider = CodebaseProvider('C:\\path\\to\\project')
print(f'Files indexed: {len(provider.file_index)}')
print(f'Classes indexed: {len(provider.class_index)}')
print(provider.class_index.get('UserController'))
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License

## 🌟 Features & Technologies

| Technology         | Usage              |
|--------------------|--------------------|
| **Python 3.13**    | Core language      |
| **Streamlit**      | Web UI framework   |
| **OpenAI GPT-4o**  | AI code generation |
| **Elasticsearch**  | Log ingestion      |
| **asyncio**        | Async operations   |
| **aiohttp**        | HTTP client        |
| **Git**            | Version control    |

## ⚠️ Important Notes

> **🔴 Production Warning**: This system generates code automatically with AI. All generated code **must be reviewed** and **tested**. Do **not** push directly to production!

> **💡 Tip**: Start with **mock data** to test and learn the system, then switch to real ELK.

> **🔒 Security**: Never store API keys in code, always use environment variables.

---

**Heal your error logs automatically with LogHeal!** 🩺✨

provider = CodebaseProvider("C:\\path\\to\\project")
print(f"Files indexed: {len(provider.file_index)}")
print(f"Classes indexed: {len(provider.class_index)}")
print(provider.class_index.get("UserController"))
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License

## 🌟 Features & Technologies

| Technology         | Usage              |
|--------------------|--------------------|
| **Python 3.13**    | Core language      |
| **Streamlit**      | Web UI framework   |
| **OpenAI GPT-4o**  | AI code generation |
| **Elasticsearch**  | Log ingestion      |
| **asyncio**        | Async operations   |
| **aiohttp**        | HTTP client        |
| **Git**            | Version control    |

## ⚠️ Important Notes

> **🔴 Production Warning**: This system generates code automatically with AI. All generated code **must be reviewed** and **tested**. Do **not** push directly to production!

> **💡 Tip**: Start with **mock data** to test and learn the system, then switch to real ELK.

> **🔒 Security**: Never store API keys in code, always use environment variables.

---

**Heal your error logs automatically with LogHeal!** 🩺✨
