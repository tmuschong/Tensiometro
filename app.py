from flask import Flask, render_template_string
import random
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Función para generar una imagen de gráfico en base64
def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(10, 4))  # Más ancho (doble)
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    imagen_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return imagen_base64

@app.route("/")
def home():
    # Simulamos 72 mediciones
    sistolica = [random.randint(110, 140) for _ in range(72)]
    diastolica = [random.randint(70, 90) for _ in range(72)]
    mediciones = list(range(1, 73))  # Números de medición

    img_sis = generar_grafico("Presión Sistólica", sistolica)
    img_dia = generar_grafico("Presión Diastólica", diastolica)

    # Plantilla HTML con estilos
    html = """
    <html>
    <head>
        <title>Presiones Arteriales</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 30px;
            }
            .contenedor {
                max-width: 1000px;
                margin: auto;
            }
            .datos-paciente {
                font-size: 0.9em;
                color: #333;
                margin-bottom: 20px;
                line-height: 1.4em;
            }
            .graficos {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 30px;
                margin-bottom: 40px;
            }
            .tabla {
                margin-top: 20px;
                overflow-x: auto;
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                border: 1px solid #888;
                padding: 6px 10px;
                text-align: center;
                font-size: 0.9em;
            }
            th {
                background-color: #eee;
            }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <div class="datos-paciente">
                <p><strong>Datos del paciente:</strong></p>
                <p>Nombre: Pepe</p>
                <p>Apellido: Pepito</p>
                <p>DNI: 12.345.678</p>
                <p>Edad: 71</p>
                <p>Tiempo de muestreo (min): 20</p>
            </div>
            <h1>Monitor de Presión Arterial</h1>
            <div class="graficos">
                <div>
                    <h2>Presión Sistólica</h2>
                    <img src="data:image/png;base64,{{img_sis}}">
                </div>
                <div>
                    <h2>Presión Diastólica</h2>
                    <img src="data:image/png;base64,{{img_dia}}">
                </div>
            </div>
            <div class="tabla">
                <h2>Valores numéricos</h2>
                <table>
                    <tr>
                        <th>Medición</th>
                        <th>Sistólica (mmHg)</th>
                        <th>Diastólica (mmHg)</th>
                    </tr>
                    {% for i in range(72) %}
                    <tr>
                        <td>{{ i+1 }}</td>
                        <td>{{ sistolica[i] }}</td>
                        <td>{{ diastolica[i] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, img_sis=img_sis, img_dia=img_dia, sistolica=sistolica, diastolica=diastolica)

if __name__ == "__main__":
    app.run(debug=True)

