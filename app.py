from flask import Flask, render_template_string
import random
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Función para generar imagen de gráfico en base64
def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(12, 4))  # más ancho
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Medición")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route("/")
def home():
    # Simulamos lecturas
    sistolica = [random.randint(110, 140) for _ in range(72)]
    diastolica = [random.randint(70, 90) for _ in range(72)]

    img_sis = generar_grafico("Presión Sistólica", sistolica)
    img_dia = generar_grafico("Presión Diastólica", diastolica)

    html = """
    <html>
    <head>
        <title>Monitor de Presión</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
                background-color: #f9f9f9;
            }
            .contenedor {
                max-width: 1200px;
                margin: auto;
            }
            .graficos img {
                display: block;
                width: 100%;
                margin-bottom: 30px;
                border: 1px solid #ccc;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
            }
            .tabla {
                margin-top: 40px;
                overflow-x: auto;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 6px 8px;
                text-align: center;
            }
            th {
                background-color: #e0e0e0;
            }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <h1>Monitor de Presión Arterial</h1>
            <div class="graficos">
                <h2>Presión Sistólica</h2>
                <img src="data:image/png;base64,{{img_sis}}">
                <h2>Presión Diastólica</h2>
                <img src="data:image/png;base64,{{img_dia}}">
            </div>
            <div class="tabla">
                <h2>Tabla de Mediciones</h2>
                <table>
                    <tr>
                        <th>#</th>
                        <th>Sistólica</th>
                        <th>Diastólica</th>
                    </tr>
                    {% for i in range(valores|length) %}
                    <tr>
                        <td>{{ i+1 }}</td>
                        <td>{{ valores[i][0] }}</td>
                        <td>{{ valores[i][1] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    valores = list(zip(sistolica, diastolica))
    return render_template_string(html, img_sis=img_sis, img_dia=img_dia, valores=valores)

if __name__ == "__main__":
    app.run(debug=True)


