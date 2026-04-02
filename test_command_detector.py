"""Quick verification that command_detector works correctly."""
from command_detector import is_direct_command

tests = [
    # (input, expected_is_direct_command)
    # Direct commands — should return True
    ("gcc --version", True),
    ("git status", True),
    ("node -v", True),
    ("pip list", True),
    ("python --version", True),
    ("dir", True),
    ("cls", True),
    ("ipconfig", True),
    ("D:", True),
    ("java -version", True),
    ("npm -v", True),
    ("docker ps", True),
    ("curl google.com", True),
    ("echo hello", True),
    ("tasklist", True),
    ("systeminfo", True),
    ("whoami", True),
    ("ping 8.8.8.8", True),
    ("netstat -an", True),
    ("set", True),

    # Natural language — should return False
    ("show me all files", False),
    ("create folder test", False),
    ("check ram usage", False),
    ("where am i", False),
    ("what is my ip", False),
    ("how much memory do i have", False),
    ("tell me the time", False),
    ("delete the folder named old", False),
]

passed = 0
failed = 0
for inp, expected in tests:
    result = is_direct_command(inp)
    status = "PASS" if result == expected else "FAIL"
    if result == expected:
        passed += 1
    else:
        failed += 1
    print(f"  [{status}] '{inp}' -> {result} (expected {expected})")

print(f"\nResults: {passed}/{passed + failed} passed, {failed} failed")
