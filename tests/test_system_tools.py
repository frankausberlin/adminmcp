import pytest
from unittest.mock import patch, MagicMock
from adminmcp.tools.system import get_system_info, list_processes

def test_get_system_info():
    with patch('platform.system', return_value='Linux'), \
         patch('platform.release', return_value='5.15.0'), \
         patch('psutil.cpu_count', return_value=4), \
         patch('psutil.virtual_memory') as mock_mem:
        
        mock_mem.return_value.total = 16000000000
        mock_mem.return_value.available = 8000000000
        mock_mem.return_value.percent = 50.0
        
        info = get_system_info()
        
        assert info['os'] == 'Linux'
        assert info['release'] == '5.15.0'
        assert info['cpu_count'] == 4
        assert info['memory']['total'] == 16000000000

def test_list_processes():
    mock_proc1 = MagicMock()
    mock_proc1.info = {'pid': 1, 'name': 'init', 'status': 'running', 'username': 'root'}
    
    mock_proc2 = MagicMock()
    mock_proc2.info = {'pid': 100, 'name': 'python', 'status': 'running', 'username': 'user'}
    
    with patch('psutil.process_iter', return_value=[mock_proc1, mock_proc2]):
        procs = list_processes()
        
        assert len(procs) == 2
        assert procs[0]['name'] == 'init'
        assert procs[1]['name'] == 'python'