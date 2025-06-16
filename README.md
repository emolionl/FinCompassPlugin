# FinCompass Plugin

FinCompass is a plugin for AetherOnePy that allows you to automatically create a case, session, and run an analysis in a single API call. The results are returned directly to you, making the process fast and seamless.

## Features
- **Automatic Analysis**: Create a case, session, and run an analysis with one API call.
- **Catalog Selection**: Choose which catalog item to use for your analysis.
- **Results Returned Instantly**: Get the analysis results in the same response.
- **Case Tracking**: All cases created through FinCompass are tracked locally for your reference.

## How It Works
1. **Send a POST request to `/fincompass/analyze-complete`**
   - Provide the case details, session details, and the catalog ID you want to analyze.
   - Example request body:
     ```json
     {
       "case": {
         "name": "My Analysis Case"
       },
       "session": {
         "description": "Initial session",
         "intention": "Analyze market trends"
       },
       "catalogId": 1,
       "note": "Optional note for the analysis"
     }
     ```
   - The plugin will:
     - Create the case in AetherOnePy
     - Create a session
     - Run the analysis for the selected catalog
     - Return all results in the response

2. **Get All Cases**
   - Send a GET request to `/fincompass/cases` to see all cases created through FinCompass.

3. **Health Check**
   - Send a GET request to `/fincompass/ping` to check if the plugin is running.

## Example Response
```json
{
  "status": "success",
  "case": { ... },
  "session": { ... },
  "analysis": { ... },
  "results": [ ... ]
}
```

## Postman Collection
A ready-to-use Postman collection is available in `FinCompass_endpoints.json` for easy testing of all endpoints.

## Swagger/OpenAPI Docs
Interactive API documentation is available at `/apidocs` when the server is running.

---

**FinCompass** makes it easy to automate and streamline your analysis workflow in AetherOnePy! 