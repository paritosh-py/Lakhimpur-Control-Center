import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class WeatherAlerts extends StatelessWidget {
  final String temperature;
  final String condition;
  final int weatherCode;
  final String alert;

  final VoidCallback? onMore;
  final VoidCallback? onWeatherTap;

  const WeatherAlerts({
    super.key,
    required this.temperature,
    required this.condition,
    required this.weatherCode,
    required this.alert,
    this.onMore,
    this.onWeatherTap,
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
    if (weatherCode == 0) return Colors.orange;

    if (weatherCode == 1 || weatherCode == 2) {
      return Colors.orange;
    }

    if (weatherCode == 3) return Colors.blueGrey;

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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const SizedBox(width: 8),

            Text(
              l10n.weatherAndAlerts,
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: Colors.black87,
              ),
            ),

            const Spacer(),

            TextButton(
              onPressed: onMore,
              style: TextButton.styleFrom(
                foregroundColor: const Color(0xFFFF6B35),
                padding: const EdgeInsets.symmetric(horizontal: 8),
              ),
              child: Row(
                children: [
                  Text(
                    l10n.more,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 2),
                  const Icon(Icons.arrow_forward_ios_rounded, size: 12),
                ],
              ),
            ),
          ],
        ),

        const SizedBox(height: 1),

        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.grey.shade200),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.06),
                blurRadius: 16,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Column(
            children: [
              Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: onWeatherTap ?? onMore,
                  borderRadius: BorderRadius.circular(16),
                  child: Padding(
                    padding: const EdgeInsets.all(4),
                    child: Row(
                      children: [
                        Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: weatherIconColor.withValues(alpha: 0.10),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(
                            weatherIcon,
                            color: weatherIconColor,
                            size: 28,
                          ),
                        ),

                        const SizedBox(width: 14),

                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              Text(
                                temperature,
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.w700,
                                  color: Colors.black87,
                                ),
                              ),

                              const SizedBox(height: 3),

                              Text(
                                condition,
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        ),

                        Icon(
                          Icons.chevron_right_rounded,
                          color: Colors.grey[400],
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 16),

              Divider(height: 1, color: Colors.grey.shade200),

              const SizedBox(height: 14),

              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: Colors.red.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.warning_rounded,
                      color: Colors.red,
                      size: 28,
                    ),
                  ),

                  const SizedBox(width: 12),

                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l10n.latestAlert,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: Colors.black87,
                          ),
                        ),

                        const SizedBox(height: 4),

                        Text(
                          alert,
                          style: TextStyle(
                            fontSize: 14,
                            height: 1.4,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}
