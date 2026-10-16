@app.route('/trends')
def trends_api_request():
  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

  # Connect to the Trends API.
  trends_service = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  # Define the request parameters.
  start_time = datetime(2024, 12, 1)
  end_time = datetime(2025, 8, 31)
  request = {
      "spec": {
          "expression": {"terms": [{"value": "world cup", "type": "BROAD"}]},
          "geo": {"type": "GEO_TYPE_COUNTRY_OR_REGION", "code": "GB"},
          "timeRange": {
              "startTime": {"seconds": int(start_time.timestamp())},
              "endTime": {"seconds": int(end_time.timestamp())},
          },
          "timeResolution": "MONTH",
      }
  }

  # Send the request to the API.
  fetch_ts_operation = service.v1alpha().fetchTimeSeries(body=request).execute()
  print(json.dumps(fetch_ts_operation, indent=2))

  # Retrieve the results.
  operation_name = "operations/" + fetch_ts_response['name']
  max_attempts = 10
  while max_attempts > 0:
    fetch_ts_response = service.operations().get(name=operation_name).execute()
    if fetch_ts_response['done']:
      break
    time.sleep(1)
    max_attempts -= 1

  if max_attempts == 0:
    print("Operation timed out.")
  else:
    print(json.dumps(fetch_ts_response, indent=2))


  # Save credentials back to session in case access token was refreshed.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  flask.session['credentials'] = credentials_to_dict(credentials)