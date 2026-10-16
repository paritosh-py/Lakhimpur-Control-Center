import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class CommunicationReadiness extends StatelessWidget {
  final bool internetReady;
  final bool aeroLinkReady;
  final bool baseStationReady;
  final VoidCallback? onAeroLinkTap;

  const CommunicationReadiness({
    super.key,
    required this.internetReady,
    required this.aeroLinkReady,
    required this.baseStationReady,
    this.onAeroLinkTap,
  });

  @override
  Widget build(BuildContext context) {
    final readyCount = [
      internetReady,
      aeroLinkReady,
      baseStationReady,
    ].where((status) => status).length;

    final bool systemReady = readyCount > 0;
    final l10n = AppLocalizations.of(context)!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              l10n.emergencyReadiness,
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: Colors.black87,
              ),
            ),

            const Spacer(),

            Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
              decoration: BoxDecoration(
                color: systemReady
                    ? Colors.green.withValues(alpha: 0.10)
                    : Colors.red.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                systemReady ? l10n.ready : l10n.offline,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: systemReady ? Colors.green[700] : Colors.red[700],
                ),
              ),
            ),
          ],
        ),

        const SizedBox(height: 12),

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
              _CommunicationRow(
                title: l10n.internet,
                subtitle: internetReady ? l10n.connected : l10n.unavailable,
                isReady: internetReady,
              ),

              _divider(),

              // CLICKABLE AEROLINK DEVICE ROW
              Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: onAeroLinkTap,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      vertical: 8,
                      horizontal: 4,
                    ),
                    child: _CommunicationRow(
                      title: l10n.aeroLinkDevice,
                      subtitle: aeroLinkReady
                          ? l10n.connected
                          : l10n.searchingForDevice,
                      isReady: aeroLinkReady,
                      showArrow: false,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _divider() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Divider(height: 1, color: Colors.grey.shade200),
    );
  }
}

// =================================
// COMMUNICATION STATUS ROW
// =================================

class _CommunicationRow extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool isReady;
  final bool showArrow;

  const _CommunicationRow({
    required this.title,
    required this.subtitle,
    required this.isReady,
    this.showArrow = false,
  });

  @override
  Widget build(BuildContext context) {
    final Color statusColor = isReady ? Colors.green : Colors.orange;

    return Row(
      children: [
        Expanded(
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
        ),

        Text(subtitle, style: TextStyle(fontSize: 12, color: Colors.grey[600])),

        const SizedBox(width: 9),

        Container(
          width: 9,
          height: 9,
          decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
        ),

        if (showArrow) ...[
          const SizedBox(width: 8),
          Icon(Icons.chevron_right_rounded, size: 20, color: Colors.grey[400]),
        ],
      ],
    );
  }
}
