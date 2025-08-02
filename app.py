from flask import Flask, render_template_string, request, send_file
import random
import matplotlib.pyplot as plt
import io
import base64
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

app = Flask(__name__)

# Función para generar un gráfico y devolverlo como imagen base64 o como archivo temporal
def generar_grafico(titulo, valores, para_pdf=False):
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    if para_pdf:
        return buf
    else:
        return base64.b64encode(buf.read()).decode('utf-8')

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Leer datos del formulario
        nombre = request.form.get("nombre", "Pepe")
        apellido = request.form.get("apellido", "Pepito")
        dni = request.form.get("dni", "12.345.678")
        edad = request.form.get("edad", "71")
        tiempo = request.form.get("tiempo", "20")

        sistolica = [random.randint(110, 140) for _ in range(72)]
        diastolica = [random.randint(70, 90) for _ in range(72)]

        img_sis = generar_grafico("Presión Sistólica", sistolica)
        img_dia = generar_grafico("Presión Diastólica", diastolica)

        tabla = list(zip(range(1, 73), sistolica, diastolica))

        html = """
        <html>
        <head>
            <title>Informe de Presión</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 30px; }
                .datos { font-size: 12px; text-align: left; margin-bottom: 20px; }
                .graficos { display: flex; flex-direction: column; align-items: center; }
                table { border-collapse: collapse; margin-top: 20px; width: 100%; }
                th, td { border: 1px solid #000; padding: 4px; text-align: center; font-size: 14px; }
                th { background-color: #ddd; }
            </style>
        </head>
        <body>
            <div class="datos">
                <p><strong>Datos del paciente:</strong></p>
                <p>Nombre: {{nombre}}</p>
                <p>Apellido: {{apellido}}</p>
                <p>DNI: {{dni}}</p>
                <p>Edad: {{edad}}</p>
                <p>Tiempo de muestreo (min): {{tiempo}}</p>
            </div>
            <div class="graficos">
                <h2>Presión Sistólica</h2>
                <img src="data:image/png;base64,{{img_sis}}">
                <h2>Presión Diastólica</h2>
                <img src="data:image/png;base64,{{img_dia}}">
            </div>
            <table>
                <tr>
                    <th>#</th><th>Sistólica</th><th>Diastólica</th>
                </tr>
                {% for n, sis, dia in tabla %}
                <tr><td>{{n}}</td><td>{{sis}}</td><td>{{dia}}</td></tr>
                {% endfor %}
            </table>
            <br><br>
            <form action="/pdf" method="post">
                <input type="hidden" name="nombre" value="{{nombre}}">
                <input type="hidden" name="apellido" value="{{apellido}}">
                <input type="hidden" name="dni" value="{{dni}}">
                <input type="hidden" name="edad" value="{{edad}}">
                <input type="hidden" name="tiempo" value="{{tiempo}}">
                <input type="hidden" name="sistolica" value="{{sistolica}}">
                <input type="hidden" name="diastolica" value="{{diastolica}}">
                <button type="submit">Exportar PDF</button>
            </form>
        </body>
        </html>
        """

        return render_template_string(
            html,
            nombre=nombre, apellido=apellido, dni=dni, edad=edad, tiempo=tiempo,
            img_sis=img_sis, img_dia=img_dia,
            tabla=tabla, sistolica=','.join(map(str, sistolica)), diastolica=','.join(map(str, diastolica))
        )

    # Formulario de ingreso
    return '''
    <form method="post">
        <label>Nombre: <input name="nombre" required></label><br>
        <label>Apellido: <input name="apellido" required></label><br>
        <label>DNI: <input name="dni" required></label><br>
        <label>Edad: <input name="edad" required></label><br>
        <label>Tiempo de muestreo (min): <input name="tiempo" required></label><br>
        <button type="submit">Ingresar datos del paciente</button>
    </form>
    '''

@app.route("/pdf", methods=["POST"])
def pdf():
    # Recuperamos los datos
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    dni = request.form["dni"]
    edad = request.form["edad"]
    tiempo = request.form["tiempo"]

    sistolica = list(map(int, request.form["sistolica"].split(",")))
    diastolica = list(map(int, request.form["diastolica"].split(",")))

    tabla = [["#", "Sistólica", "Diastólica"]]
    for i in range(len(sistolica)):
        tabla.append([str(i + 1), str(sistolica[i]), str(diastolica[i])])

    img_sis_buf = generar_grafico("Presión Sistólica", sistolica, para_pdf=True)
    img_dia_buf = generar_grafico("Presión Diastólica", diastolica, para_pdf=True)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Datos del paciente:</b>", styles["Normal"]))
    elements.append(Paragraph(f"Nombre: {nombre}", styles["Normal"]))
    elements.append(Paragraph(f"Apellido: {apellido}", styles["Normal"]))
    elements.append(Paragraph(f"DNI: {dni}", styles["Normal"]))
    elements.append(Paragraph(f"Edad: {edad}", styles["Normal"]))
    elements.append(Paragraph(f"Tiempo de muestreo: {tiempo} minutos", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Agregar imágenes
    elements.append(Paragraph("Presión Sistólica", styles["Heading2"]))
    elements.append(RLImage(img_sis_buf, width=400, height=150))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Presión Diastólica", styles["Heading2"]))
    elements.append(RLImage(img_dia_buf, width=400, height=150))
    elements.append(Spacer(1, 12))

    # Tabla
    t = Table(tabla)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="informe_presion.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)
