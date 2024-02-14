import json
from helperfunctions import setup_logger

logger = setup_logger()

class AutoSaveDict(dict):
    def __init__(self, *args, **kwargs):
        self.file_path = kwargs.pop('file_path', 'data.json')
        super().__init__(*args, **kwargs)
        self._save_to_file()
        logger.info(f"Initialized AutoSaveDict with file path: {self.file_path}")
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._save_to_file()
        logger.info(f"Set item: {key} = {value}")
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self._save_to_file()
        logger.info(f"Deleted item: {key}")
    
    def update(self, *args, **kwards):
        super().update(*args, **kwargs)
        self._save_to_file()
        logger.info(f"Updated dictionary with new items")
    
    def _save_to_file(self):
        with open(self.file_path, 'w') as file:
            json.dump(self, file, indent=4)
        logger.info(f"Saved dictionary to file: {self.file_path}")