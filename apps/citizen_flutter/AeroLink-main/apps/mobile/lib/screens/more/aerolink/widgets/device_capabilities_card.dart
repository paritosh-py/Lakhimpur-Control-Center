import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

class DeviceCapabilitiesCard extends StatelessWidget {
  const DeviceCapabilitiesCard({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        children: [
          _CapabilityRow(
            icon: Icons.emergency_rounded,
            title: l10n.emergencyTransmission,
            subtitle: l10n.transmitSosThroughAeroLink,
          ),

          SizedBox(height: 18),

          _CapabilityRow(
            icon: Icons.location_on_outlined,
            title: l10n.locationRelay,
            subtitle: l10n.shareLocationDuringEmergencies,
          ),

          SizedBox(height: 18),

          _CapabilityRow(
            icon: Icons.wifi_tethering_rounded,
            title: l10n.offlineCommunication,
            subtitle: l10n.communicationWithoutInternet,
          ),
        ],
      ),
    );
  }
}

class _CapabilityRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const _CapabilityRow({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: const Color(0xFFE53935).withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(13),
          ),
          child: Icon(icon, color: const Color(0xFFE53935), size: 21),
        ),

        const SizedBox(width: 13),

        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),

              const SizedBox(height: 3),

              Text(
                subtitle,
                style: TextStyle(fontSize: 10, color: Colors.grey),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
