import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class AdditionalDetails extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onVoicePressed;

  const AdditionalDetails({
    super.key,
    required this.controller,
    required this.onVoicePressed,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          l10n.additionalDetails,
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
        ),

        const SizedBox(height: 10),

        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Stack(
            children: [
              TextField(
                controller: controller,
                minLines: 1,
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: l10n.describeEmergency,
                  hintStyle: TextStyle(fontSize: 12, color: Colors.grey[500]),
                  border: InputBorder.none,

                  // Keeps space for the voice clip.
                  contentPadding: const EdgeInsets.fromLTRB(16, 16, 16, 52),
                ),
              ),

              // VOICE CLIP — BOTTOM RIGHT
              Positioned(
                right: 10,
                bottom: 10,
                child: InkWell(
                  onTap: onVoicePressed,
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 7,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE53935).withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.mic_none_rounded,
                          size: 16,
                          color: Color(0xFFE53935),
                        ),
                        SizedBox(width: 5),
                        Text(
                          l10n.voice,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFFE53935),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 7),

        Text(
          l10n.youCanTypeOrUseVoiceInput,
          style: TextStyle(fontSize: 10, color: Colors.grey[500]),
        ),
      ],
    );
  }
}
