from flask import Flask, render_template, request
import requests
import pandas as pd
import joblib

app = Flask(__name__)

# Function to get 3-hour forecasted weather data from OpenWeather API
def get_forecast_data(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error fetching forecast data: {response.status_code}")
        return None  

# Function to extract weather data for a specific day
def extract_weather_data(forecast_data, day):
    day_index = {'today': 0, 'tomorrow': 8, 'day_after_tomorrow': 16, 'day-4': 24, 'day-5': 32}
    if day not in day_index:
        return None

    index = day_index[day]  # Get index based on the day

    windspeed_m_s = forecast_data['list'][index]['wind']['speed']  # Wind speed in m/s
    windspeed_km_h = windspeed_m_s * 3.6  # Convert wind speed from m/s to km/h

    weather_description = forecast_data['list'][index]['weather'][0]['description']  # Get weather description

    weather_data = {
        'temp': forecast_data['list'][index]['main']['temp'],  # Temperature in Celsius
        'humidity': forecast_data['list'][index]['main']['humidity'],  # Humidity in %
        'sealevelpressure': forecast_data['list'][index]['main']['pressure'],  # Sea-level pressure in hPa
        'windspeed': windspeed_km_h,  # Wind speed in km/h
        'description': weather_description  # Weather description
    }
    return weather_data

# Function to make a rainfall prediction based on weather data
def predict_rainfall(weather_data, model):
    # Check if the description indicates clear or sunny weather
    if 'clear sky' in weather_data['description'].lower() or 'sunny' in weather_data['description'].lower():
        return "No Rain"  # Immediately return No Rain
    
    # Prepare input for model prediction
    X_input = pd.DataFrame([{
        'temp': weather_data['temp'],
        'humidity': weather_data['humidity'],
        'sealevelpressure': weather_data['sealevelpressure'],
        'windspeed': weather_data['windspeed']
    }])
    
    # Get prediction from model
    prediction = model.predict(X_input)
    
    return "Rain" if prediction == 1 else "No Rain"

# Define route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling form submission
@app.route('/Predict', methods=['POST'])
def Predict():
    if request.method == 'POST':
        # Fetch form data
        place = request.form['coordinates']  # This will now contain lat,lng
        date = request.form['date']

        # Error handling for unpacking latitude and longitude
        if place:
            try:
                # Split the place value to get latitude and longitude
                lat, lon = place.split(',')
                
                # Replace with your actual API key
                api_key = "dc57c4b46c6081fa835fbdf62cd2a6e0"
                
                # Load your pre-trained RandomForest model
                rf_model = joblib.load("rf_model.pkl")  # Load the model

                # Fetch weather forecast data
                forecast_data = get_forecast_data(lat, lon, api_key)
                
                if forecast_data:
                    # Extract weather data for the selected day
                    weather_data = extract_weather_data(forecast_data, date)
                    
                    if weather_data:
                        # Predict rainfall
                        rainfall_prediction = predict_rainfall(weather_data, rf_model)
                        return render_template('result.html', place=place, date=date, prediction=rainfall_prediction)
                    else:
                        return "Invalid day input."
                else:
                    return "Error fetching forecast data."
            except ValueError:
                return "Error: The coordinates format is incorrect. Please select a valid place."
        else:
            return "Error: No coordinates provided. Please select a place."

if __name__ == "__main__":
    app.run(debug=True)
