from flask import Flask, render_template_string
import random
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Función para generar una imagen de gráfico en base64
def generar_grafico(titulo, valores):
    fig, ax = plt.subplots()
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")

    # Convertimos el gráfico en imagen base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    imagen_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return imagen_base64

@app.route("/")
def home():
    # Simulamos 72 lecturas aleatorias
    sistolica = [random.randint(110, 140) for _ in range(72)]
    diastolica = [random.randint(70, 90) for _ in range(72)]

    img_sis = generar_grafico("Presión Sistólica", sistolica)
    img_dia = generar_grafico("Presión Diastólica", diastolica)

    # Plantilla HTML
    html = """
    <html>
    <head>
        <title>Presiones Arteriales</title>
        <style>
            .contenedor {
                display: flex;
                flex-direction: row;
                align-items: flex-start;
            }
            .graficos {
                flex: 1;
                padding: 10px;
            }
            .tabla {
                flex: 1;
                padding: 10px;
            }
            table, th, td {
                border: 1px solid black;
                border-collapse: collapse;
                padding: 5px;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Monitor de Presión Arterial</h1>
        <div class="contenedor">
            <div class="graficos">
                <h2>Presión Sistólica</h2>
                <img src="data:image/png;base64,{{img_sis}}">
                <h2>Presión Diastólica</h2>
                <img src="data:image/png;base64,{{img_dia}}">
            </div>
            <div class="tabla">
                <h2>Valores Numéricos</h2>
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
    # Combinamos los valores para usarlos en la tabla
    valores = list(zip(sistolica, diastolica))
    return render_template_string(html, img_sis=img_sis, img_dia=img_dia, valores=valores)

if __name__ == "__main__":
    app.run(debug=True)

