from flask import Flask, request, render_template_string, send_file, g
import random
import matplotlib.pyplot as plt
import io
import base64
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(10, 3))  # Más largo en eje X
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.form.get("nombre", "N/A")
        apellido = request.form.get("apellido", "N/A")
        dni = request.form.get("dni", "N/A")
        edad = request.form.get("edad", "N/A")
        tiempo = request.form.get("tiempo", "N/A")

        # Simular mediciones
        sistolica = [random.randint(110, 140) for _ in range(72)]
        diastolica = [random.randint(70, 90) for _ in range(72)]

        img_sis = generar_grafico("Presión Sistólica", sistolica)
        img_dia = generar_grafico("Presión Diastólica", diastolica)

        # Crear filas para la tabla HTML
        filas = "".join(
            f"<tr><td>{i+1}</td><td>{s}</td><td>{d}</td></tr>"
            for i, (s, d) in enumerate(zip(sistolica, diastolica))
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
            </div>

            <table>
                <tr><th>N°</th><th>Sistólica</th><th>Diastólica</th></tr>
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
        <input type="hidden" name="img_sis" value="{img_sis}">
        <input type="hidden" name="img_dia" value="{img_dia}">
        <button type="submit">Exportar a PDF</button>
    </form>
        </html>
        """
        return html

    # Si es GET, mostrar el formulario
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

@app.route("/exportar_pdf", methods=["POST"])
def exportar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    # Leer datos del formulario
    nombre = request.form.get("nombre")
    apellido = request.form.get("apellido")
    dni = request.form.get("dni")
    edad = request.form.get("edad")
    tiempo = request.form.get("tiempo")

    sistolica = list(map(int, request.form.get("sistolica").split(',')))
    diastolica = list(map(int, request.form.get("diastolica").split(',')))

    img_sis_b64 = request.form.get("img_sis")
    img_dia_b64 = request.form.get("img_dia")

    # Guardar imágenes temporales para reportlab
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_sis, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_dia:
        f_sis.write(base64.b64decode(img_sis_b64))
        f_dia.write(base64.b64decode(img_dia_b64))
        ruta_sis = f_sis.name
        ruta_dia = f_dia.name

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

    elementos.append(Paragraph("Gráfico Presión Sistólica", styles['Heading2']))
    elementos.append(RLImage(ruta_sis, width=400, height=150))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico Presión Diastólica", styles['Heading2']))
    elementos.append(RLImage(ruta_dia, width=400, height=150))
    elementos.append(Spacer(1, 12))

    tabla_datos = [["N°", "Sistólica", "Diastólica"]]
    for i, (s, d) in enumerate(zip(sistolica, diastolica)):
        tabla_datos.append([str(i+1), str(s), str(d)])

    t = Table(tabla_datos, repeatRows=1)
    elementos.append(t)

    doc.build(elementos)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="informe_presion.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)

