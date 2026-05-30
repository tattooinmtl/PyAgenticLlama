import subprocess, json

def system_info() -> dict:
    try:
        out = subprocess.check_output(
            ['powershell', '-NoProfile', '-Command', r'''
                $os  = Get-WmiObject Win32_OperatingSystem
                $gpu = Get-WmiObject Win32_VideoController | Select-Object -First 1
                $cpu = Get-WmiObject Win32_Processor | Select-Object -First 1
                @{
                  RamTotal = [long]$os.TotalVisibleMemorySize
                  RamFree  = [long]$os.FreePhysicalMemory
                  Vram     = [long]$gpu.AdapterRAM
                  GpuName  = [string]$gpu.Name
                  CpuName  = [string]$cpu.Name
                  Cores    = [int]$cpu.NumberOfCores
                } | ConvertTo-Json -Compress
            '''],
            text=True, timeout=10
        ).strip()
        d = json.loads(out)
        return {
            'ram_total_gb':     round(d.get('RamTotal', 0) / 1024 / 1024, 1),
            'ram_available_gb': round(d.get('RamFree',  0) / 1024 / 1024, 1),
            'vram_gb':          round(d.get('Vram',     0) / 1024**3, 1),
            'gpu_name':         d.get('GpuName', 'Unknown'),
            'cpu_name':         d.get('CpuName', 'Unknown'),
            'cpu_cores':        d.get('Cores', 0),
        }
    except Exception as e:
        return {
            'ram_total_gb': 0, 'ram_available_gb': 0, 'vram_gb': 0,
            'gpu_name': 'Unknown', 'cpu_name': 'Unknown', 'cpu_cores': 0,
            'error': str(e),
        }

def will_fit(model_ram_gb: float) -> tuple[bool, str]:
    hw = system_info()
    usable = max(hw['ram_available_gb'] - 3.0, 0)
    fits = model_ram_gb <= usable
    msg = (
        f"Fits — {model_ram_gb:.1f} GB needed, {usable:.1f} GB free"
        if fits else
        f"May not fit — {model_ram_gb:.1f} GB needed, {usable:.1f} GB free"
    )
    return fits, msg
