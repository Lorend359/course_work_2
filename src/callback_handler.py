from flask import Flask, Response, make_response, request

app = Flask(__name__)


@app.route("/callback")
def callback() -> Response:
    """
    Обработчик callback для получения authorization code.
    """
    auth_code = request.args.get("code")
    if auth_code:
        return make_response(f"Authorization code received: {auth_code}", 200)
    else:
        return make_response("Authorization code not found!", 400)


if __name__ == "__main__":
    app.run(port=8000)
