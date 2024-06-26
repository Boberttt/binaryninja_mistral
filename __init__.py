from binaryninja import PluginCommand
from binaryninja.settings import Settings

from .reverser_ai.binary_ninja import (plugin_wrapper_rename_all_functions_bg,
                                       plugin_wrapper_rename_function_bg)
PluginCommand.register_for_function(
    "Mistral Summarize Current Function",
    "Summarize current function via mistral's 7b model.",
    plugin_wrapper_rename_function_bg
)


Settings().register_group(
    "mistral_ai",
    "Mistral"
)


Settings().register_setting(
    "mistral_ai.use_mmap",
    '''{
        "description" : "Optimize speed by loading the entire model into memory (requires ~5GB RAM)", 
        "title" : "Use Memory Mapping", 
        "default" : true, 
        "type" : "boolean",
        "requiresRestart": true
    }'''
)

Settings().register_setting(
    "mistral_ai.n_threads",
    '''{
        "description" : "Utilize CPU threads; set to 0 to disable CPU. For full CPU load, set to maximum number of available threads", 
        "title" : "Number of CPU Threads", 
        "default" : 0, 
        "type" : "number",
        "requiresRestart": true
    }'''
)

Settings().register_setting(
    "mistral_ai.n_gpu_layers",
    '''{
        "description" : "Utilize GPU layers for faster processing with a strong GPU", 
        "title" : "Number of GPU Layers", 
        "default" : 99,
        "type" : "number",
        "requiresRestart": true
    }'''
)

Settings().register_setting(
    "mistral_ai.seed",
    '''{
        "description" : "Ensure deterministic model outputs by specifying a seed", 
        "title" : "Seed for Determinism", 
        "default" : 0, 
        "type" : "number",
        "requiresRestart": true
    }'''
)

Settings().register_setting(
    "mistral_ai.verbose",
    '''{
        "description" : "Toggle verbose logging of model configurations", 
        "title" : "Verbose Model Logging", 
        "default" : false, 
        "type" : "boolean",
        "requiresRestart": true
    }'''
)
