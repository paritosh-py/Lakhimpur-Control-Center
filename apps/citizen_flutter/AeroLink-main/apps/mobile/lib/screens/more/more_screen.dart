import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../widgets/app_bottom_navigation.dart';

import '../home/home_screen.dart';
import '../sos/sos_screen.dart';

// ================= PROFILE =================
import 'profile/personal_information_screen.dart';

// ================= EMERGENCY =================
import 'emergency/emergency_contacts_screen.dart';
import 'emergency/emergency_preferences_screen.dart';

// ================= AEROLINK =================
import 'aerolink/aerolink_device_screen.dart';
import 'aerolink/base_station_screen.dart';

// ================= PREFERENCES =================
import 'preferences/notifications_screen.dart';
import 'preferences/appearance_screen.dart';

// ================= SUPPORT =================
import 'support/help_support_screen.dart';
import 'about/about_aerolink_screen.dart';

// ================= WIDGETS =================
import 'widgets/more_section.dart';
import 'widgets/more_menu_item.dart';

class MoreScreen extends StatelessWidget {
  const MoreScreen({super.key});

  void _openScreen(BuildContext context, Widget screen) {
    Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
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
                    // BACK BUTTON
                    Positioned(
                      left: 8,
                      child: IconButton(
                        onPressed: () {
                          Navigator.pop(context);
                        },
                        icon: const Icon(Icons.arrow_back_rounded, size: 22),
                      ),
                    ),

                    // CENTER TITLE
                    Center(
                      child: Text(
                        l10n.more,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ================= CONTENT =================
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 12),

                    // ================= PROFILE =================
                    MoreSection(
                      title: l10n.profile,
                      children: [
                        MoreMenuItem(
                          title: l10n.personalInformation,
                          subtitle: l10n.personalInformationSubtitle,
                          onTap: () {
                            _openScreen(
                              context,
                              const PersonalInformationScreen(),
                            );
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ================= EMERGENCY =================
                    MoreSection(
                      title: l10n.emergency,
                      children: [
                        MoreMenuItem(
                          title: l10n.emergencyContacts,
                          subtitle: l10n.emergencyContactsSubtitle,
                          onTap: () {
                            _openScreen(
                              context,
                              const EmergencyContactsScreen(),
                            );
                          },
                        ),

                        MoreMenuItem(
                          title: l10n.emergencyPreferences,
                          subtitle: l10n.emergencyPreferencesSubtitle,
                          onTap: () {
                            _openScreen(
                              context,
                              const EmergencyPreferencesScreen(),
                            );
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ================= AEROLINK =================
                    MoreSection(
                      title: l10n.aeroLink,
                      children: [
                        MoreMenuItem(
                          title: l10n.aeroLinkDevice,
                          subtitle: l10n.aeroLinkDeviceSubtitle,
                          onTap: () {
                            _openScreen(context, const AeroLinkDeviceScreen());
                          },
                        ),

                        MoreMenuItem(
                          title: l10n.baseStation,
                          subtitle: l10n.baseStationSubtitle,
                          onTap: () {
                            _openScreen(context, BaseStationScreen());
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ================= PREFERENCES =================
                    MoreSection(
                      title: l10n.preferences,
                      children: [
                        MoreMenuItem(
                          title: l10n.notifications,
                          subtitle: l10n.notificationsSubtitle,
                          onTap: () {
                            _openScreen(context, const NotificationsScreen());
                          },
                        ),

                        MoreMenuItem(
                          title: l10n.appearance,
                          subtitle: l10n.appearanceSubtitle,
                          onTap: () {
                            _openScreen(context, const AppearanceScreen());
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ================= SUPPORT =================
                    MoreSection(
                      title: l10n.supportAndApp,
                      children: [
                        MoreMenuItem(
                          title: l10n.helpAndSupport,
                          subtitle: l10n.helpAndSupportSubtitle,
                          onTap: () {
                            _openScreen(context, const HelpSupportScreen());
                          },
                        ),

                        MoreMenuItem(
                          title: l10n.aboutAeroLink,
                          subtitle: l10n.aboutAeroLinkSubtitle,
                          onTap: () {
                            _openScreen(context, const AboutAeroLinkScreen());
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),

      // ================= BOTTOM NAVIGATION =================
      bottomNavigationBar: AppBottomNavigation(
        currentIndex: 2,

        onHome: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const HomeScreen()),
          );
        },

        onSOS: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const SOSScreen()),
          );
        },

        onMore: () {
          // Already on More screen.
        },
      ),
    );
  }
}
