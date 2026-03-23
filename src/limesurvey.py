import urllib.request
import json
import base64
import io
import pandas as pd


def call_api(url, method, params, id=1):

    payload = json.dumps({
        "method": method,
        "params": params,
        "id": id
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get("error"):
                raise Exception(f"LimeSurvey Error: {result['error']}")
            return result["result"]
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