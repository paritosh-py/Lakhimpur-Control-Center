import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

class DeviceStatusCard extends StatelessWidget {
  final bool isConnected;
  final bool isScanning;
  final VoidCallback onConnect;
  final VoidCallback onDisconnect;

  const DeviceStatusCard({
    super.key,
    required this.isConnected,
    required this.isScanning,
    required this.onConnect,
    required this.onDisconnect,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final Color statusColor = isConnected
        ? Colors.green
        : const Color(0xFFE53935);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: statusColor.withValues(alpha: 0.18)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 14,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: statusColor.withValues(alpha: 0.10),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.sensors_rounded, color: statusColor, size: 30),
          ),

          const SizedBox(height: 14),

          Text(
            l10n.aeroLinkDevice,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Colors.black87,
            ),
          ),

          const SizedBox(height: 5),

          Text(
            isScanning
                ? l10n.searchingNearbyDevices
                : isConnected
                ? l10n.connectedAndReady
                : l10n.noDeviceConnected,
            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
          ),

          const SizedBox(height: 18),

          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              onPressed: isScanning
                  ? null
                  : isConnected
                  ? onDisconnect
                  : onConnect,
              style: ElevatedButton.styleFrom(
                elevation: 0,
                backgroundColor: isConnected
                    ? Colors.white
                    : const Color(0xFFE53935),
                foregroundColor: isConnected
                    ? const Color(0xFFE53935)
                    : Colors.white,
                side: isConnected
                    ? const BorderSide(color: Color(0xFFE53935))
                    : BorderSide.none,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(15),
                ),
              ),
              child: isScanning
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(
                      isConnected ? l10n.disconnectDevice : l10n.connectDevice,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
