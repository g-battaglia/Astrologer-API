from app.main import app
import json


with open("openapi.json", "w") as outfile:
    json.dump(app.openapi(), outfile)
