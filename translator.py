from flask import Flask, request, jsonify, render_template_string
import os
import traceback
from openai import AzureOpenAI  # or AzureOpenAI depending on SDK

# Azure OpenAI configuration
AZURE_ENDPOINT = "AZURE_OPENAI_ENDPOINT"
AZURE_KEY = "AZURE_OPENAI_KEY"
DEPLOYMENT = "AZURE_DEPLOYMENT_NAME"  # e.g. "gpt-4o-mini"
API_VERSION = "API_VERSION"   # or "2025-04-01-preview" if your resource supports it
# ----------------------------


# Initialize Azure client
client = AzureOpenAI(
     
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_KEY,
    api_version=API_VERSION
    
)

# ----------------------------
# FLASK APP
# ----------------------------
app = Flask(__name__)

# ----------------------------
# HTML + JS + CSS
# ----------------------------
HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Azure AI Text Translator</title>
<style>
body { font-family: Arial, sans-serif; background: #eef6ff; margin: 0; padding: 0;}
.container { max-width: 700px; margin: 50px auto; padding: 30px; background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);}
h1 { color: #1662c4; text-align:center;}
textarea { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #ccc;}
select { padding: 10px; border-radius: 8px; margin: 10px 0;}
button { background: #1e90ff; color: #fff; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-weight: bold;}
button:disabled { opacity: 0.6; cursor: not-allowed;}
#output { background: #f3f7ff; padding: 12px; border-radius: 8px; min-height: 50px; margin-top: 10px;}
</style>
</head>
<body>
<div class="container">
<h1>Azure AI Text Translator</h1>

<label for="language">Select target language:</label>
<select id="language">
  <option value="French">French</option>
  <option value="Spanish">Spanish</option>
  <option value="German">German</option>
  <option value="Chinese">Chinese</option>
  <option value="Arabic">Arabic</option>
  <option value="Hindi">Hindi</option>
  <option value="Urdu">Urdu (Pakistan)</option>
  <option value="Japanese">Japanese</option>
  <option value="Russian">Russian</option>
</select>

<textarea id="inputText" rows="5" placeholder="Enter text to translate..."></textarea>
<button id="translateBtn">Translate</button>

<h3>Translated Text:</h3>
<div id="output"></div>

<script>
const inputText = document.getElementById('inputText');
const language = document.getElementById('language');
const outputDiv = document.getElementById('output');
const btn = document.getElementById('translateBtn');

btn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    if (!text) return;
    outputDiv.innerText = "Translating...";
    btn.disabled = true;

    try {
        const res = await fetch('/translate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text, target_lang: language.value })
        });
        const data = await res.json();
        outputDiv.innerText = data.translation || "No translation received.";
    } catch(err) {
        outputDiv.innerText = "Error: " + err.message;
    } finally {
        btn.disabled = false;
    }
});
</script>
</div>
</body>
</html>
"""

# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "")
    target_lang = data.get("target_lang", "French")

    if not text:
        return jsonify({"translation": "Please provide text to translate."}), 400

    # Use Azure AI chat completion to translate
    try:
        prompt = f"Translate the following text to {target_lang}:\n\n{text}"
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role":"user","content": prompt}],
            max_tokens=300
        )
        translation = response.choices[0].message.content if response.choices else "No translation returned."
    except Exception as e:
        translation = f"Error communicating with Azure: {str(e)}"
        print(traceback.format_exc())

    return jsonify({"translation": translation})

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
