# Quick Start: Multi-Agent System

## 🚀 Get Started in 2 Steps

### Step 1: Verify Installation

Install all requirements:

```bash
pip install -r requirements.txt
```

**Note:** The system currently uses a **simplified workflow** that doesn't require LangGraph. If you want to use the full LangGraph implementation in the future, install:

```bash
pip install langgraph==0.0.20
```

### Step 2: Enable Multi-Agent Mode

The multi-agent mode is **enabled by default**. To verify, check `config.py`:

```python
# Multi-Agent Settings
USE_MULTI_AGENT: bool = True  # ✅ Already enabled
```

### Step 3: Run the Generator

```bash
# Start Ollama (if not running)
ollama serve

# Pull the model (if not already pulled)
ollama pull llama3.2

# Run the generator with multi-agent system
python main.py https://www.tivdak.com/patient-stories/
```

That's it! The multi-agent system will automatically:
1. ✅ Analyze DOM with DOM Agent
2. ✅ Classify interactions with Classifier Agent
3. ✅ Generate hover scenarios with Hover Agent
4. ✅ Generate popup scenarios with Popup Agent
5. ✅ Format with Gherkin Agent
6. ✅ Validate with Validator Agent

---

## 📊 Compare Single vs Multi-Agent

Want to see the difference? Run the comparison script:

```bash
python compare_agents.py https://www.tivdak.com/patient-stories/
```

This will run **both** approaches on the same URL and show you:
- Number of scenarios generated
- Time taken
- Quality metrics
- Sample outputs

---

## 🎯 Expected Output

When you run with multi-agent mode, you'll see logs like:

```
🤖 Generating test scenarios with Multi-Agent AI Workflow...
🚀 Starting Multi-Agent Workflow...
🔬 [Workflow] DOM Analysis Agent...
[DOM_Analysis_Agent] Analyzing 12 interactions...
[DOM_Analysis_Agent] Classified 12 interactions

📊 [Workflow] Classifier Agent...
[Interaction_Classifier_Agent] Classification results:
  - Hover: 7
  - Popup: 2

🖱️  [Workflow] Hover Agent...
[Hover_Agent] Generating scenarios for 7 hover interactions...
[Hover_Agent] ✓ Generated: Verify navigation from menu to What is Tivdak
[Hover_Agent] Generated 7 hover scenarios

🪟 [Workflow] Popup Agent...
[Popup_Agent] Generating scenarios for 2 popup interactions...
[Popup_Agent] ✓ Generated: Verify popup behavior with cancel and continue
[Popup_Agent] Generated 2 popup scenarios

📝 [Workflow] Gherkin Agent...
[Gherkin_Agent] Formatted 9 scenarios

✅ [Workflow] Validator Agent...
[Validator_Agent] Validating 9 scenarios...
[Validator_Agent] 8/9 scenarios passed validation

✅ Workflow complete: 8 validated scenarios

📊 Multi-Agent Statistics:
  - Total Scenarios: 8
  - Hover Scenarios: 6
  - Popup Scenarios: 2
  - Average Confidence: 0.78

✓ Generated 8 scenarios using multi-agent workflow
```

---

## 🔄 Switch Back to Single-Agent

If you want to use the legacy single-agent approach:

1. Edit `config.py`:
```python
USE_MULTI_AGENT: bool = False  # Disable multi-agent
```

2. Run normally:
```bash
python main.py https://www.nike.com
```

---

## 🐛 Troubleshooting

### "Module 'langgraph' not found"

```bash
pip install langgraph==0.0.20
```

### "Ollama not accessible"

```bash
# Start Ollama
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

### "No scenarios generated"

Check the logs to see which agent failed:
- If DOM Agent fails → Check interactions are being captured
- If Hover/Popup Agent fails → Check Ollama is responding
- If Validator Agent rejects all → Check scenario quality

Enable verbose logging:
```bash
python main.py https://www.example.com --verbose
```

---

## 📚 Learn More

- **Full Architecture:** See `MULTI_AGENT_ARCHITECTURE.md`
- **Agent Details:** Check files in `src/ai/agents/`
- **Workflow Logic:** See `src/ai/graph/workflow.py`

---

## 🎉 Benefits You Get

✅ **Better Quality** - Specialized agents produce more accurate scenarios  
✅ **Validation** - Validator agent ensures only quality scenarios pass  
✅ **Modularity** - Easy to debug and extend individual agents  
✅ **Consistency** - Gherkin agent ensures proper formatting  
✅ **Transparency** - See exactly which agent is working at each step  

---

## 💡 Pro Tips

1. **Use verbose mode** to see detailed agent logs:
   ```bash
   python main.py https://www.example.com --verbose
   ```

2. **Compare approaches** before committing to one:
   ```bash
   python compare_agents.py https://www.example.com
   ```

3. **Check validation logs** to understand why scenarios are rejected

4. **Extend the system** by adding new agents (see Architecture doc)

---

## ✅ You're Ready!

The multi-agent system is now active and ready to generate high-quality BDD tests. Just run:

```bash
python main.py <YOUR_URL>
```

Happy testing! 🎉
