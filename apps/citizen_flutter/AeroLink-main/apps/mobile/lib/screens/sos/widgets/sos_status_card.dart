import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class SOSStatusCard extends StatelessWidget {
  final Widget? requestContent;
  final bool locationReady;
  final bool transmissionReady;

  const SOSStatusCard({
    super.key,
    this.requestContent,
    required this.locationReady,
    required this.transmissionReady,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Container(
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
      child:
          requestContent ??
          Column(
            children: [
              _StatusRow(
                title: l10n.location,
                subtitle: locationReady
                    ? l10n.locationAvailable
                    : l10n.locationUnavailable,
                isReady: locationReady,
              ),

              _divider(),

              _StatusRow(
                title: l10n.transmission,
                subtitle: transmissionReady
                    ? l10n.transmissionReady
                    : l10n.transmissionNotReady,
                isReady: transmissionReady,
              ),
            ],
          ),
    );
  }

  Widget _divider() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Divider(height: 1, color: Colors.grey.shade200),
    );
  }
}

class _StatusRow extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool isReady;

  const _StatusRow({
    required this.title,
    required this.subtitle,
    required this.isReady,
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
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
        ),

        Text(subtitle, style: TextStyle(fontSize: 10, color: Colors.grey[600])),

        const SizedBox(width: 9),

        Container(
          width: 9,
          height: 9,
          decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
        ),
      ],
    );
  }
}
