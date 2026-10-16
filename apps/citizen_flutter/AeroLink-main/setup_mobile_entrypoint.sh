#!/usr/bin/env bash
set -euo pipefail

# AeroLink Mobile Entry-Point Bootstrap
#
# Run this script from the ROOT of the AeroLink monorepo.
# It preserves the existing structure and ONLY creates/replaces:
#
#   apps/mobile/lib/main.dart
#   apps/mobile/lib/app.dart
#   apps/mobile/lib/features/home/home_screen.dart
#   apps/mobile/lib/features/sos/sos_screen.dart
#
# Usage:
#   bash setup_mobile_entrypoint.sh

ROOT="$(pwd)"
MOBILE_DIR="$ROOT/apps/mobile"
LIB_DIR="$MOBILE_DIR/lib"

echo "============================================================"
echo " AeroLink Mobile Entry-Point Setup"
echo "============================================================"
echo

if [[ ! -d "$MOBILE_DIR" ]]; then
  echo "ERROR: Expected directory not found:"
  echo "  $MOBILE_DIR"
  echo "Run this script from the AeroLink repository root."
  exit 1
fi

if [[ ! -f "$MOBILE_DIR/pubspec.yaml" ]]; then
  echo "ERROR: pubspec.yaml not found:"
  echo "  $MOBILE_DIR/pubspec.yaml"
  exit 1
fi

mkdir -p "$LIB_DIR/features/home"
mkdir -p "$LIB_DIR/features/sos"

cat > "$LIB_DIR/main.dart" <<'DART'
import 'package:flutter/material.dart';

import 'app.dart';

void main() {
  runApp(const AeroLinkApp());
}
DART

cat > "$LIB_DIR/app.dart" <<'DART'
import 'package:flutter/material.dart';

import 'features/home/home_screen.dart';

class AeroLinkApp extends StatelessWidget {
  const AeroLinkApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AeroLink',
      debugShowCheckedModeBanner: false,
      home: const HomeScreen(),
    );
  }
}
DART

cat > "$LIB_DIR/features/home/home_screen.dart" <<'DART'
import 'package:flutter/material.dart';

import '../sos/sos_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AeroLink'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Communication Readiness',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            const ListTile(
              title: Text('Internet'),
              trailing: Text('Online'),
            ),
            const ListTile(
              title: Text('AeroLink Node'),
              trailing: Text('Unknown'),
            ),
            const ListTile(
              title: Text('Reliability Zone'),
              trailing: Text('Unmeasured'),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const SosScreen(),
                  ),
                );
              },
              child: const Text('EMERGENCY SOS'),
            ),
            const SizedBox(height: 20),
            const Text(
              'Active Alerts',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text('No active warnings'),
          ],
        ),
      ),
    );
  }
}
DART

cat > "$LIB_DIR/features/sos/sos_screen.dart" <<'DART'
import 'package:flutter/material.dart';

enum SosStatus {
  idle,
  sending,
  transmitting,
  retrying,
  acknowledged,
  failed,
}

class SosScreen extends StatefulWidget {
  const SosScreen({super.key});

  @override
  State<SosScreen> createState() => _SosScreenState();
}

class _SosScreenState extends State<SosScreen> {
  String incidentType = 'Medical';
  double severity = 3;

  final TextEditingController _peopleController = TextEditingController();
  final TextEditingController _messageController = TextEditingController();

  SosStatus status = SosStatus.idle;

  @override
  void dispose() {
    _peopleController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> sendSos() async {
    setState(() {
      status = SosStatus.sending;
    });

    await Future.delayed(
      const Duration(seconds: 2),
    );

    if (!mounted) return;

    setState(() {
      status = SosStatus.transmitting;
    });

    await Future.delayed(
      const Duration(seconds: 2),
    );

    if (!mounted) return;

    setState(() {
      status = SosStatus.acknowledged;
    });
  }

  String getStatusText() {
    switch (status) {
      case SosStatus.idle:
        return 'Ready to send SOS';
      case SosStatus.sending:
        return 'Sending SOS...';
      case SosStatus.transmitting:
        return 'Transmitting to AeroLink node...';
      case SosStatus.retrying:
        return 'Retrying...';
      case SosStatus.acknowledged:
        return 'SOS Acknowledged';
      case SosStatus.failed:
        return 'Delivery Not Confirmed';
    }
  }

  bool get isSending {
    return status == SosStatus.sending ||
        status == SosStatus.transmitting ||
        status == SosStatus.retrying;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency SOS'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DropdownButtonFormField<String>(
                initialValue: incidentType,
                decoration: const InputDecoration(
                  labelText: 'Incident Type',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(
                    value: 'Flood',
                    child: Text('Flood'),
                  ),
                  DropdownMenuItem(
                    value: 'Fire',
                    child: Text('Fire'),
                  ),
                  DropdownMenuItem(
                    value: 'Medical',
                    child: Text('Medical'),
                  ),
                  DropdownMenuItem(
                    value: 'Trapped',
                    child: Text('Trapped'),
                  ),
                  DropdownMenuItem(
                    value: 'Food/Water',
                    child: Text('Food / Water'),
                  ),
                  DropdownMenuItem(
                    value: 'Other',
                    child: Text('Other'),
                  ),
                ],
                onChanged: isSending
                    ? null
                    : (value) {
                        if (value == null) return;

                        setState(() {
                          incidentType = value;
                        });
                      },
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _peopleController,
                enabled: !isSending,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'People Affected',
                  hintText: 'Example: 3',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Severity: ${severity.toInt()}',
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                ),
              ),
              Slider(
                min: 1,
                max: 5,
                divisions: 4,
                label: severity.toInt().toString(),
                value: severity,
                onChanged: isSending
                    ? null
                    : (value) {
                        setState(() {
                          severity = value;
                        });
                      },
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _messageController,
                enabled: !isSending,
                maxLength: 32,
                decoration: const InputDecoration(
                  labelText: 'Optional Message',
                  hintText: 'Short clarification',
                  border: OutlineInputBorder(),
                ),
              ),
              const Spacer(),
              Text(
                getStatusText(),
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: status == SosStatus.acknowledged
                      ? Colors.green
                      : status == SosStatus.failed
                          ? Colors.red
                          : null,
                ),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: isSending ? null : sendSos,
                  child: Text(
                    isSending ? 'SENDING...' : 'SEND SOS',
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
DART

echo
echo "Updated:"
echo "  apps/mobile/lib/main.dart"
echo "  apps/mobile/lib/app.dart"
echo "  apps/mobile/lib/features/home/home_screen.dart"
echo "  apps/mobile/lib/features/sos/sos_screen.dart"

cd "$MOBILE_DIR"

if command -v dart >/dev/null 2>&1; then
  echo
  echo "Formatting updated Dart files..."
  dart format     lib/main.dart     lib/app.dart     lib/features/home/home_screen.dart     lib/features/sos/sos_screen.dart
fi

if command -v flutter >/dev/null 2>&1; then
  echo
  echo "Running flutter pub get..."
  flutter pub get

  echo
  echo "Running flutter analyze..."
  flutter analyze
fi

echo
echo "============================================================"
echo " Setup complete"
echo "============================================================"
echo
echo "Expected app flow:"
echo "  Home -> EMERGENCY SOS -> SEND SOS"
echo "  Ready -> Sending -> Transmitting -> SOS Acknowledged"
