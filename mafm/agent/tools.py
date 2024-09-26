from typing import Annotated
from langchain_core.tools import Tool


def print_abc_tool(*args, **kwargs):
    """
    Tool that prints 'ABC'.
    """
    print("ABC")
    return "Printed: ABC"


# Step 2: Create the tool
print_abc = Tool(
    name="PrintABC",
    func=print_abc_tool,  # The function to call
    description="This tool simply prints 'ABC'.",
)
