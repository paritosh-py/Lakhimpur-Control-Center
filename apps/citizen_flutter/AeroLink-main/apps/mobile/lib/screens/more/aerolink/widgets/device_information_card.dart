import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

class DeviceInformationCard extends StatelessWidget {
  final bool isConnected;

  const DeviceInformationCard({super.key, required this.isConnected});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final String unavailableText = isConnected
        ? l10n.available
        : l10n.notConnected;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        children: [
          _InformationRow(
            title: l10n.deviceId,
            value: isConnected ? 'AER-0001' : '—',
          ),

          Divider(height: 1, color: Colors.grey.shade200),

          _InformationRow(
            title: l10n.firmware,
            value: isConnected ? 'v1.0.0' : '—',
          ),

          Divider(height: 1, color: Colors.grey.shade200),

          _InformationRow(title: l10n.battery, value: unavailableText),
        ],
      ),
    );
  }
}

class _InformationRow extends StatelessWidget {
  final String title;
  final String value;

  const _InformationRow({required this.title, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      child: Row(
        children: [
          Expanded(
            child: Text(
              title,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            ),
          ),

          Text(value, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
        ],
      ),
    );
  }
}
