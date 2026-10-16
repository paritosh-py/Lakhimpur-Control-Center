import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/emergency_contact.dart';

class EmergencyContactService {
  static const String _storageKey = 'emergency_contacts';

  Future<List<EmergencyContact>> loadContacts() async {
    final preferences = await SharedPreferences.getInstance();

    final String? savedData = preferences.getString(_storageKey);

    if (savedData == null || savedData.isEmpty) {
      return [];
    }

    try {
      final List<dynamic> decodedData = jsonDecode(savedData);

      return decodedData
          .map(
            (contact) =>
                EmergencyContact.fromJson(Map<String, dynamic>.from(contact)),
          )
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> saveContacts(List<EmergencyContact> contacts) async {
    final preferences = await SharedPreferences.getInstance();

    final String encodedData = jsonEncode(
      contacts.map((contact) => contact.toJson()).toList(),
    );

    await preferences.setString(_storageKey, encodedData);
  }
}
