import os
import subprocess
import uuid
from flask import Flask, render_template, request, send_file, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = 'uploads'
DEOBFUSCATOR_PATH = 'Prometheus-DeobfuscatorV2-main/src/deob/cli.lua'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deobfuscate', methods=['POST'])
def deobfuscate():
    if 'file' not in request.files and 'code' not in request.form:
        flash('No file or code provided')
        return redirect(url_for('index'))

    input_path = None
    try:
        # Handle file upload
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and file.filename.endswith('.lua'):
                filename = f"{uuid.uuid4()}.lua"
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(input_path)
            else:
                flash('Invalid file type. Please upload a .lua file.')
                return redirect(url_for('index'))
        # Handle text area input
        elif 'code' in request.form and request.form['code'].strip() != '':
            code = request.form['code']
            filename = f"{uuid.uuid4()}.lua"
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(input_path, 'w') as f:
                f.write(code)
        else:
            flash('No file or code provided')
            return redirect(url_for('index'))

        if input_path:
            output_filename = f"{uuid.uuid4()}.deob.lua"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

            # Run the deobfuscator script
            # Example command: lua src/deob/cli.lua <input.lua> --out <output.lua>
            command = [
                'lua',
                DEOBFUSCATOR_PATH,
                input_path,
                '--out',
                output_path
            ]

            # Use --trace api as a default for better results as per README
            command.insert(3, '--trace')
            command.insert(4, 'api')

            result = subprocess.run(command, capture_output=True, text=True, check=True)

            with open(output_path, 'r') as f:
                deobfuscated_code = f.read()

            return render_template('result.html', original_code=open(input_path).read(), deobfuscated_code=deobfuscated_code, download_path=output_filename)

    except subprocess.CalledProcessError as e:
        error_message = f"Deobfuscation failed:\n LUA SCRIPT ERROR \n{e.stderr}"
        # Also include stdout if it has useful info
        if e.stdout:
            error_message += f"\n--- stdout ---\n{e.stdout}"
        flash(error_message)
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"An unexpected error occurred: {e}")
        return redirect(url_for('index'))
    finally:
        # Clean up the uploaded and generated files
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        # The output file is not removed immediately so it can be downloaded.
        # A proper app would have a cleanup job for old files.

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        flash("File not found.")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
