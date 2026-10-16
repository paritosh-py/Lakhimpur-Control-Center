import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';

class AppBottomNavigation extends StatelessWidget {
  final int currentIndex;
  final VoidCallback onHome;
  final VoidCallback onSOS;
  final VoidCallback onMore;

  const AppBottomNavigation({
    super.key,
    required this.currentIndex,
    required this.onHome,
    required this.onSOS,
    required this.onMore,
  });

  // static const Color _primaryColor = Color(0xFFFF6B35);
  static const Color _sosRed = Color(0xFFE53935);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return SizedBox(
      height: 88,
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.topCenter,
        children: [
          // NAVIGATION BAR
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              height: 68,
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: Colors.grey.shade200)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: _NavItem(
                      icon: Icons.home_rounded,
                      label: l10n.home,
                      isActive: currentIndex == 0,
                      onTap: onHome,
                    ),
                  ),

                  const SizedBox(width: 88),

                  Expanded(
                    child: _NavItem(
                      icon: Icons.grid_view_rounded,
                      label: l10n.more,
                      isActive: currentIndex == 2,
                      onTap: onMore,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // SOS BUTTON
          Positioned(
            top: 0,
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: onSOS,
                borderRadius: BorderRadius.circular(50),
                child: Ink(
                  width: 68,
                  height: 68,
                  decoration: const BoxDecoration(
                    color: _sosRed,
                    shape: BoxShape.circle,
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.sos_rounded, color: Colors.white, size: 27),
                      SizedBox(height: 1),
                      Text(
                        l10n.sos,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.8,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final Color color = isActive
        ? const Color(0xFFFF6B35)
        : Colors.grey.shade500;

    return InkWell(
      onTap: onTap,
      child: SizedBox(
        height: double.infinity,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 23, color: color),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
