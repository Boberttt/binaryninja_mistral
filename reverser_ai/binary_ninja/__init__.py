from binaryninja.plugin import BackgroundTaskThread
from .function_name_gpt_wrapper import FunctionNameGPTWrapper
from .utils import is_derived_func_name


class BinjaFunctionNameGPTManager:
    """
    Manages a single instance of FunctionNameGPTWrapper to ensure it is initialized only once across multiple
    uses in the Binary Ninja plugin.

    This class implements the singleton design pattern to manage the unique and static initialization
    of FunctionNameGPTWrapper, which facilitates the application of GPT-based function naming suggestions
    within the Binary Ninja analysis environment.

    Attributes:
        _binja_function_name_gpt (FunctionNameGPTWrapper or None): A singleton instance of FunctionNameGPTWrapper.
    """

    def __init__(self):
        """
        Initializes the manager with a specified configuration path.
        """
        self._binja_function_name_gpt = None

    def get_instance(self):
        """
        Retrieves the singleton instance of FunctionNameGPTWrapper.

        If the instance has not been initialized, it initializes it.

        Returns:
            FunctionNameGPTWrapper: The initialized singleton instance of the wrapper.
        """
        if self._binja_function_name_gpt is None:
            self._binja_function_name_gpt = FunctionNameGPTWrapper()
        return self._binja_function_name_gpt


# Initialize the manager as a global variable to be reused across plugin functions
manager = BinjaFunctionNameGPTManager()


def plugin_wrapper_rename_function(_, f):
    """
    Queries FunctionNameGPTWrapper for a function name suggestion and applies it to a single function.

    This function is intended to be used as a callback or a hook within the Binary Ninja UI
    to rename a specific function.

    Args:
        _ : Ignored. Placeholder for the unused binary view.
        f (binaryninja.function.Function): The Binary Ninja function object to rename.
    """
    # Retrieve the singleton instance of the GPT manager
    gpt = manager.get_instance()

    # Apply the GPT-based name suggestion to the function
    gpt.apply_suggestion(f)


def plugin_wrapper_rename_all_functions(bv):
    """
    Iterates over all functions in a Binary Ninja binary view, querying a GPT-based model for name suggestions,
    and applies those suggestions to each function.

    This function implements a worklist algorithm to ensure that functions are renamed in an order that respects
    their call dependencies. Specifically, it aims to rename "leaf" functions (those that do not call other functions)
    before renaming functions that call them. This approach facilitates the propagation of contextual information
    and learned insights across function names, potentially leading to more accurate and context-aware renaming.

    Due to the reliance on a GPT-based model for suggestions and the iterative nature of the algorithm, this operation
    can be slow, especially for binaries with a large number of functions.

    Args:
        bv (binaryninja.BinaryView): The binary view containing the functions to be renamed.
    """
    # Retrieve the singleton instance of the GPT manager for name suggestions
    gpt = manager.get_instance()

    # Initialize sets and lists for tracking processed and pending functions
    # A set to keep track of functions that have been processed
    done = set()
    # A worklist of functions pending processing
    todo = []

    # Initial population of the worklist with all functions in the binary view
    # This loop also avoids re-adding functions that have already been processed
    for f in bv.functions:
        if f not in done:
            todo.append(f)

    # Process functions in the worklist, respecting call dependencies
    while len(todo) != 0:
        # Retrieve the last function added to the worklist
        current = todo.pop()

        # Skip already processed functions
        if current in done:
            continue

        # Check if all callees of the current function have been processed
        if all(callee in done for callee in current.callees):
            # Apply the GPT-based name suggestion to the function if its actual name is not derived
            if not is_derived_func_name(current.name):
                gpt.apply_suggestion(current)
            # Mark the current function as processed
            done.add(current)

        # Re-add the current function to the worklist to ensure it's reconsidered after its callees are processed
        todo.append(current)

        # Add unprocessed callees to the worklist for processing
        for callee in current.callees:
            if callee not in done:
                todo.append(callee)


class BGTask(BackgroundTaskThread):
    """
    Executes a provided function as a background task within the Binary Ninja environment.

    This class allows plugin commands to execute without blocking the main UI thread,
    enhancing responsiveness when performing potentially long-running operations.

    Attributes:
        bv (binaryninja.BinaryView): The binary view context for the operation.
        msg (str): A message describing the background task's purpose.
        f (function): The function to be executed in the background.
    """

    def __init__(self, bv, msg, f):
        super().__init__(msg, True)
        self.f = f
        self.bv = bv

    def run(self):
        """
        Executes the stored function with the provided binary view.
        """
        self.f(self.bv)


class BGTaskFunction(BackgroundTaskThread):
    """
    Specialized version of BGTask for executing functions that require an additional argument.

    Intended for use with Binary Ninja's PluginCommand.register_for_function, this class
    supports operations that act on specific items, like individual functions, within the binary.

    Attributes:
        bv (binaryninja.BinaryView): The binary view context for the operation.
        msg (str): A message describing the background task's purpose.
        f (function): The function to be executed in the background.
        arg (any): An additional argument to be passed to the function, typically a function object.
    """

    def __init__(self, bv, msg, f, arg):
        super().__init__(msg, True)
        self.f = f
        self.bv = bv
        self.arg = arg

    def run(self):
        """
        Executes the stored function with the provided binary view and additional argument.
        """
        self.f(self.bv, self.arg)


def plugin_wrapper_rename_all_functions_bg(bv):
    """
    Initiates a background task to rename all functions in the binary.

    This function leverages a GPT-based naming model to suggest and apply new names
    to every function in the provided binary view, improving the clarity of disassembled code.

    Args:
        bv (binaryninja.BinaryView): The binary view containing the functions to be renamed.
    """
    background_task = BGTask(
        bv,
        "Renaming all functions in the binary based on GPT suggestions.",
        plugin_wrapper_rename_all_functions
    )
    background_task.start()


def plugin_wrapper_rename_function_bg(bv, f):
    """
    Initiates a background task to rename a single function using a GPT-based suggestion.

    This function queries a GPT model for a suggested name for the specified function
    and applies the suggestion, aiding in the understanding and analysis of binary code.

    Args:
        bv (binaryninja.BinaryView): The binary view where the function is located.
        f (binaryninja.Function): The function object to be renamed.
    """
    background_task = BGTaskFunction(
        bv,
        "Querying GPT for a function summary",
        plugin_wrapper_rename_function,
        f
    )
    background_task.start()
