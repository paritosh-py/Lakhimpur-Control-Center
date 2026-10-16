import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

import 'widgets/notification_section.dart';
import 'widgets/notification_toggle.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool _sosUpdates = true;
  bool _weatherAlerts = true;
  bool _nearbyAlerts = true;

  bool _connectionChanges = true;
  bool _deviceStatus = true;
  bool _baseStationUpdates = true;

  bool _soundEnabled = true;
  bool _vibrationEnabled = true;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: Colors.white,

      body: SafeArea(
        child: Column(
          children: [
            // ================= HEADER =================
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.06),
                    blurRadius: 10,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: SizedBox(
                height: 56,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Positioned(
                      left: 8,
                      child: IconButton(
                        onPressed: () {
                          Navigator.pop(context);
                        },
                        icon: const Icon(Icons.arrow_back_rounded, size: 22),
                      ),
                    ),

                    Text(
                      l10n.notifications,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 22, 16, 30),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.notificationsIntro,
                      style: TextStyle(
                        fontSize: 12,
                        height: 1.5,
                        color: Colors.grey[600],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // ================= EMERGENCY =================
                    NotificationSection(
                      title: l10n.emergencyAlerts,
                      children: [
                        NotificationToggle(
                          title: l10n.sosUpdates,
                          subtitle: l10n.sosUpdatesSubtitle,
                          icon: Icons.sos_rounded,
                          value: _sosUpdates,
                          onChanged: (value) {
                            setState(() {
                              _sosUpdates = value;
                            });
                          },
                        ),

                        Divider(
                          height: 1,
                          indent: 16,
                          endIndent: 16,
                          color: Colors.grey.shade200,
                        ),

                        NotificationToggle(
                          title: l10n.weatherAlerts,
                          subtitle: l10n.weatherAlertsSubtitle,
                          icon: Icons.cloud_outlined,
                          value: _weatherAlerts,
                          onChanged: (value) {
                            setState(() {
                              _weatherAlerts = value;
                            });
                          },
                        ),

                        Divider(
                          height: 1,
                          indent: 16,
                          endIndent: 16,
                          color: Colors.grey.shade200,
                        ),

                        NotificationToggle(
                          title: l10n.nearbyAlerts,
                          subtitle: l10n.nearbyAlertsSubtitle,
                          icon: Icons.warning_amber_rounded,
                          value: _nearbyAlerts,
                          onChanged: (value) {
                            setState(() {
                              _nearbyAlerts = value;
                            });
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ================= COMMUNICATION =================
                    NotificationSection(
                      title: l10n.communication,
                      children: [
                        NotificationToggle(
                          title: l10n.connectionChanges,
                          subtitle: l10n.connectionChangesSubtitle,
                          icon: Icons.wifi_rounded,
                          value: _connectionChanges,
                          onChanged: (value) {
                            setState(() {
                              _connectionChanges = value;
                            });
                          },
                        ),

                        Divider(
                          height: 1,
                          indent: 16,
                          endIndent: 16,
                          color: Colors.grey.shade200,
                        ),

                        NotificationToggle(
                          title: l10n.aeroLinkDevice,
                          subtitle: l10n.deviceUpdatesSubtitle,
                          icon: Icons.sensors_rounded,
                          value: _deviceStatus,
                          onChanged: (value) {
                            setState(() {
                              _deviceStatus = value;
                            });
                          },
                        ),

                        Divider(
                          height: 1,
                          indent: 16,
                          endIndent: 16,
                          color: Colors.grey.shade200,
                        ),

                        NotificationToggle(
                          title: l10n.baseStation,
                          subtitle: l10n.stationUpdatesSubtitle,
                          icon: Icons.cell_tower_rounded,
                          value: _baseStationUpdates,
                          onChanged: (value) {
                            setState(() {
                              _baseStationUpdates = value;
                            });
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ================= SOUND =================
                    NotificationSection(
                      title: l10n.alertPreferences,
                      children: [
                        NotificationToggle(
                          title: l10n.sound,
                          subtitle: l10n.soundSubtitle,
                          icon: Icons.volume_up_outlined,
                          value: _soundEnabled,
                          onChanged: (value) {
                            setState(() {
                              _soundEnabled = value;
                            });
                          },
                        ),

                        Divider(
                          height: 1,
                          indent: 16,
                          endIndent: 16,
                          color: Colors.grey.shade200,
                        ),

                        NotificationToggle(
                          title: l10n.vibration,
                          subtitle: l10n.vibrationSubtitle,
                          icon: Icons.vibration_rounded,
                          value: _vibrationEnabled,
                          onChanged: (value) {
                            setState(() {
                              _vibrationEnabled = value;
                            });
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    Text(
                      l10n.criticalAlertsInfo,
                      style: TextStyle(
                        fontSize: 10,
                        height: 1.5,
                        color: Colors.grey[500],
                      ),
                    ),
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
