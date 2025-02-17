import os
from insurgent import build, load_config
from insurgent.logger import error

def test_example():
    os.chdir("../example")
    assert build("example", load_config("project.yaml")) is not None

test_example()