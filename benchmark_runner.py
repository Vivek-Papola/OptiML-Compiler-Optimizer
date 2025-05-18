import subprocess
import time

def compile_and_run(source_file, flags):
    output_bin = 'a.out'
    compile_cmd = ["gcc", source_file, "-o", output_bin] + flags

    try:
        subprocess.run(compile_cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return float('inf')

    start = time.perf_counter()
    try:
        subprocess.run(["./" + output_bin], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return float('inf')
    end = time.perf_counter()
    
    return end - start
