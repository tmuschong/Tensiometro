from flask import Flask, request, render_template_string, jsonify
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Variable global para almacenar los datos del ESP01
datos_esp = {
    "sistolica": [],
    "diastolica": [],
    "ppm": []
}

# Función para generar gráficos en base64
def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(8,3))
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Valor")
    ax.set_xlabel("Tiempo")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# Endpoint para recibir datos POST desde ESP01
@app.route("/data", methods=["POST"])
def recibir_datos():
    global datos_esp
    try:
        contenido = request.get_json()
        # Guardamos solo los campos que nos interesan
        datos_esp["sistolica"] = contenido.get("sistolica", [])
        datos_esp["diastolica"] = contenido.get("diastolica", [])
        datos_esp["ppm"] = contenido.get("ppm", [])
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detalle": str(e)}), 400
        
# Endpoint GET para debug: mostrar datos actuales en navegador
@app.route("/data_debug", methods=["GET"])
def data_debug():
    global datos_esp
    return jsonify(datos_esp)


# Página principal que muestra gráficos
@app.route("/", methods=["GET"])
def home():
    img_sis = generar_grafico("Presión Sistólica", datos_esp.get("sistolica", []))
    img_dia = generar_grafico("Presión Diastólica", datos_esp.get("diastolica", []))
    img_ppm = generar_grafico("PPM", datos_esp.get("ppm", []))

    html = f"""
    <html>
    <body>
        <h2>Presión Sistólica</h2>
        <img src="data:image/png;base64,{img_sis}">
        <h2>Presión Diastólica</h2>
        <img src="data:image/png;base64,{img_dia}">
        <h2>PPM</h2>
        <img src="data:image/png;base64,{img_ppm}">
    </body>
    </html>
    """
    return html

# Endpoint para ver datos en JSON (debug)
@app.route("/data_get", methods=["GET"])
def ver_datos():
    return jsonify(datos_esp)

if __name__ == "__main__":
    # Escuchar en todas las interfaces para Render
    app.run(host="0.0.0.0", port=5000, debug=True)


