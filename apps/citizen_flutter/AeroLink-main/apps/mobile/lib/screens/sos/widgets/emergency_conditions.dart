import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

enum EmergencyCondition {
  immediateDanger,
  trapped,
  evacuationRequired,
  medicalAssistance,
}

class EmergencyConditions extends StatelessWidget {
  final Set<EmergencyCondition> selectedConditions;
  final ValueChanged<Set<EmergencyCondition>> onChanged;

  const EmergencyConditions({
    super.key,
    required this.selectedConditions,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          l10n.emergencyConditions,
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            color: Colors.black87,
          ),
        ),

        const SizedBox(height: 10),

        Align(
          alignment: Alignment.center,
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _ConditionChip(
                label: l10n.danger,
                condition: EmergencyCondition.immediateDanger,
                selectedConditions: selectedConditions,
                onChanged: onChanged,
              ),

              _ConditionChip(
                label: l10n.trapped,
                condition: EmergencyCondition.trapped,
                selectedConditions: selectedConditions,
                onChanged: onChanged,
              ),

              _ConditionChip(
                label: l10n.evacuate,
                condition: EmergencyCondition.evacuationRequired,
                selectedConditions: selectedConditions,
                onChanged: onChanged,
              ),

              _ConditionChip(
                label: l10n.medical,
                condition: EmergencyCondition.medicalAssistance,
                selectedConditions: selectedConditions,
                onChanged: onChanged,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ConditionChip extends StatelessWidget {
  final String label;
  final EmergencyCondition condition;
  final Set<EmergencyCondition> selectedConditions;
  final ValueChanged<Set<EmergencyCondition>> onChanged;

  const _ConditionChip({
    required this.label,
    required this.condition,
    required this.selectedConditions,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final bool isSelected = selectedConditions.contains(condition);

    return InkWell(
      onTap: () {
        final updated = Set<EmergencyCondition>.from(selectedConditions);

        if (isSelected) {
          updated.remove(condition);
        } else {
          updated.add(condition);
        }

        onChanged(updated);
      },
      borderRadius: BorderRadius.circular(20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFE53935) : Colors.grey.shade50,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFFE53935) : Colors.grey.shade200,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isSelected) ...[
              const Icon(Icons.check_rounded, size: 13, color: Colors.white),
              const SizedBox(width: 4),
            ],

            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: isSelected ? Colors.white : Colors.grey.shade700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
