┌─────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                         │
│                          (main.py)                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Browser Automation Layer                     │
│              (Playwright - automation.py)                       │
│  • Navigate to URL                                              │
│  • Execute JavaScript                                           │
│  • Capture screenshots                                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Element Detection Layer                      │
│                  (element_detector.py)                          │
│  • Find hoverable elements (CSS, ARIA, JS analysis)            │
│  • Detect popup triggers                                        │
│  • Simulate interactions                                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Analysis Layer                             │
│        (dom_analyzer.py + interaction_mapper.py)               │
│  • Parse HTML structure                                         │
│  • Map interactions to outcomes                                 │
│  • Extract semantic information                                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AI Layer                                 │
│         (Ollama + agent_orchestrator.py)                       │
│  • Understand interactions contextually                         │
│  • Generate natural language descriptions                       │
│  • Create test scenarios                                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Gherkin Generation Layer                      │
│                  (gherkin_generator.py)                         │
│  • Format scenarios as Gherkin                                  │
│  • Validate syntax                                              │
│  • Save .feature files                                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Output & Cache Layer                         │
│              (storage.py + file system)                         │
│  • Save .feature files                                          │
│  • Cache results (SQLite)                                       │
└─────────────────────────────────────────────────────────────────┘