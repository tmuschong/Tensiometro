from flask import Flask, render_template_string, request, send_file
import random
import matplotlib.pyplot as plt
import io
import base64
from fpdf import FPDF
import tempfile

app = Flask(__name__)

def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(10, 4))  # Más largo
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8'), buf

@app.route("/", methods=["GET", "POST"])
def home():
    datos = {
        "nombre": "Pepe",
        "apellido": "Pepito",
        "dni": "12.345.678",
        "edad": "71",
        "tiempo": "20"
    }

    if request.method == "POST":
        for campo in datos:
            datos[campo] = request.form.get(campo)

    sistolica = [random.randint(110, 140) for _ in range(72)]
    diastolica = [random.randint(70, 90) for _ in range(72)]

    img_sis_base64, img_sis_buffer = generar_grafico("Presión Sistólica", sistolica)
    img_dia_base64, img_dia_buffer = generar_grafico("Presión Diastólica", diastolica)

    tabla_datos = [(i + 1, sistolica[i], diastolica[i]) for i in range(72)]

    html = """
    <html>
    <head>
        <title>Informe de Presión</title>
        <style>
            body { font-family: Arial; margin: 30px; }
            .formulario input { margin: 5px; padding: 5px; width: 200px; }
            .formulario button { margin: 10px; padding: 5px 10px; }
            .paciente-info { font-size: 14px; margin-bottom: 20px; text-align: left; }
            .grafico { width: 48%; display: inline-block; vertical-align: top; }
            .tabla { margin-top: 40px; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <form class="formulario" method="post">
            <input name="nombre" placeholder="Nombre" value="{{datos.nombre}}">
            <input name="apellido" placeholder="Apellido" value="{{datos.apellido}}">
            <input name="dni" placeholder="DNI" value="{{datos.dni}}">
            <input name="edad" placeholder="Edad" value="{{datos.edad}}">
            <input name="tiempo" placeholder="Tiempo (min)" value="{{datos.tiempo}}">
            <button type="submit">Ingresar datos del paciente</button>
        </form>

        <div class="paciente-info">
            <strong>Datos del paciente:</strong><br>
            Nombre: {{datos.nombre}}<br>
            Apellido: {{datos.apellido}}<br>
            DNI: {{datos.dni}}<br>
            Edad: {{datos.edad}}<br>
            Tiempo de muestreo (min): {{datos.tiempo}}<br>
        </div>

        <div>
            <div class="grafico">
                <h3>Presión Sistólica</h3>
                <img src="data:image/png;base64,{{img_sis}}">
            </div>
            <div class="grafico">
                <h3>Presión Diastólica</h3>
                <img src="data:image/png;base64,{{img_dia}}">
            </div>
        </div>

        <div class="tabla">
            <h3>Datos de las mediciones</h3>
            <table>
                <tr><th>N°</th><th>Sistólica</th><th>Diastólica</th></tr>
                {% for i, sis, dia in tabla_datos %}
                    <tr><td>{{i}}</td><td>{{sis}}</td><td>{{dia}}</td></tr>
                {% endfor %}
            </table>
        </div>

        <form action="/descargar_pdf" method="post">
            {% for key, value in datos.items() %}
                <input type="hidden" name="{{key}}" value="{{value}}">
            {% endfor %}
            <input type="hidden" name="img_sis" value="{{img_sis}}">
            <input type="hidden" name="img_dia" value="{{img_dia}}">
            {% for i, sis, dia in tabla_datos %}
                <input type="hidden" name="tabla" value="{{i}},{{sis}},{{dia}}">
            {% endfor %}
            <button type="submit">Exportar PDF</button>
        </form>
    </body>
    </html>
    """

    return render_template_string(html, datos=datos, img_sis=img_sis_base64, img_dia=img_dia_base64, tabla_datos=tabla_datos)

@app.route("/descargar_pdf", methods=["POST"])
def descargar_pdf():
    datos = {k: request.form.get(k) for k in ["nombre", "apellido", "dni", "edad", "tiempo"]}
    tabla = [tuple(map(int, row.split(','))) for row in request.form.getlist("tabla")]

    img_sis_data = base64.b64decode(request.form["img_sis"])
    img_dia_data = base64.b64decode(request.form["img_dia"])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f2:
        f1.write(img_sis_data)
        f2.write(img_dia_data)
        f1_path = f1.name
        f2_path = f2.name

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Informe de Presión Arterial", ln=True, align="C")
    pdf.ln(10)
    for k, v in datos.items():
        pdf.cell(200, 8, f"{k.capitalize()}: {v}", ln=True)
    pdf.ln(5)
    pdf.image(f1_path, w=180)
    pdf.ln(5)
    pdf.image(f2_path, w=180)
    pdf.ln(5)

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, "Tabla de datos", ln=True)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(20, 8, "N°", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Sistólica", 1, 0, 'C', 1)
    pdf.cell(40, 8, "Diastólica", 1, 1, 'C', 1)

    for i, sis, dia in tabla:
        pdf.cell(20, 8, str(i), 1)
        pdf.cell(40, 8, str(sis), 1)
        pdf.cell(40, 8, str(dia), 1)
        pdf.ln(8)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
        pdf.output(output.name)
        output.seek(0)
        return send_file(output.name, as_attachment=True, download_name="informe_paciente.pdf")

if __name__ == "__main__":
    app.run(debug=True)

