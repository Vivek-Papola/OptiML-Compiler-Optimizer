import os
import re
import tempfile
from flask import Flask, request, render_template_string, redirect, flash
import joblib
import pandas as pd
import numpy as np
import subprocess

# --- Feature extraction and prediction logic ---
class PredictFeatureExtractor:
    def __init__(self):
        self.features_list = [
            "add", "mul", "load", "store", "call",
            "define", "br i1", "loops", "basic_blocks", "total_instructions"
        ]

    def _count_in_ir(self, ir_filename, pattern):
        cnt = 0
        regex = re.compile(pattern)
        with open(ir_filename, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if regex.search(line):
                    cnt += 1
        return cnt

    def count_instruction(self, ir_filename, keyword):
        return self._count_in_ir(ir_filename, re.escape(keyword))

    def count_instruction_c_source(self, filename, keyword):
        try:
            result = subprocess.check_output(
                rf"grep -E '\\b(for|while|do)\\b' {filename} | wc -l",
                shell=True
            )
            return int(result.strip())
        except Exception:
            return 0

    def get_basic_block_count(self, ir_filename):
        return self._count_in_ir(ir_filename, r'^[A-Za-z0-9_.]+:')

    def get_total_instructions(self, ir_filename):
        with open(ir_filename, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)

    def extract_features(self, c_file_path):
        if not os.path.exists(c_file_path):
            return {}
        feature_dict = {}
        with tempfile.NamedTemporaryFile(suffix=".ll", delete=False) as tmp_ll:
            temp_ir_file = tmp_ll.name
        try:
            subprocess.run(
                f"clang -S -emit-llvm {c_file_path} -o {temp_ir_file}",
                shell=True, check=True, capture_output=True
            )
            for feature in self.features_list:
                if feature == "basic_blocks":
                    feature_dict[feature] = self.get_basic_block_count(temp_ir_file)
                elif feature == "total_instructions":
                    feature_dict[feature] = self.get_total_instructions(temp_ir_file)
                elif feature == "loops":
                    feature_dict[feature] = self.count_instruction_c_source(c_file_path, "loops")
                else:
                    feature_dict[feature] = self.count_instruction(temp_ir_file, feature)
        except subprocess.CalledProcessError:
            return {}
        finally:
            if os.path.exists(temp_ir_file):
                os.remove(temp_ir_file)
        return feature_dict


def predict_optimization_flags(c_file_path, model, feature_extractor):
    features = feature_extractor.extract_features(c_file_path)
    if not features:
        return None, None, None
    cols = [
        "add", "mul", "load", "store", "call",
        "define", "br i1", "loops", "basic_blocks", "total_instructions"
    ]
    df = pd.DataFrame([[features.get(c, 0) for c in cols]], columns=cols)
    preds = model.predict(df)
    row = preds.flatten()
    opt_idx = int(np.argmax(row[:5]))
    opt_map = {0: "O0", 1: "O1", 2: "O2", 3: "O3", 4: "Os"}
    opt_flag = opt_map.get(opt_idx, "O0")
    f_flag = "fomit-frame-pointer" if row[5] >= 0.5 else None
    u_flag = "funroll-loops" if row[6] >= 0.5 else None
    return opt_flag, f_flag, u_flag

# --- Flask App ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load model
MODEL_PATH = 'random_forest_optimization_model.joblib'
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load model: {e}")
extractor = PredictFeatureExtractor()

# HTML template with Bootstrap, Animate.css, spinner, editor & file upload
TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OptiML</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" />
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <style>
    #spinner { display: none; }
    .btn-animate:hover { transform: scale(1.05); transition: transform 0.2s; }
  </style>
</head>
<body class="bg-light animate__animated animate__fadeIn">
  <div class="container py-5">
    <h1 class="mb-4 text-center animate__animated animate__zoomIn">OptiML</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="alert alert-danger animate__animated animate__shakeX">
          {% for msg in messages %}
            <div>{{ msg }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
    <form method="post" enctype="multipart/form-data" onsubmit="showSpinner()" class="animate__animated animate__fadeInUp">
      <div class="mb-3">
        <label for="codeArea" class="form-label">Paste C code here:</label>
        <textarea class="form-control animate__animated animate__fadeIn" id="codeArea" name="code" rows="6"></textarea>
      </div>
      <div class="mb-3">
        <label for="cfile" class="form-label">Or upload a C source file:</label>
        <input class="form-control" type="file" id="cfile" name="cfile" accept=".c">
      </div>
      <button type="submit" class="btn btn-primary btn-animate animate__animated animate__heartBeat">Predict</button>
      <div id="spinner" class="spinner-border text-primary ms-3 animate__animated animate__rotateIn" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </form>
    {% if result %}
      <div class="card mt-4 animate__animated animate__fadeInRight">
        <div class="card-body">
          <h5 class="card-title">Prediction for {{ filename }}:</h5>
          <ul>
            <li><strong>-{{ result.opt_flag }}</strong></li>
            {% if result.f_flag %}<li><strong>-{{ result.f_flag }}</strong></li>{% endif %}
            {% if result.u_flag %}<li><strong>-{{ result.u_flag }}</strong></li>{% endif %}
          </ul>
          <p>Compile with:</p>
          <code>clang -{{ result.opt_flag }} {% if result.f_flag %}-{{ result.f_flag }} {% endif %}{% if result.u_flag %}-{{ result.u_flag }} {% endif %}{{ filename }} -o {{ filename[:-2] }}</code>
        </div>
      </div>
    {% endif %}
  </div>
  <script>
    function showSpinner() {
      document.getElementById('spinner').style.display = 'inline-block';
    }
  </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def upload_and_predict():
    result = None
    filename = None
    if request.method == 'POST':
        code_text = request.form.get('code')
        uploaded = request.files.get('cfile')
        if not code_text and (not uploaded or uploaded.filename == ''):
            flash('Please paste code or upload a .c file')
            return render_template_string(TEMPLATE, result=None)
        tmp = tempfile.NamedTemporaryFile(suffix='.c', delete=False)
        filename = uploaded.filename if uploaded and uploaded.filename.endswith('.c') else 'pasted_code.c'
        if code_text:
            tmp.write(code_text.encode())
        else:
            uploaded.save(tmp.name)
        tmp.close()
        try:
            opt, fopt, uopt = predict_optimization_flags(tmp.name, model, extractor)
        except Exception:
            flash('Error during feature extraction or prediction')
            os.remove(tmp.name)
            return render_template_string(TEMPLATE, result=None)
        os.remove(tmp.name)
        if not opt:
            flash('Could not extract features. Please check your C code.')
        else:
            result = {'opt_flag': opt, 'f_flag': fopt, 'u_flag': uopt}
    return render_template_string(TEMPLATE, result=result, filename=filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
