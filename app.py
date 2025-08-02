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

        # Guardar imágenes en archivos temporales para el PDF
        tempfile_sis = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tempfile_dia = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

        with open(tempfile_sis.name, 'wb') as f:
            f.write(base64.b64decode(img_sis))

        with open(tempfile_dia.name, 'wb') as f:
            f.write(base64.b64decode(img_dia))

        # Guardar los datos para exportar en PDF usando g (global context)
        g.datos_pdf = {
            "nombre": nombre,
            "apellido": apellido,
            "dni": dni,
            "edad": edad,
            "tiempo": tiempo,
            "sistolica": sistolica,
            "diastolica": diastolica,
            "img_sis": tempfile_sis.name,
            "img_dia": tempfile_dia.name
        }

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
                <button type="submit">Exportar a PDF</button>
            </form>
            <br><a href="/">Volver</a>
        </body>
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

    datos = g.get("datos_pdf", None)
    if not datos:
        return "No hay datos para exportar", 400

    elementos.append(Paragraph("Informe de Presión Arterial", styles['Title']))
    elementos.append(Spacer(1, 12))

    info = f"""
    <b>Nombre:</b> {datos['nombre']}<br/>
    <b>Apellido:</b> {datos['apellido']}<br/>
    <b>DNI:</b> {datos['dni']}<br/>
    <b>Edad:</b> {datos['edad']}<br/>
    <b>Tiempo de muestreo:</b> {datos['tiempo']} min
    """
    elementos.append(Paragraph(info, styles['Normal']))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico Presión Sistólica", styles['Heading2']))
    elementos.append(RLImage(datos['img_sis'], width=400, height=150))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico Presión Diastólica", styles['Heading2']))
    elementos.append(RLImage(datos['img_dia'], width=400, height=150))
    elementos.append(Spacer(1, 12))

    # Crear tabla con datos
    tabla_datos = [["N°", "Sistólica", "Diastólica"]]
    for i, (s, d) in enumerate(zip(datos["sistolica"], datos["diastolica"])):
        tabla_datos.append([str(i+1), str(s), str(d)])

    t = Table(tabla_datos, repeatRows=1)
    elementos.append(t)

    doc.build(elementos)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="informe_presion.pdf", mimetype='application/pdf')


if __name__ == "__main__":
    app.run(debug=True)

