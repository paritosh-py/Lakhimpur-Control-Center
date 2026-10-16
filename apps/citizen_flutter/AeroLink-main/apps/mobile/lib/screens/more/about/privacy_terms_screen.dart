import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class PrivacyTermsScreen extends StatelessWidget {
  const PrivacyTermsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: const Color(0xFFF9F9F9),
      body: SafeArea(
        child: Column(
          children: [
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
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.arrow_back_rounded, size: 22),
                    ),
                  ),
                  Text(
                    l10n.privacyAndTerms,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _PolicySection(
                      icon: Icons.privacy_tip_outlined,
                      title: l10n.privacy,
                      content: l10n.privacyBody,
                    ),

                    const SizedBox(height: 16),

                    _PolicySection(
                      icon: Icons.gavel_outlined,
                      title: l10n.termsOfUse,
                      content: l10n.termsBody,
                    ),

                    const SizedBox(height: 16),

                    _PolicySection(
                      icon: Icons.security_outlined,
                      title: l10n.dataAndSecurity,
                      content: l10n.dataSecurityBody,
                    ),

                    const SizedBox(height: 28),

                    Text(
                      l10n.lastUpdated,
                      style: TextStyle(fontSize: 10, color: Colors.grey[500]),
                    ),

                    const SizedBox(height: 12),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PolicySection extends StatelessWidget {
  final IconData icon;
  final String title;
  final String content;

  const _PolicySection({
    required this.icon,
    required this.title,
    required this.content,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(13),
            ),
            child: Icon(icon),
          ),

          const SizedBox(height: 14),

          Text(
            title,
            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
          ),

          const SizedBox(height: 8),

          Text(
            content,
            style: TextStyle(
              fontSize: 12,
              height: 1.6,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }
}
