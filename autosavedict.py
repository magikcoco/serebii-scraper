import json

class AutoSaveDict(dict):
    def __init__(self, *args, **kwargs):
        self.file_path = kwargs.pop('file_path', 'data.json')
        super().__init__(*args, **kwargs)
        self._save_to_file()
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._save_to_file()
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self._save_to_file()
    
    def update(self, *args, **kwards):
        super().update(*args, **kwargs)
        self._save_to_file()
    
    def _save_to_file(self):
        with open(self.file_path, 'w') as file:
            json.dump(self, file, indent=4)