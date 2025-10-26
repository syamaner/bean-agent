# Overview

In Phase 1 we have fine tuned an ASR model to detect first crack and implemented ingestion as well as inference pipeline and achieved 93% test accuracy.

Relevant files are:
 - [Phase 1 summary](../../PHASE1_COMPLETE.md) 
 - [Phase 1 plan](../../PHASE1_PLAN.md) 
 - And overall requirements was in the [Readme](../../README.md) file.

## Phase 2 Objectives:

### Objective 1 - Wrap Inference pipeline as an MCP Server ✅ COMPLETE

- Build an MCP server that will wrap the inference pipeline as a long running process.
  - We already have the [inference pipeline](../../src/inference/first_crack_detector.py) supporting our requirements.
    - Before building the server understand how this class works.
    - Although MCP server is stateless, this class need to start once and then same instance is reused for each requests.
    - Idempotency is important
      - Calling start multiple times will return same response but if it is running already, it will not alter the state.
  - Start monitoring and inference.
    - We can pass a pre recorded audio or microphone
      - Microphone should support external usb microphone we used for recordings.
  - Get stats:
    - Should be either First Crack detected or first crack not detected.
    - If first crack detected, the time stamp should also be returned
      - Currently the timestamp is relative to starting monitoring:
        - I think we should also add a second timestamp for actual time in local time zone.
  - Stop the pipeline
  - We should use AUTH 0 for the authorisation and the agent we will build at phase-3 will use Auth0 for authentication to access the MCP server with user tokens.
    - Some documentation links: 
      - https://auth0.com/blog/an-introduction-to-mcp-and-authorization/
      - https://auth0.com/docs/get-started/auth0-mcp-server
      - [PDF Manual for the roaster](../../docs/KN-8828B-2K+Manual_0_1g.pdf)
    - Our MCP server will mainly worry about a valid token and ensuring the token has necessary scopes for the required tool call
    - We have 2 roles:
      - Roast Admin role: this allows full access to all tools.
      - Roast Observer role: This allows calling is_first_crack tool.

### Objective 2 - Build an MCP tool to control Hottop Roaster ✅ COMPLETE

- Relevant links:
  - [Hottop KN8828B-2K+ product page](https://www.hottopamericas.com/KN-8828B-2Kplus.html)
  - [Hottop python client library - pyhottop](https://github.com/splitkeycoffee/pyhottop)
- Roaster controls:
  - Increase / decrease heat: 10% steps +/-
  - Increase / decrease fan speed: 10% steps +/-
  - Open bean drop door
  - Start / stop cooling fan
  - Start stop roaster control (the drum starts running or stops)
- Roaster sensors:
  - Read chamber temperature
  - Read bean temperature
- Maintain roast status data:
  - Rate of rise
    - Delta bean temperature in the last 60 seconds. Temp at T - Temp at T-60 secs)
    - Roast timer
      - From the point beans are added to the point beans dropped.
      - The timer only starts when beans are added not when the roaster is turned on and heat applied.
      - Usually beans will be added at a certain bean temperature. On this machine around 170 degrees C works well.
      - The tool will detect the sudden drop in bran temperature (if we add at 170 degrees, suddenly ban temperature will drop)
      - The moment drop happens is T0.
    - Temperature at which beans were added will be captured and reported.
    - First crack happened.
      - The agent will be using our previously built first crack detector and once detected, will tell the roaster MCP first crack happened.
      - Temperature at which first crack happened will also be reported on.
    - Development time.
      - Development time is the duration between first crack start and roast end (bean drop) moment.
      - There should also be a percentage as our agent will make a call when development time % is around 15% to stop the roast or not. 
        - There are other parameters for it so MCP server does not need to worry.
    - Drop time and temperature
    - Total roast duration

Tools exposed will be:
- Manage the roaster using roaster controls
  - If we expose a single control tool with input arguments or multiple tools will be decided as we refine the requirements together.
- Get status
  - Includes all the data described above happened at the time of request. It is ok for payload to be repetitive.
  - Sensors, derived values all will be included.
  - Timestamps also will be included when certain events described above.

Authorisation
  - We should use AUTH 0 for the authorisation and the agent we will build at phase-3 will use Auth0 for authentication to access the MCP server with user tokens.
    - Some documentation links: 
      - https://auth0.com/blog/an-introduction-to-mcp-and-authorization/
      - https://auth0.com/docs/get-started/auth0-mcp-server
      - [PDF Manual for the roaster](../../docs/KN-8828B-2K+Manual_0_1g.pdf)
    - Our MCP server will mainly worry about a valid token and ensuring the token has necessary scopes for the required tool call
    - We have 2 roles:
      - Roast Admin role: this allows full access to all tools.
      - Roast Observer role: This allows get status and all sensor data readonly

