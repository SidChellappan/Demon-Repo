Output docs/demo.gif

Set FontSize 20
Set Width 960
Set Height 540

Type "reviewit --model ollama --style concise"
Enter
Sleep 500ms
Type "reviewit is reviewing your diff"
Enter
Type "provider: ollama | model: llama3.1 | style: concise"
Enter
Sleep 500ms
Type "## Summary"
Enter
Type "The change is close, but one error path can ship a broken response."
Enter
Sleep 500ms
Type "## 🔴 Critical (must fix before merging)"
Enter
Type "- [api.py:42] The exception handler returns 200 instead of 500."
Enter
Type "## 🟡 Suggestions (nice to have)"
Enter
Type "- [tests/test_api.py:12] Add coverage for the failure path."
Enter
