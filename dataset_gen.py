import subprocess
import os
import csv
import tempfile

class DatasetGenerator:
    def __init__(self, csv_file='code_dataset.csv'):
        self.opt_levels = ['-O0', '-O1', '-O2', '-O3', '-Os']
        self.features = ["add", "mul", "load", "store", "call", "define", "br i1"]
        self.csv_file = csv_file

    def count_instruction(self, filename, keyword):
        try:
            result = subprocess.check_output(f"grep -o '{keyword}' {filename} | wc -l", shell=True)
            return int(result.strip())
        except:
            return 0

    def get_basic_block_count(self, filename):
        try:
            result = subprocess.check_output(f"grep -oE '^[a-zA-Z0-9_.]+:' {filename} | wc -l", shell=True)
            return int(result.strip())
        except:
            return 0

    def get_instruction_count(self, filename):
        try:
            result = subprocess.check_output(f"grep -E '^\\s+[a-z]' {filename} | wc -l", shell=True)
            return int(result.strip())
        except:
            return 0

    def compile_and_measure(self, c_file, opt_flag):
        out_exec = tempfile.mktemp()
        try:
            subprocess.run(f"clang {opt_flag} {c_file} -o {out_exec} -lm", shell=True, check=True)
            result = subprocess.check_output(f"/usr/bin/time -f '%e' {out_exec}", shell=True, stderr=subprocess.STDOUT)
            exec_time = float(result.strip().splitlines()[-1])
            return exec_time
        except subprocess.CalledProcessError:
            print(f"[!] Failed at {opt_flag}")
            return float('inf')
        finally:
            if os.path.exists(out_exec):
                os.remove(out_exec)

    def extract_features(self, c_file):
        ir_file = tempfile.mktemp(suffix=".ll")
        subprocess.run(f"clang -O0 -S -emit-llvm {c_file} -o {ir_file}", shell=True, check=True)
        
        feats = {}
        for instr in self.features:
            feats[instr] = self.count_instruction(ir_file, instr)
        
        feats['basic_blocks'] = self.get_basic_block_count(ir_file)
        feats['total_instructions'] = self.get_instruction_count(ir_file)

        os.remove(ir_file)
        return feats

    def get_best_optimization_flag(self, c_file):
        timings = {}
        for flag in self.opt_levels:
            time_taken = self.compile_and_measure(c_file, flag)
            timings[flag] = time_taken
        return min(timings, key=timings.get)

    def save_to_csv(self, feature_dict, label):
        header = list(feature_dict.keys()) + ['label']
        row = list(feature_dict.values()) + [label]
        file_exists = os.path.exists(self.csv_file)
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(row)

    def process_file(self, c_file):
        feats = self.extract_features(c_file)
        best_flag = self.get_best_optimization_flag(c_file)
        self.save_to_csv(feats, best_flag)
        print(f"[✓] Processed {c_file}, best flag: {best_flag}")
