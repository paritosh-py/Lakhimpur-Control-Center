import 'dart:convert';

import 'package:http/http.dart' as http;

class WeatherData {
  final double temperature;
  final int weatherCode;
  final String condition;

  const WeatherData({
    required this.temperature,
    required this.weatherCode,
    required this.condition,
  });
}

class WeatherService {
  Future<WeatherData> getCurrentWeather({
    required double latitude,
    required double longitude,
  }) async {
    final Uri url = Uri.parse(
      'https://api.open-meteo.com/v1/forecast'
      '?latitude=$latitude'
      '&longitude=$longitude'
      '&current=temperature_2m,weather_code'
      '&forecast_days=1',
    );

    final response = await http.get(url);

    if (response.statusCode != 200) {
      throw Exception(
        'Unable to fetch weather data. '
        'Status code: ${response.statusCode}',
      );
    }

    final Map<String, dynamic> data = jsonDecode(response.body);

    final Map<String, dynamic> current =
        data['current'] as Map<String, dynamic>;

    final double temperature = (current['temperature_2m'] as num).toDouble();

    final int weatherCode = (current['weather_code'] as num).toInt();

    return WeatherData(
      temperature: temperature,
      weatherCode: weatherCode,
      condition: _getWeatherCondition(weatherCode),
    );
  }

  String _getWeatherCondition(int code) {
    switch (code) {
      case 0:
        return 'Clear sky';

      case 1:
        return 'Mainly clear';

      case 2:
        return 'Partly cloudy';

      case 3:
        return 'Overcast';

      case 45:
      case 48:
        return 'Foggy';

      case 51:
        return 'Light drizzle';

      case 53:
        return 'Moderate drizzle';

      case 55:
        return 'Heavy drizzle';

      case 56:
        return 'Light freezing drizzle';

      case 57:
        return 'Heavy freezing drizzle';

      case 61:
        return 'Light rain';

      case 63:
        return 'Moderate rain';

      case 65:
        return 'Heavy rain';

      case 66:
        return 'Light freezing rain';

      case 67:
        return 'Heavy freezing rain';

      case 71:
        return 'Light snowfall';

      case 73:
        return 'Moderate snowfall';

      case 75:
        return 'Heavy snowfall';

      case 77:
        return 'Snow grains';

      case 80:
        return 'Light rain showers';

      case 81:
        return 'Moderate rain showers';

      case 82:
        return 'Heavy rain showers';

      case 85:
        return 'Light snow showers';

      case 86:
        return 'Heavy snow showers';

      case 95:
        return 'Thunderstorm';

      case 96:
        return 'Thunderstorm with light hail';

      case 99:
        return 'Thunderstorm with heavy hail';

      default:
        return 'Unknown weather';
    }
  }
}
