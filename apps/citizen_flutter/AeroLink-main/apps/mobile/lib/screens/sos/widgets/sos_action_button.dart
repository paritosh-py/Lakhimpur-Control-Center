import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

class SOSActionButton extends StatelessWidget {
  final VoidCallback onActivate;

  const SOSActionButton({super.key, required this.onActivate});

  static const Color _sosRed = Color(0xFFE53935);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return SizedBox(
      width: double.infinity,
      height: 58,
      child: ElevatedButton(
        onPressed: onActivate,
        style: ElevatedButton.styleFrom(
          backgroundColor: _sosRed,
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.warning_rounded, size: 21),

            SizedBox(width: 9),

            Text(
              l10n.holdToSendSos,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.7,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
