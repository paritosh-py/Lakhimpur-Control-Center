import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class PeopleAffectedSelector extends StatelessWidget {
  final int count;
  final ValueChanged<int> onChanged;

  const PeopleAffectedSelector({
    super.key,
    required this.count,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Row(
      children: [
        // LEFT — HEADER
        Expanded(
          child: Text(
            l10n.peopleAffected,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
        ),

        // RIGHT — NUMBER SELECTOR
        Container(
          height: 40,
          padding: const EdgeInsets.symmetric(horizontal: 4),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _CounterButton(
                icon: Icons.remove_rounded,
                onTap: count > 1 ? () => onChanged(count - 1) : null,
              ),

              SizedBox(
                width: 32,
                child: Text(
                  '$count',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: Colors.black87,
                  ),
                ),
              ),

              _CounterButton(
                icon: Icons.add_rounded,
                onTap: () => onChanged(count + 1),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CounterButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onTap;

  const _CounterButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final bool enabled = onTap != null;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: SizedBox(
        width: 32,
        height: 32,
        child: Icon(
          icon,
          size: 18,
          color: enabled ? Colors.black87 : Colors.grey.shade300,
        ),
      ),
    );
  }
}
