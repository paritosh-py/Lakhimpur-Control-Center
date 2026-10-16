import 'dart:io';

import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

class PersonalInformationScreen extends StatefulWidget {
  const PersonalInformationScreen({super.key});

  @override
  State<PersonalInformationScreen> createState() =>
      _PersonalInformationScreenState();
}

class _PersonalInformationScreenState extends State<PersonalInformationScreen> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();

  final ImagePicker _imagePicker = ImagePicker();

  bool _isLoading = true;
  bool _isEditing = true;
  bool _hasSavedInformation = false;

  String? _profileImagePath;

  static const String _nameKey = 'user_full_name';
  static const String _phoneKey = 'user_phone_number';
  static const String _emailKey = 'user_email_address';
  static const String _profileImageKey = 'user_profile_image';

  @override
  void initState() {
    super.initState();
    _loadInformation();
  }

  // ===============================
  // LOAD SAVED INFORMATION
  // ===============================

  Future<void> _loadInformation() async {
    final prefs = await SharedPreferences.getInstance();

    final String name = prefs.getString(_nameKey) ?? '';
    final String phone = prefs.getString(_phoneKey) ?? '';
    final String email = prefs.getString(_emailKey) ?? '';
    final String? profileImage = prefs.getString(_profileImageKey);

    if (!mounted) return;

    setState(() {
      _nameController.text = name;
      _phoneController.text = phone;
      _emailController.text = email;
      _profileImagePath = profileImage;

      _hasSavedInformation = name.isNotEmpty || phone.isNotEmpty;

      _isEditing = !_hasSavedInformation;

      _isLoading = false;
    });
  }

  // ===============================
  // PICK PROFILE IMAGE
  // ===============================

  Future<void> _pickProfileImage() async {
    try {
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );

      if (image == null) {
        return;
      }

      final prefs = await SharedPreferences.getInstance();

      await prefs.setString(_profileImageKey, image.path);

      if (!mounted) return;

      setState(() {
        _profileImagePath = image.path;
      });
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            AppLocalizations.of(context)!.failedToSelectImage(e.toString()),
          ),
        ),
      );

      debugPrint('IMAGE PICKER ERROR: $e');
    }
  }

  // ===============================
  // SAVE INFORMATION
  // ===============================

  Future<void> _saveInformation() async {
    final String name = _nameController.text.trim();
    final String phone = _phoneController.text.trim();
    final String email = _emailController.text.trim();

    if (name.isEmpty || phone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context)!.requiredNameAndPhone),
        ),
      );
      return;
    }

    final prefs = await SharedPreferences.getInstance();

    await prefs.setString(_nameKey, name);
    await prefs.setString(_phoneKey, phone);
    await prefs.setString(_emailKey, email);

    if (!mounted) return;

    setState(() {
      _hasSavedInformation = true;
      _isEditing = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(AppLocalizations.of(context)!.personalInformationSaved),
      ),
    );
  }

  // ===============================
  // ENABLE EDIT MODE
  // ===============================

  void _enableEditing() {
    setState(() {
      _isEditing = true;
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(color: Color(0xFFFF6B35)),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // HEADER
            Container(
              width: double.infinity,
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
              child: SizedBox(
                height: 56,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Positioned(
                      left: 8,
                      child: IconButton(
                        onPressed: () {
                          Navigator.pop(context, _profileImagePath);
                        },
                        icon: const Icon(Icons.arrow_back_rounded, size: 22),
                      ),
                    ),

                    Center(
                      child: Text(
                        l10n.personalInformation,
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // CONTENT
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.personalInfoEmergencyUse,
                      style: TextStyle(
                        fontSize: 12,
                        height: 1.5,
                        color: Colors.grey[600],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // INFORMATION CARD
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(color: Colors.grey.shade200),
                      ),
                      child: Column(
                        children: [
                          // PROFILE AVATAR
                          Center(
                            child: Stack(
                              children: [
                                Container(
                                  width: 110,
                                  height: 110,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: const Color(0xFFFF6B35),
                                      width: 2,
                                    ),
                                  ),
                                  child: ClipOval(
                                    child:
                                        _profileImagePath != null &&
                                            File(_profileImagePath!)
                                                .existsSync()
                                        ? Image.file(
                                            File(_profileImagePath!),
                                            fit: BoxFit.cover,
                                          )
                                        : Image.asset(
                                            'assets/images/profile_avatar.png',
                                            fit: BoxFit.cover,
                                            errorBuilder:
                                                (context, error, stackTrace) {
                                                  return const Icon(
                                                    Icons.person,
                                                    size: 55,
                                                    color: Color(0xFF1A2A3A),
                                                  );
                                                },
                                          ),
                                  ),
                                ),

                                // EDIT AVATAR BUTTON
                                Positioned(
                                  right: 0,
                                  bottom: 0,
                                  child: Material(
                                    color: const Color(0xFFFF6B35),
                                    shape: const CircleBorder(),
                                    child: InkWell(
                                      onTap: _pickProfileImage,
                                      customBorder: const CircleBorder(),
                                      child: const Padding(
                                        padding: EdgeInsets.all(8),
                                        child: Icon(
                                          Icons.camera_alt_rounded,
                                          color: Colors.white,
                                          size: 18,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 28),

                          _buildTextField(
                            controller: _nameController,
                            label: l10n.fullName,
                            hint: l10n.enterFullName,
                            textInputAction: TextInputAction.next,
                          ),

                          const SizedBox(height: 18),

                          _buildTextField(
                            controller: _phoneController,
                            label: l10n.phoneNumber,
                            hint: l10n.enterPhoneNumber,
                            keyboardType: TextInputType.phone,
                            textInputAction: TextInputAction.next,
                          ),

                          const SizedBox(height: 18),

                          _buildTextField(
                            controller: _emailController,
                            label: l10n.emailAddress,
                            hint: l10n.enterEmailAddress,
                            keyboardType: TextInputType.emailAddress,
                            textInputAction: TextInputAction.done,
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // EDIT / SAVE BUTTON
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _isEditing
                            ? _saveInformation
                            : _enableEditing,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFFF6B35),
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                        child: Text(
                          _isEditing
                              ? (_hasSavedInformation
                                    ? l10n.saveChanges
                                    : l10n.saveInformation)
                              : l10n.editInformation,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
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

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required String hint,
    TextInputType? keyboardType,
    TextInputAction? textInputAction,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: Colors.black87,
          ),
        ),

        const SizedBox(height: 7),

        TextField(
          controller: controller,
          enabled: _isEditing,
          keyboardType: keyboardType,
          textInputAction: textInputAction,
          style: TextStyle(
            fontSize: 14,
            color: _isEditing ? Colors.black87 : Colors.black54,
          ),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(fontSize: 12, color: Colors.grey[500]),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 14,
              vertical: 13,
            ),
            filled: true,
            fillColor: _isEditing
                ? Colors.white
                : Colors.grey.withValues(alpha: 0.04),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade200),
            ),
            disabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade200),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(
                color: Color(0xFFFF6B35),
                width: 1.5,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
