import pytest
from lib.presets_manager import PresetManagerMixin

class DummyPresetManager(PresetManagerMixin):
    def __init__(self):
        pass
        
def test_validate_preset():
    manager = DummyPresetManager()
    
    valid_preset = {
        "lower_bound": [0, 50, 50],
        "upper_bound": [10, 255, 255],
        "width": 100,
        "height": 100,
        "area": 10000,
        "tolerance": 0.5,
        "min_area": 0.2,
        "max_area": 4.0,
        "proximity": 100.0
    }
    
    assert manager.validate_preset(valid_preset) == True
    
    invalid_preset_missing_key = valid_preset.copy()
    del invalid_preset_missing_key["area"]
    assert manager.validate_preset(invalid_preset_missing_key) == False
    
    invalid_preset_wrong_type = valid_preset.copy()
    invalid_preset_wrong_type["lower_bound"] = "not_a_list"
    assert manager.validate_preset(invalid_preset_wrong_type) == False
    
    invalid_preset_bad_list = valid_preset.copy()
    invalid_preset_bad_list["lower_bound"] = [0, 50] # Only 2 elements
    assert manager.validate_preset(invalid_preset_bad_list) == False
    
    invalid_preset_bad_float = valid_preset.copy()
    invalid_preset_bad_float["tolerance"] = "high"
    assert manager.validate_preset(invalid_preset_bad_float) == False
