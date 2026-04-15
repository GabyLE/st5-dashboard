import urllib.request
import json
import base64
import io
import pandas as pd


def call_api(url, method, params, id=1):
    payload = {
        "method": method,
        "params": params,
        "id": id,
        "jsonrpc": "2.0"
    }

    # FORZAMOS A BYTES AQUÍ. Si falla aquí, es que 'payload' no se puede convertir.
    try:
        data_to_send = json.dumps(payload).encode('utf-8')
    except Exception as e:
        raise Exception(f"DEBUG: No puedo convertir el payload a bytes. Tipo de payload: {type(payload)}. Error: {e}")

    req = urllib.request.Request(url, data=data_to_send)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            raw_data = response.read()  # Esto es bytes

            # Intentar decodificar
            try:
                decoded_data = raw_data.decode('utf-8')
                result = json.loads(decoded_data)
            except Exception as e:
                raise Exception(f"DEBUG: No puedo decodificar la respuesta. Respuesta recibida: {raw_data}. Error: {e}")

            if "error" in result and result["error"]:
                raise Exception(f"LimeSurvey API Error: {result['error']}")

            return result.get("result")

    except TypeError as e:
        # ESTE ES EL QUE NOS INTERESA
        raise Exception(
            f"¡ENCONTRADO! TypeError en el código: {e}. Revisa si alguna variable es un dict cuando debería ser bytes.")
    except Exception as e:
        raise Exception(f"Error de conexión: {e}")


def get_responses_df(url, username, password, survey_id):


    # (Login)
    skey = call_api(url, "get_session_key", [username, password])

    try:

        params = [skey, survey_id, "csv", "de", "complete", "code", "short"]
        export_data_base64 = call_api(url, "export_responses", params)

        if export_data_base64:

            csv_text = base64.b64decode(export_data_base64).decode('utf-8')

            return pd.read_csv(io.StringIO(csv_text), sep=";")
        return None

    finally:

        call_api(url, "release_session_key", [skey])