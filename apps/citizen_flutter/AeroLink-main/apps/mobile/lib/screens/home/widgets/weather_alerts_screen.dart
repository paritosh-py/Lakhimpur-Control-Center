import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class WeatherAlertsScreen extends StatelessWidget {
  final String temperature;
  final String condition;
  final int weatherCode;

  const WeatherAlertsScreen({
    super.key,
    required this.temperature,
    required this.condition,
    required this.weatherCode,
  });

  IconData _getWeatherIcon() {
    if (weatherCode == 0) {
      return Icons.wb_sunny_rounded;
    }

    if (weatherCode == 1 || weatherCode == 2) {
      return Icons.wb_cloudy_rounded;
    }

    if (weatherCode == 3) {
      return Icons.cloud_rounded;
    }

    if (weatherCode == 45 || weatherCode == 48) {
      return Icons.foggy;
    }

    if ((weatherCode >= 51 && weatherCode <= 67) ||
        (weatherCode >= 80 && weatherCode <= 82)) {
      return Icons.grain_rounded;
    }

    if (weatherCode >= 71 && weatherCode <= 77) {
      return Icons.ac_unit_rounded;
    }

    if (weatherCode == 85 || weatherCode == 86) {
      return Icons.cloudy_snowing;
    }

    if (weatherCode >= 95 && weatherCode <= 99) {
      return Icons.thunderstorm_rounded;
    }

    return Icons.cloud_outlined;
  }

  Color _getWeatherIconColor() {
    if (weatherCode == 0) {
      return Colors.orange;
    }

    if (weatherCode == 1 || weatherCode == 2) {
      return Colors.orange;
    }

    if (weatherCode == 3) {
      return Colors.blueGrey;
    }

    if (weatherCode == 45 || weatherCode == 48) {
      return Colors.grey;
    }

    if ((weatherCode >= 51 && weatherCode <= 67) ||
        (weatherCode >= 80 && weatherCode <= 82)) {
      return Colors.blue;
    }

    if (weatherCode >= 71 && weatherCode <= 86) {
      return Colors.lightBlue;
    }

    if (weatherCode >= 95 && weatherCode <= 99) {
      return Colors.deepPurple;
    }

    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final weatherIcon = _getWeatherIcon();
    final weatherIconColor = _getWeatherIconColor();

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FB),
      body: SafeArea(
        child: Column(
          children: [
            // HEADER
            Container(
              height: 60,
              width: double.infinity,
              color: Colors.white,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Positioned(
                    left: 4,
                    child: IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(
                        Icons.arrow_back_rounded,
                        color: Color(0xFF1A2A3A),
                      ),
                    ),
                  ),

                  Text(
                    l10n.weatherAndAlerts,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF1A2A3A),
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // WEATHER SUMMARY
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.grey.shade200),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.04),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 52,
                            height: 52,
                            decoration: BoxDecoration(
                              color: weatherIconColor.withValues(alpha: 0.10),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Icon(
                              weatherIcon,
                              color: weatherIconColor,
                              size: 30,
                            ),
                          ),

                          const SizedBox(width: 16),

                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  temperature,
                                  style: const TextStyle(
                                    fontSize: 24,
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF1A2A3A),
                                  ),
                                ),

                                const SizedBox(height: 4),

                                Text(
                                  condition,
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 28),

                    // ALERTS HEADER
                    Text(
                      l10n.emergencyAlerts,
                      style: TextStyle(
                        fontSize: 19,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF1A2A3A),
                      ),
                    ),

                    const SizedBox(height: 5),

                    Text(
                      l10n.alertsForCurrentLocation,
                      style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                    ),

                    const SizedBox(height: 16),

                    // CURRENT STATUS
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: Colors.green.withValues(alpha: 0.25),
                        ),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.check_circle_rounded,
                            color: Colors.green,
                            size: 28,
                          ),

                          SizedBox(width: 14),

                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  l10n.noActiveAlerts,
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF1A2A3A),
                                  ),
                                ),

                                SizedBox(height: 5),

                                Text(
                                  l10n.noEmergencyAlerts,
                                  style: TextStyle(
                                    fontSize: 13,
                                    height: 1.4,
                                    color: Colors.black54,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // MONITORING STATUS
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFF6B35).withValues(alpha: 0.07),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.radar_rounded, color: Color(0xFFFF6B35)),

                          SizedBox(width: 12),

                          Expanded(
                            child: Text(
                              l10n.alertMonitoringInfo,
                              style: TextStyle(
                                fontSize: 13,
                                height: 1.4,
                                color: Color(0xFF1A2A3A),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 30),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
