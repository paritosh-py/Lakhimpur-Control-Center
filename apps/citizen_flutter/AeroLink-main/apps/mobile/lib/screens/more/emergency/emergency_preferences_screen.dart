import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

import 'widgets/preference_section.dart';
import 'widgets/preference_row.dart';

class EmergencyPreferencesScreen extends StatefulWidget {
  const EmergencyPreferencesScreen({super.key});

  @override
  State<EmergencyPreferencesScreen> createState() =>
      _EmergencyPreferencesScreenState();
}

class _EmergencyPreferencesScreenState
    extends State<EmergencyPreferencesScreen> {
  bool _shareLiveLocation = true;

  bool _notifyEmergencyContacts = true;

  bool _confirmationBeforeSOS = false;

  bool _loudEmergencyAlert = true;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: const Color(0xFFF9F9F9),

      body: SafeArea(
        child: Column(
          children: [
            // ================= HEADER =================

            Container(
              height: 56,
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
                    l10n.emergencyPreferences,
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 20, 16, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ================= INTRO =================

                    Text(
                      l10n.emergencyPreferencesIntro,
                      style: TextStyle(
                        fontSize: 12,
                        height: 1.5,
                        color: Colors.grey[600],
                      ),
                    ),

                    const SizedBox(height: 26),

                    // ================= ACTIVATION =================
                    PreferenceSection(
                      title: l10n.emergencyActivation,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    l10n.holdToActivate,
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),

                                  const SizedBox(height: 4),

                                  Text(
                                    l10n.preventsAccidentalSos,
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                ],
                              ),
                            ),

                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 7,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE53935)
                                    .withValues(alpha: 0.10),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                l10n.hold,
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w800,
                                  color: Color(0xFFE53935),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 24),

                    // ================= TRANSMISSION =================
                    PreferenceSection(
                      title: l10n.emergencyTransmission,
                      child: Column(
                        children: [
                          PreferenceRow(
                            title: l10n.shareLiveLocation,
                            subtitle: l10n.keepUpdatingLocation,
                            value: _shareLiveLocation,
                            onChanged: (value) {
                              setState(() {
                                _shareLiveLocation = value;
                              });
                            },
                          ),

                          Divider(height: 1, color: Colors.grey.shade200),

                          PreferenceRow(
                            title: l10n.shareEmergencyContacts,
                            subtitle: l10n.shareContactsWithAuthorities,
                            value: _notifyEmergencyContacts,
                            onChanged: (value) {
                              setState(() {
                                _notifyEmergencyContacts = value;
                              });
                            },
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // ================= SAFETY =================
                    PreferenceSection(
                      title: l10n.safety,
                      child: Column(
                        children: [
                          PreferenceRow(
                            title: l10n.confirmationBeforeSos,
                            subtitle: l10n.askBeforeSos,
                            value: _confirmationBeforeSOS,
                            onChanged: (value) {
                              setState(() {
                                _confirmationBeforeSOS = value;
                              });
                            },
                          ),

                          Divider(height: 1, color: Colors.grey.shade200),

                          PreferenceRow(
                            title: l10n.loudEmergencyAlert,
                            subtitle: l10n.playAlertWhenSosStarts,
                            value: _loudEmergencyAlert,
                            onChanged: (value) {
                              setState(() {
                                _loudEmergencyAlert = value;
                              });
                            },
                          ),
                        ],
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
