from flask import Flask, request, render_template_string, jsonify, send_file
import matplotlib.pyplot as plt
import io
import base64
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# Variable global para almacenar los datos más recientes del ESP01
datos_esp = {
    "sistolica": [],
    "diastolica": [],
    "hora": [],
    "minutos": [],
    "segundos": [],
    "dia": [],
    "mes": [],
    "ano": [],
    "ppm": []
}

# Función para generar gráficos y devolver base64
def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Valor")
    ax.set_xlabel("Tiempo")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# Endpoint para recibir datos desde ESP01
@app.route("/data", methods=["POST"])
def recibir_datos():
    global datos_esp
    try:
        contenido = request.get_json()
        # Guardar todos los campos enviados por ESP
        datos_esp["sistolica"]  = contenido.get("sistolica", [])
        datos_esp["diastolica"] = contenido.get("diastolica", [])
        datos_esp["hora"]       = contenido.get("hora", [])
        datos_esp["minutos"]    = contenido.get("minutos", [])
        datos_esp["segundos"]   = contenido.get("segundos", [])
        datos_esp["dia"]        = contenido.get("dia", [])
        datos_esp["mes"]        = contenido.get("mes", [])
        datos_esp["ano"]        = contenido.get("ano", [])
        datos_esp["ppm"]        = contenido.get("ppm", [])
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detalle": str(e)}), 400

# Página principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Datos del paciente
        nombre = request.form.get("nombre", "N/A")
        apellido = request.form.get("apellido", "N/A")
        dni = request.form.get("dni", "N/A")
        edad = request.form.get("edad", "N/A")
        tiempo = request.form.get("tiempo", "N/A")

        # Datos de ESP01
        sistolica  = datos_esp.get("sistolica", [])
        diastolica = datos_esp.get("diastolica", [])
        ppm        = datos_esp.get("ppm", [])

        # Generar gráficos
        img_sis = generar_grafico("Presión Sistólica", sistolica)
        img_dia = generar_grafico("Presión Diastólica", diastolica)
        img_ppm = generar_grafico("PPM", ppm)

        # Tabla HTML con PPM
        filas = "".join(
            f"<tr><td>{i+1}</td><td>{s}</td><td>{d}</td><td>{p}</td></tr>"
            for i, (s, d, p) in enumerate(zip(sistolica, diastolica, ppm))
        )

        html = f"""
        <html>
        <head>
            <title>Informe de Presión</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                .datos {{ font-size: 0.9em; text-align: left; margin-bottom: 20px; }}
                .graficos {{ display: flex; flex-direction: column; align-items: center; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 6px;
                    text-align: center;
                }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="datos">
                <strong>Datos del paciente:</strong><br>
                Nombre: {nombre}<br>
                Apellido: {apellido}<br>
                DNI: {dni}<br>
                Edad: {edad}<br>
                Tiempo de muestreo (min): {tiempo}
            </div>

            <div class="graficos">
                <h2>Presión Sistólica</h2>
                <img src="data:image/png;base64,{img_sis}">
                <h2>Presión Diastólica</h2>
                <img src="data:image/png;base64,{img_dia}">
                <h2>PPM</h2>
                <img src="data:image/png;base64,{img_ppm}">
            </div>

            <table>
                <tr><th>N°</th><th>Sistólica</th><th>Diastólica</th><th>PPM</th></tr>
                {filas}
            </table>

            <br>
            <form action="/exportar_pdf" method="post">
                <input type="hidden" name="nombre" value="{nombre}">
                <input type="hidden" name="apellido" value="{apellido}">
                <input type="hidden" name="dni" value="{dni}">
                <input type="hidden" name="edad" value="{edad}">
                <input type="hidden" name="tiempo" value="{tiempo}">
                <input type="hidden" name="sistolica" value="{','.join(map(str, sistolica))}">
                <input type="hidden" name="diastolica" value="{','.join(map(str, diastolica))}">
                <input type="hidden" name="ppm" value="{','.join(map(str, ppm))}">
                <input type="hidden" name="img_sis" value="{img_sis}">
                <input type="hidden" name="img_dia" value="{img_dia}">
                <input type="hidden" name="img_ppm" value="{img_ppm}">
                <button type="submit">Exportar a PDF</button>
            </form>
        </body>
        </html>
        """
        return html

    # GET: formulario de ingreso
    return """
    <html>
    <head>
        <title>Datos del Paciente</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            form { max-width: 400px; }
            label { display: block; margin-top: 10px; }
            input[type="text"], input[type="number"] {
                width: 100%;
                padding: 6px;
                margin-top: 4px;
            }
            input[type="submit"] {
                margin-top: 20px;
                padding: 10px 20px;
            }
        </style>
    </head>
    <body>
        <h2>Ingresar datos del paciente</h2>
        <form method="POST">
            <label>Nombre:
                <input type="text" name="nombre" required>
            </label>
            <label>Apellido:
                <input type="text" name="apellido" required>
            </label>
            <label>DNI:
                <input type="text" name="dni" required>
            </label>
            <label>Edad:
                <input type="number" name="edad" required>
            </label>
            <label>Tiempo de muestreo (min):
                <input type="number" name="tiempo" required>
            </label>
            <input type="submit" value="Ingresar datos del paciente">
        </form>
    </body>
    </html>
    """

