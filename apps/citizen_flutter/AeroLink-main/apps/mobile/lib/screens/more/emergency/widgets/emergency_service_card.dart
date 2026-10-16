import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

import 'emergency_service_row.dart';

class EmergencyServiceCard extends StatelessWidget {
  const EmergencyServiceCard({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
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
          EmergencyServiceRow(
            title: l10n.police,
            subtitle: l10n.emergencyAssistance,
            number: '112',
            icon: Icons.local_police_outlined,
          ),

          _ServiceDivider(),

          EmergencyServiceRow(
            title: l10n.ambulance,
            subtitle: l10n.medicalEmergency,
            number: '112',
            icon: Icons.local_hospital_outlined,
          ),

          _ServiceDivider(),

          EmergencyServiceRow(
            title: l10n.fireBrigade,
            subtitle: l10n.fireEmergency,
            number: '112',
            icon: Icons.local_fire_department_outlined,
          ),
        ],
      ),
    );
  }
}

class _ServiceDivider extends StatelessWidget {
  const _ServiceDivider();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Divider(height: 1, color: Colors.grey.shade200),
    );
  }
}
