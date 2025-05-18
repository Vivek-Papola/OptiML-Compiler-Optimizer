import os
import csv
from pycparser import parse_file, c_ast
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd

class FeatureExtractor(c_ast.NodeVisitor):
    def __init__(self):
        self.num_loops = 0
        self.num_ifs = 0
        self.num_functions = 0
        self.function_call_depths = []
        self.data_type_counts = {"int": 0, "float": 0}
        self.current_function_depth = 0
        self.max_call_depth = 0
        self.cyclomatic_complexity = 0

    def visit_FuncDef(self, node):
        self.num_functions += 1
        self.current_function_depth = 0
        self.cyclomatic_complexity += 1
        self.visit(node.body)

    def visit_If(self, node):
        self.num_ifs += 1
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.num_loops += 1
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.num_loops += 1
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_DoWhile(self, node):
        self.num_loops += 1
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_FuncCall(self, node):
        self.current_function_depth += 1
        if self.current_function_depth > self.max_call_depth:
            self.max_call_depth = self.current_function_depth
        self.generic_visit(node)
        self.current_function_depth -= 1

    def visit_Decl(self, node):
        if isinstance(node.type, c_ast.TypeDecl):
            type_str = self.get_type(node.type)
            if type_str in self.data_type_counts:
                self.data_type_counts[type_str] += 1

    def get_type(self, node):
        if isinstance(node, c_ast.TypeDecl):
            return self.get_type(node.type)
        if isinstance(node, c_ast.IdentifierType):
            return node.names[0]
        return None

def extract_features(c_file):
    try:
        ast = parse_file(
            c_file,
            use_cpp=True,
            cpp_path='gcc',
            cpp_args=[
                r'-I"C:\Users\Vivek\AppData\Roaming\Python\Python312\site-packages\pycparser\utils\fake_libc_include"'
            ]
        )
        extractor = FeatureExtractor()
        extractor.visit(ast)

        return {
            "filename": os.path.basename(c_file),
            "num_loops": extractor.num_loops,
            "num_ifs": extractor.num_ifs,
            "num_functions": extractor.num_functions,
            "max_function_call_depth": extractor.max_call_depth,
            "cyclomatic_complexity": extractor.cyclomatic_complexity,
            "int_count": extractor.data_type_counts["int"],
            "float_count": extractor.data_type_counts["float"],
            # Fake target for demo: 0 or 1 (e.g., use `-O2` or `-O3`)
            "best_flag": 1 if extractor.num_loops + extractor.num_ifs > 5 else 0
        }
    except Exception as e:
        print(f"Error parsing {c_file}: {e}")
        return None

def process_directory(dir_path, output_csv):
    fieldnames = ["filename", "num_loops", "num_ifs", "num_functions", "max_function_call_depth",
                  "cyclomatic_complexity", "int_count", "float_count", "best_flag"]

    rows = []
    for file in os.listdir(dir_path):
        if file.endswith(".c"):
            file_path = os.path.join(dir_path, file)
            features = extract_features(file_path)
            if features:
                rows.append(features)

    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Dataset saved to {output_csv} ✅")

def train_model(csv_path):
    df = pd.read_csv(csv_path)
    X = df.drop(columns=["filename", "best_flag"])
    y = df["best_flag"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n🎯 Model Evaluation:\n")
    print(classification_report(y_test, y_pred))

if __name__ == "__main__":
    c_dir = "c_files"
    output_csv = "dataset.csv"
    process_directory(c_dir, output_csv)
    train_model(output_csv)
