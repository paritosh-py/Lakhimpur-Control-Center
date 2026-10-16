import 'package:flutter/material.dart';

import 'people_affected_selector.dart';
import 'emergency_conditions.dart';

class SOSInformationCard extends StatelessWidget {
  final int peopleAffected;
  final ValueChanged<int> onPeopleAffectedChanged;

  final Set<EmergencyCondition> selectedConditions;
  final ValueChanged<Set<EmergencyCondition>> onConditionsChanged;

  const SOSInformationCard({
    super.key,
    required this.peopleAffected,
    required this.onPeopleAffectedChanged,
    required this.selectedConditions,
    required this.onConditionsChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PeopleAffectedSelector(
            count: peopleAffected,
            onChanged: onPeopleAffectedChanged,
          ),

          _divider(),

          EmergencyConditions(
            selectedConditions: selectedConditions,
            onChanged: onConditionsChanged,
          ),
        ],
      ),
    );
  }

  Widget _divider() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Divider(height: 1, color: Colors.grey.shade200),
    );
  }
}
