import os
import importlib.util
import inspect
import time
from plugin_interface import Plugin

PLUGIN_DIR = "plugins"

class PluginManager:
    def __init__(self):
        self.plugins = []
        self._file_cache = {}  # filename -> mtime
        self.scan_and_load()

    def scan_and_load(self):
        """
        Scans the plugin directory and reloads modified or new plugins.
        Returns:
            bool: True if changes were detected and loaded, False otherwise.
        """
        if not os.path.exists(PLUGIN_DIR):
            os.makedirs(PLUGIN_DIR)
            return False

        changes_detected = False
        current_files = set()

        for file in os.listdir(PLUGIN_DIR):
            if file.endswith(".py") and not file.startswith("__"):
                path = os.path.join(PLUGIN_DIR, file)
                current_files.add(file)
                
                try:
                    mtime = os.path.getmtime(path)
                    
                    # Check if file is new or modified
                    if file not in self._file_cache or self._file_cache[file] < mtime:
                        print(f"DEBUG: Loading/Reloading plugin: {file}")
                        self._load_plugin(file, path)
                        self._file_cache[file] = mtime
                        changes_detected = True
                        
                except Exception as e:
                    print(f"Error checking plugin {file}: {e}")

        # Remove deleted plugins (simplistic approach: just remove from cache, 
        # actual instance removal is harder without valid ID, but for now we re-scan)
        # For a robust system, we might want to clear self.plugins and re-populate 
        # but that clears state. Let's append new ones and replace old ones if possible.
        # simpler: if changes detected, just clear and reload all to be safe?
        # NO, that kills state.
        # Let's start with additive loading for now, or full reload if simple.
        
        # FULL RELOAD STRATEGY for robust dynamic behavior (easiest for now)
        if changes_detected:
            # Re-build plugin list from loaded modules
            # This is a bit tricky with distinct instances. 
            # ideally we only replace the specific instance.
            pass
            
        return changes_detected

    def _load_plugin(self, filename, path):
        module_name = filename[:-3]
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find subclasses of Plugin
                found_any = False
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) 
                        and issubclass(obj, Plugin) 
                        and obj is not Plugin):
                        
                        try:
                            # Check if we already have this plugin class (by name)
                            # If so, replace it?
                            instance = obj()
                            
                            # Remove old instance of same class name if exists
                            self.plugins = [p for p in self.plugins if p.name != instance.name]
                            
                            self.plugins.append(instance)
                            found_any = True
                            print(f"Successfully loaded plugin: {instance.name}")
                        except Exception as e:
                            print(f"Error instantiating plugin {name}: {e}")
                            
                if not found_any:
                    print(f"Warning: No Plugin subclass found in {filename}")

        except Exception as e:
            print(f"Failed to load plugin {filename}: {e}")

    def get_plugins(self):
        return self.plugins

    def reload_if_needed(self):
        self.scan_and_load()

# Global instance for backward compatibility or easy access
# But main.py should instantiate it.
def load_plugins():
    # Backward compatibility wrapper
    pm = PluginManager()
    return pm.get_plugins()

