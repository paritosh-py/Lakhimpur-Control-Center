import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

import '../models/emergency_contact.dart';
import 'personal_contact_row.dart';

class PersonalContactsCard extends StatelessWidget {
  final List<EmergencyContact> contacts;

  final bool isEditing;

  final VoidCallback onAddContact;

  final Function(int index) onDeleteContact;
  final Function(int index) onEditContact;

  const PersonalContactsCard({
    super.key,
    required this.contacts,
    required this.isEditing,
    required this.onAddContact,
    required this.onEditContact,
    required this.onDeleteContact,
  });

  Widget _divider() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Divider(height: 1, color: Colors.grey.shade200),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
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
        children: [
          if (contacts.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 18),
              child: Text(
                isEditing ? l10n.addContactsBelow : l10n.noPersonalContacts,
                style: TextStyle(fontSize: 12, color: Colors.grey[500]),
              ),
            ),

          ...List.generate(contacts.length, (index) {
            return Column(
              children: [
                PersonalContactRow(
                  contact: contacts[index],
                  isEditing: isEditing,

                  onEdit: () => onEditContact(index),

                  onDelete: () => onDeleteContact(index),
                ),

                if (index != contacts.length - 1) _divider(),
              ],
            );
          }),

          if (isEditing) ...[
            if (contacts.isNotEmpty) _divider(),

            InkWell(
              onTap: onAddContact,
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 13),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.add_rounded,
                      size: 18,
                      color: Color(0xFFE53935),
                    ),

                    const SizedBox(width: 6),

                    Text(
                      l10n.addContact,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFFE53935),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
