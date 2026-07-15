from testloop.runner import run_tests

src = "x = 1\n"
evil = """import target, socket
def test_network():
    socket.create_connection(("1.1.1.1", 53), timeout=5)
"""

r = run_tests(src, evil, use_docker=True, timeout=30)
print("network test passed?", r.passed > 0)
print(r.output[-500:])