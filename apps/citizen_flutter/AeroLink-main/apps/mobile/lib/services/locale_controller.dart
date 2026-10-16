import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocaleController extends ChangeNotifier {
  static const String _languageKey = 'selected_language';

  Locale _locale = const Locale('en');

  Locale get locale => _locale;

  String get languageCode => _locale.languageCode;

  Future<void> loadSavedLocale() async {
    final prefs = await SharedPreferences.getInstance();

    final languageCode = prefs.getString(_languageKey) ?? 'en';

    _locale = Locale(languageCode);

    notifyListeners();
  }

  Future<void> changeLocale(String languageCode) async {
    _locale = Locale(languageCode);

    final prefs = await SharedPreferences.getInstance();

    await prefs.setString(_languageKey, languageCode);

    notifyListeners();
  }
}
