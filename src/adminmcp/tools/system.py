import platform
import psutil
from typing import Dict, List, Any

def get_system_info() -> Dict[str, Any]:
    """
    Get system information including OS, Kernel, CPU, and Memory stats.
    """
    mem = psutil.virtual_memory()
    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(),
        "memory": {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used,
            "free": mem.free
        }
    }

def list_processes() -> List[Dict[str, Any]]:
    """
    Get a list of running processes.
    """
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'username']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes