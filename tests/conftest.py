def pytest_addoption(parser):
    parser.addoption("--tests.examples.nginx-source", required = False, action = "append", help = "OCI image path")
