import 'package:flutter/material.dart';

import '../models/emergency_contact.dart';

class PersonalContactRow extends StatelessWidget {
  final EmergencyContact contact;
  final bool isEditing;

  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const PersonalContactRow({
    super.key,
    required this.contact,
    required this.isEditing,
    required this.onEdit,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  contact.name,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),

                const SizedBox(height: 3),

                Text(
                  '${contact.relationship} • ${contact.phone}',
                  style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                ),
              ],
            ),
          ),

          if (isEditing)
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  onPressed: onEdit,
                  icon: const Icon(
                    Icons.edit_outlined,
                    size: 19,
                    color: Color(0xFFE53935),
                  ),
                ),

                IconButton(
                  onPressed: onDelete,
                  icon: const Icon(
                    Icons.delete_outline_rounded,
                    size: 20,
                    color: Color(0xFFE53935),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
