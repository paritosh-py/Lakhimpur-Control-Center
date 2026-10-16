import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

import 'models/emergency_contact.dart';
import 'services/emergency_contact_service.dart';

import 'widgets/personal_contacts_card.dart';
import 'widgets/add_contact_sheet.dart';
import 'widgets/emergency_service_card.dart';

class EmergencyContactsScreen extends StatefulWidget {
  const EmergencyContactsScreen({super.key});

  @override
  State<EmergencyContactsScreen> createState() =>
      _EmergencyContactsScreenState();
}

class _EmergencyContactsScreenState extends State<EmergencyContactsScreen> {
  final EmergencyContactService _contactService = EmergencyContactService();

  List<EmergencyContact> _contacts = [];

  bool _isEditing = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadContacts();
  }

  Future<void> _loadContacts() async {
    final contacts = await _contactService.loadContacts();

    if (!mounted) return;

    setState(() {
      _contacts = contacts;
      _isLoading = false;
    });
  }

  Future<void> _saveContacts() async {
    await _contactService.saveContacts(_contacts);
  }

  Future<void> _addContact() async {
    final EmergencyContact? contact =
        await showModalBottomSheet<EmergencyContact>(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.white,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          builder: (_) => const AddContactSheet(),
        );

    if (contact == null) return;

    setState(() {
      _contacts.add(contact);
    });

    await _saveContacts();
  }

  Future<void> _editContact(int index) async {
    final EmergencyContact? updatedContact =
        await showModalBottomSheet<EmergencyContact>(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.white,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          builder: (_) => AddContactSheet(existingContact: _contacts[index]),
        );

    if (updatedContact == null) return;

    setState(() {
      _contacts[index] = updatedContact;
    });

    await _saveContacts();
  }

  Future<void> _deleteContact(int index) async {
    setState(() {
      _contacts.removeAt(index);
    });

    await _saveContacts();
  }

  void _toggleEdit() {
    setState(() {
      _isEditing = !_isEditing;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: Colors.white,

      body: SafeArea(
        child: Column(
          children: [
            // HEADER
            Container(
              width: double.infinity,
              height: 56,
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
                    l10n.emergencyContacts,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(16, 20, 16, 32),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            l10n.emergencyContactsIntro,
                            style: TextStyle(
                              fontSize: 12,
                              height: 1.5,
                              color: Colors.grey[600],
                            ),
                          ),

                          const SizedBox(height: 26),

                          Text(
                            l10n.emergencyServices,
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                            ),
                          ),

                          const SizedBox(height: 10),

                          const EmergencyServiceCard(),

                          const SizedBox(height: 28),

                          Row(
                            children: [
                              Text(
                                l10n.personalEmergencyContacts,
                                style: const TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),

                              const Spacer(),

                              TextButton(
                                onPressed: _toggleEdit,
                                style: TextButton.styleFrom(
                                  foregroundColor: const Color(0xFFE53935),
                                ),
                                child: Text(
                                  _isEditing ? l10n.done : l10n.edit,
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 10),

                          PersonalContactsCard(
                            contacts: _contacts,
                            isEditing: _isEditing,
                            onAddContact: _addContact,
                            onEditContact: _editContact,
                            onDeleteContact: _deleteContact,
                          ),

                          const SizedBox(height: 8),

                          Text(
                            l10n.contactsNotificationInfo,
                            style: TextStyle(
                              fontSize: 10,
                              color: Colors.grey[500],
                            ),
                          ),
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
