import argparse
import io
import flask
from utils.object_detection import load_image_as_np_array, get_predictions
from PIL import Image
app = flask.Flask(__name__)


@app.route('/predict', methods=["POST", "GET"])
def predict():
    response = {}
    if flask.request.method == 'POST':
        try:
            image = flask.request.files["image"].read()
            image = Image.open(io.BytesIO(image))
            img_as_np_arr = load_image_as_np_array(image)
            profiling_on = flask.request.form.get('profiling_on', False) in ('true', 'True', 'TRUE')
            predictions = get_predictions(img_as_np_arr, verbose=True, profiling_on=profiling_on)
            response = {"status": "OK", "success": True, 'predictions': predictions}
        except (OSError, IOError) as e:
            response = {"status": "ERROR", "success": False, 'predictions': None, "message": "Error reading image"}

    elif flask.request.method == "GET":
        response = {"success": False, "message": " please use POST"}
    return flask.jsonify(response)


def main():
    parser = argparse.ArgumentParser(
        description="Starts the development server. Accepts two argument to determine the host ip address and the port"
    )
    parser.add_argument(
        "--host",
        required=False,
        help="The ip address of the host running this server",
        default='0.0.0.0'
    )
    parser.add_argument(
        "--port",
        required=False,
        help="The port the server listens to for incoming connections",
        default='5000'
    )

    args = parser.parse_args()
    app.run(
        host=args.host,
        port=args.port,
    )


if __name__ == '__main__':
    main()
