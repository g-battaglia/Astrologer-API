from app.main import app
import json

# with open("openapi.json", "w") as outfile:
#     json.dump(app.openapi(), outfile)

def dump_schema(output_file_path):
    BASE_URL = "https://astrologer.p.rapidapi.com/"
    RAPIDAPI_HOST = "astrologer.p.rapidapi.com" 
    openapi_data = app.openapi()

    # Define the rapidapi authentication headers
    rapidapi_auth = {
        "type": "apiKey",
        "name": "x-rapidapi-key",
        "in": "header"
    }

    # Add RapidAPI authentication to the securityDefinitions or components/securitySchemes
    if 'swagger' in openapi_data:  # Swagger 2.0
        openapi_data.setdefault('securityDefinitions', {})
        openapi_data['securityDefinitions']['RapidAPIKey'] = rapidapi_auth
    elif 'openapi' in openapi_data:  # OpenAPI 3.0+
        openapi_data.setdefault('components', {}).setdefault('securitySchemes', {})
        openapi_data['components']['securitySchemes']['RapidAPIKey'] = rapidapi_auth
    else:
        raise ValueError("Unrecognized OpenAPI version")

    # Apply the security scheme globally or to individual paths
    security_requirement = [{"RapidAPIKey": []}]
    
    # Add the security requirement to the paths
    if 'swagger' in openapi_data:  # Swagger 2.0
        for path in openapi_data.get('paths', {}).values():
            for method in path.values():
                method['security'] = security_requirement
    elif 'openapi' in openapi_data:  # OpenAPI 3.0+
        for path in openapi_data.get('paths', {}).values():
            for method in path.values():
                if isinstance(method, dict):  # Ensure we're modifying the correct level
                    method['security'] = security_requirement

    # Add the headers and hardcoded host/base URL to each path's operation
    for path, methods in openapi_data.get('paths', {}).items():
        for method, details in methods.items():
            if isinstance(details, dict):  # Ensure we're modifying the correct level
                details.setdefault('parameters', [])
                
                # Add x-rapidapi-key header
                details['parameters'].append({
                    "name": "x-rapidapi-key",
                    "in": "header",
                    "required": True,
                    "schema": {
                        "type": "string",
                        "example": "<YOUR_RAPIDAPI_KEY>"
                    }
                })
                
                # Hardcode x-rapidapi-host header
                details['parameters'].append({
                    "name": "x-rapidapi-host",
                    "in": "header",
                    "required": True,
                    "schema": {
                        "type": "string",
                        "example": RAPIDAPI_HOST
                    }
                })

                # Prepend base URL to all endpoints
                if 'servers' not in openapi_data:
                    openapi_data['servers'] = [{"url": BASE_URL}]
                else:
                    for server in openapi_data['servers']:
                        server['url'] = BASE_URL

    # Save the modified OpenAPI JSON file
    with open(output_file_path, 'w') as file:
        json.dump(openapi_data, file, indent=2)


if __name__ == "__main__":
    # https://editor-next.swagger.io/
    dump_schema("openapi.json")
    print("OpenAPI JSON file generated successfully! Check it here: https://editor-next.swagger.io/")