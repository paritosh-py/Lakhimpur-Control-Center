import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

import '../../../services/ble_service.dart';

import 'widgets/device_status_card.dart';
import 'widgets/device_information_card.dart';
import 'widgets/device_capabilities_card.dart';

class AeroLinkDeviceScreen extends StatefulWidget {
  const AeroLinkDeviceScreen({super.key});

  @override
  State<AeroLinkDeviceScreen> createState() => _AeroLinkDeviceScreenState();
}

class _AeroLinkDeviceScreenState extends State<AeroLinkDeviceScreen> {
  final BleService _bleService = BleService.instance;

  // ================= CONNECT =================

  Future<void> _connectDevice() async {
    try {
      // Scan for nearby AeroLink BLE devices.
      final devices = await _bleService.scanForAeroLinkDevices();

      if (!mounted) return;

      if (devices.isEmpty) {
        _showMessage(AppLocalizations.of(context)!.noDeviceFound);
        return;
      }

      // Connect to the first AeroLink device found.
      final device = devices.first.device;

      await _bleService.connect(device);

      if (!mounted) return;

      _showMessage(
        AppLocalizations.of(context)!.connectedToDevice(device.platformName),
      );
    } catch (e) {
      if (!mounted) return;

      _showMessage(
        AppLocalizations.of(context)!.connectionFailed(e.toString()),
      );
    }
  }

  // ================= DISCONNECT =================

  Future<void> _disconnectDevice() async {
    try {
      await _bleService.disconnect();

      if (!mounted) return;

      _showMessage(AppLocalizations.of(context)!.deviceDisconnected);
    } catch (e) {
      if (!mounted) return;

      _showMessage(
        AppLocalizations.of(context)!.disconnectFailed(e.toString()),
      );
    }
  }

  // ================= MESSAGE =================

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return ListenableBuilder(
      listenable: _bleService,
      builder: (context, child) {
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
                        l10n.aeroLinkDevice,
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                        ),
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
                        Text(
                          l10n.deviceScreenIntro,
                          style: TextStyle(
                            fontSize: 12,
                            height: 1.5,
                            color: Colors.grey[600],
                          ),
                        ),

                        const SizedBox(height: 22),

                        // ================= DEVICE STATUS =================
                        DeviceStatusCard(
                          isConnected: _bleService.isConnected,
                          isScanning: _bleService.isScanning,
                          onConnect: _connectDevice,
                          onDisconnect: _disconnectDevice,
                        ),

                        const SizedBox(height: 26),

                        // ================= DEVICE INFORMATION =================
                        Text(
                          l10n.deviceInformation,
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),

                        const SizedBox(height: 10),

                        DeviceInformationCard(
                          isConnected: _bleService.isConnected,
                        ),

                        const SizedBox(height: 26),

                        // ================= CAPABILITIES =================
                        Text(
                          l10n.capabilities,
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),

                        const SizedBox(height: 10),

                        const DeviceCapabilitiesCard(),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