# Exportar PDF con gráficos y tabla
@app.route("/exportar_pdf", methods=["POST"])
def exportar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    # Datos del formulario
    nombre = request.form.get("nombre")
    apellido = request.form.get("apellido")
    dni = request.form.get("dni")
    edad = request.form.get("edad")
    tiempo = request.form.get("tiempo")

    sistolica  = list(map(int, request.form.get("sistolica").split(',')))
    diastolica = list(map(int, request.form.get("diastolica").split(',')))
    ppm        = list(map(int, request.form.get("ppm").split(',')))

    img_sis_b64 = request.form.get("img_sis")
    img_dia_b64 = request.form.get("img_dia")
    img_ppm_b64 = request.form.get("img_ppm")

    img_bytes_sis = io.BytesIO(base64.b64decode(img_sis_b64))
    img_bytes_dia = io.BytesIO(base64.b64decode(img_dia_b64))
    img_bytes_ppm = io.BytesIO(base64.b64decode(img_ppm_b64))

    elementos.append(Paragraph("Informe de Presión Arterial", styles['Title']))
    elementos.append(Spacer(1, 12))

    info = f"""
    <b>Nombre:</b> {nombre}<br/>
    <b>Apellido:</b> {apellido}<br/>
    <b>DNI:</b> {dni}<br/>
    <b>Edad:</b> {edad}<br/>
    <b>Tiempo de muestreo:</b> {tiempo} min
    """
    elementos.append(Paragraph(info, styles['Normal']))
    elementos.append(Spacer(1, 12))

    # Agregar gráficos
    elementos.append(Paragraph("Gráfico Presión Sistólica", styles['Heading2']))
    elementos.append(RLImage(img_bytes_sis, width=400, height=150))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico Presión Diastólica", styles['Heading2']))
    elementos.append(RLImage(img_bytes_dia, width=400, height=150))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico PPM", styles['Heading2']))
    elementos.append(RLImage(img_bytes_ppm, width=400, height=150))
    elementos.append(Spacer(1, 12))

    # Tabla con PPM
    tabla_datos = [["N°", "Sistólica", "Diastólica", "PPM"]]
    for i, (s, d, p) in enumerate(zip(sistolica, diastolica, ppm)):
        tabla_datos.append([str(i+1), str(s), str(d), str(p)])

    t = Table(tabla_datos, repeatRows=1)
    elementos.append(t)

    doc.build(elementos)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="informe_presion.pdf", mimetype='application/pdf')


if __name__ == "__main__":
    app.run(debug=True)

