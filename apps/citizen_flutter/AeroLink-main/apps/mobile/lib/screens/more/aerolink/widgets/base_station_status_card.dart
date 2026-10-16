import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

class BaseStationStatusCard extends StatelessWidget {
  final bool isConnected;

  const BaseStationStatusCard({super.key, required this.isConnected});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final Color statusColor = isConnected ? Colors.green : Colors.orange;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: statusColor.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(
              isConnected ? Icons.link_rounded : Icons.link_off_rounded,
              color: statusColor,
            ),
          ),

          const SizedBox(width: 13),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.baseStationStatus,
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),

                const SizedBox(height: 3),

                Text(
                  isConnected
                      ? l10n.stationConnectedReady
                      : l10n.stationDetectedNotConnected,
                  style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                ),
              ],
            ),
          ),

          Container(
            width: 9,
            height: 9,
            decoration: BoxDecoration(
              color: statusColor,
              shape: BoxShape.circle,
            ),
          ),
        ],
      ),
    );
  }
}
