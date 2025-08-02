from flask import Flask, render_template_string, request, send_file
import random
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
from weasyprint import HTML

app = Flask(__name__)

# Generar gráfico como imagen base64
def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# Ruta principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        dni = request.form["dni"]
        edad = request.form["edad"]
        tiempo = request.form["tiempo"]

        sistolica = [random.randint(110, 140) for _ in range(72)]
        diastolica = [random.randint(70, 90) for _ in range(72)]

        img_sis = generar_grafico("Presión Sistólica", sistolica)
        img_dia = generar_grafico("Presión Diastólica", diastolica)

        datos_tabla = list(zip(range(1, 73), sistolica, diastolica))

        # Guardamos todo para el PDF
        html = render_template_string(PLANTILLA, nombre=nombre, apellido=apellido,
                                      dni=dni, edad=edad, tiempo=tiempo,
                                      img_sis=img_sis, img_dia=img_dia, datos=datos_tabla, pdf=False)
        with open("last_report.html", "w", encoding="utf-8") as f:
            f.write(html)

        return html

    return '''
    <form method="post">
        <h3>Ingresar datos del paciente:</h3>
        Nombre: <input name="nombre"><br>
        Apellido: <input name="apellido"><br>
        DNI: <input name="dni"><br>
        Edad: <input name="edad"><br>
        Tiempo de muestreo (min): <input name="tiempo"><br>
        <button type="submit">Ingresar datos del paciente</button>
    </form>
    '''

# Ruta para descargar el PDF
@app.route("/descargar_pdf")
def descargar_pdf():
    pdf_html = open("last_report.html", encoding="utf-8").read()
    pdf_io = io.BytesIO()
    HTML(string=pdf_html).write_pdf(pdf_io)
    pdf_io.seek(0)
    return send_file(pdf_io, as_attachment=True, download_name="informe_paciente.pdf", mimetype='application/pdf')

# Plantilla HTML para web y PDF
PLANTILLA = """
<html>
<head>
    <title>Informe del Paciente</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .datos { font-size: 12px; text-align: left; }
        .graficos { display: flex; flex-direction: column; align-items: center; }
        table { border-collapse: collapse; margin-top: 20px; width: 100%; }
        th, td { border: 1px solid black; padding: 5px; text-align: center; font-size: 12px; }
        h1 { margin-top: 20px; }
        .btn-descarga { margin-top: 20px; }
    </style>
</head>
<body>
    <div class="datos">
        <strong>Datos del paciente:</strong><br>
        Nombre: {{nombre}}<br>
        Apellido: {{apellido}}<br>
        DNI: {{dni}}<br>
        Edad: {{edad}}<br>
        Tiempo de muestreo (min): {{tiempo}}<br>
    </div>

    <div class="graficos">
        <h1>Presión Sistólica</h1>
        <img src="data:image/png;base64,{{img_sis}}" width="100%">
        <h1>Presión Diastólica</h1>
        <img src="data:image/png;base64,{{img_dia}}" width="100%">
    </div>

    <h2>Tabla de Valores</h2>
    <table>
        <tr><th>Medición</th><th>Sistólica</th><th>Diastólica</th></tr>
        {% for i, sis, dia in datos %}
        <tr><td>{{i}}</td><td>{{sis}}</td><td>{{dia}}</td></tr>
        {% endfor %}
    </table>

    {% if not pdf %}
    <div class="btn-descarga">
        <a href="/descargar_pdf" target="_blank">📄 Descargar PDF</a>
    </div>
    {% endif %}
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)



