# FinCompass Plugin

FinCompass is a plugin for AetherOnePy that allows you to automatically create a case, session, and run an analysis in a single API call. The results are returned directly to you, making the process fast and seamless.

## Features
- **Automatic Analysis**: Create a case, session, and run an analysis with one API call.
- **Catalog Selection**: Choose which catalog item to use for your analysis.
- **Results Returned Instantly**: Get the analysis results in the same response.
- **Case Tracking**: All cases created through FinCompass are tracked locally for your reference.

---

## 🚀 Coming Soon: One-Click Full Analysis & Schedule Flow

FinCompass will soon support a fully automated, one-click workflow for market analysis and scheduling trades. This will streamline the entire process into a single action for the user.

### **Planned One-Click Workflow**

1. **Select Intention**
   - User selects an intention (e.g., "Buy BTC when signal is strong").
2. **Select Case**
   - User selects a case (or creates a new one).
3. **Click 'Run Full Analysis & Schedule'**
   - The system will:
     1. **Create a new session** for the selected case/intention.
     2. **Sync provider rates** (symbols) from the selected provider.
     3. **Select the appropriate catalog** (e.g., "mexc").
     4. **Run analysis** for the session and catalog.
     5. **Determine the highest rate** (symbol) from the analysis results.
     6. **Prompt the user for buy/sell times** (or use sensible defaults).
     7. **Post a schedule** to the remote server (e.g., fincompass.emolio.com) with all required data:
        - Intention
        - Symbol (highest rate)
        - Buy/Sell times
        - Case/session IDs, etc.
     8. **Show success/failure feedback** in the UI.

### **Benefits**
- No more manual step-by-step clicking—just select your intention/case and go!
- Ensures all data is in sync and valid before scheduling.
- Reduces errors and saves time for power users.

---

## How It Works (Current)
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


AetherOne protocol
1. get rates from server
2. add it to rates
3. add id of rates
4. make session (intention)
5. analyze
6. get analyse like what coin to buy


frontend: 

Share on AetherOnePySocial
1. make or share key
2. send analyse
3. get key

FinCompass protocol
1. select provider_id
2. make schedule to buy with above key
and get id back so we can use that id for selling and make selling schedule


1 select intention add to "http://localhost:7000/session" with 
{"id":0,"caseID":2,"intention":"ttt","description":"ttt","created":"2025-06-23T12:05:48.127Z"}
getting back
{
    "id": 5,
    "intention": "ttt",
    "description": "ttt",
    "created": "2025-06-23T14:05:48.132456",
    "caseID": 2
}

2. select provider and set it in database as provider_id name and selected

check if provider is selected, if not give link to providers to click on select

3. now make a function that gets the symbols from server and we are going to add it to rates
same for this we need to select it....we need caltalog_id



2 select provider and get rates import to website
3. hit analyse

## What Happens When You Click "Start Magic"?

When you click the Start Magic button, the following happens (all in one backend call):

1. The backend creates a new session and analysis for your selected intention, case, and catalog.
2. It runs the analysis and finds the most profitable symbol.
3. It calculates buy/sell times using your intention's hold period.
4. It sends a schedule to the remote server (for buy/sell) and saves the schedule locally.
5. You get instant feedback and schedule IDs in the UI.

All of this is triggered by a single call to `/fincompass/api/start-magic`.


