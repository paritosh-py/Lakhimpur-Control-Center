import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';

import '../models/emergency_contact.dart';

class AddContactSheet extends StatefulWidget {
  final EmergencyContact? existingContact;

  const AddContactSheet({super.key, this.existingContact});

  @override
  State<AddContactSheet> createState() => _AddContactSheetState();
}

class _AddContactSheetState extends State<AddContactSheet> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _relationshipController = TextEditingController();

  final Color _primaryRed = const Color(0xFFE53935);

  bool get _isEditing => widget.existingContact != null;

  @override
  void initState() {
    super.initState();

    final contact = widget.existingContact;

    if (contact != null) {
      _nameController.text = contact.name;
      _phoneController.text = contact.phone;
      _relationshipController.text = contact.relationship;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _relationshipController.dispose();
    super.dispose();
  }

  void _saveContact() {
    final String name = _nameController.text.trim();
    final String phone = _phoneController.text.trim();
    final String relationship = _relationshipController.text.trim();

    if (name.isEmpty || phone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context)!.requiredContactFields),
        ),
      );
      return;
    }

    Navigator.pop(
      context,
      EmergencyContact(
        name: name,
        phone: phone,
        relationship: relationship.isEmpty
            ? AppLocalizations.of(context)!.emergencyContact
            : relationship,
      ),
    );
  }

  InputDecoration _inputDecoration({
    required String label,
    required String hint,
    required IconData icon,
  }) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      labelStyle: TextStyle(fontSize: 13, color: Colors.grey[700]),
      hintStyle: TextStyle(fontSize: 12, color: Colors.grey[400]),
      prefixIcon: Icon(icon, size: 20, color: Colors.grey[600]),
      filled: true,
      fillColor: const Color(0xFFF8F8F8),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: Colors.grey.shade200),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: Colors.grey.shade200),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: _primaryRed, width: 1.4),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final double keyboardHeight = MediaQuery.of(context).viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.only(bottom: keyboardHeight),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // ================= DRAG HANDLE =================
                Container(
                  width: 42,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),

                const SizedBox(height: 22),

                // ================= HEADER =================
                Row(
                  children: [
                    Container(
                      width: 42,
                      height: 42,
                      decoration: BoxDecoration(
                        color: _primaryRed.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(13),
                      ),
                      child: Icon(
                        _isEditing
                            ? Icons.edit_outlined
                            : Icons.person_add_alt_1_rounded,
                        color: _primaryRed,
                        size: 21,
                      ),
                    ),

                    const SizedBox(width: 12),

                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _isEditing
                                ? l10n.editEmergencyContact
                                : l10n.addEmergencyContact,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                            ),
                          ),

                          const SizedBox(height: 3),

                          Text(
                            _isEditing
                                ? l10n.updateEmergencyContact
                                : l10n.emergencyContactDescription,
                            style: const TextStyle(
                              fontSize: 11,
                              color: Colors.grey,
                            ),
                          ),
                        ],
                      ),
                    ),

                    IconButton(
                      onPressed: () {
                        Navigator.pop(context);
                      },
                      icon: const Icon(Icons.close_rounded, size: 21),
                    ),
                  ],
                ),

                const SizedBox(height: 26),

                // ================= FULL NAME =================
                TextField(
                  controller: _nameController,
                  textCapitalization: TextCapitalization.words,
                  decoration: _inputDecoration(
                    label: l10n.fullName,
                    hint: l10n.enterContactName,
                    icon: Icons.person_outline_rounded,
                  ),
                ),

                const SizedBox(height: 14),

                // ================= RELATIONSHIP =================
                TextField(
                  controller: _relationshipController,
                  textCapitalization: TextCapitalization.words,
                  decoration: _inputDecoration(
                    label: l10n.relationship,
                    hint: l10n.relationshipHint,
                    icon: Icons.people_outline_rounded,
                  ),
                ),

                const SizedBox(height: 14),

                // ================= PHONE =================
                TextField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: _inputDecoration(
                    label: l10n.phoneNumber,
                    hint: l10n.enterPhoneNumber,
                    icon: Icons.phone_outlined,
                  ),
                ),

                const SizedBox(height: 22),

                // ================= SAVE BUTTON =================
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _saveContact,
                    style: ElevatedButton.styleFrom(
                      elevation: 0,
                      backgroundColor: _primaryRed,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: Text(
                      _isEditing ? l10n.saveChanges : l10n.saveContact,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
