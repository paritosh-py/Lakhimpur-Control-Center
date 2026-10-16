import 'dart:io';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../more/profile/personal_information_screen.dart';

class HomeHeader extends StatefulWidget {
  const HomeHeader({super.key});

  @override
  State<HomeHeader> createState() => _HomeHeaderState();
}

class _HomeHeaderState extends State<HomeHeader> {
  static const String _profileImageKey = 'user_profile_image';

  String? _profileImagePath;

  @override
  void initState() {
    super.initState();
    _loadProfileImage();
  }

  Future<void> _loadProfileImage() async {
    final prefs = await SharedPreferences.getInstance();

    final imagePath = prefs.getString(_profileImageKey);

    if (!mounted) return;

    setState(() {
      _profileImagePath = imagePath;
    });
  }

  Future<void> _openProfile() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const PersonalInformationScreen(),
      ),
    );

    // Reload the avatar after returning from the profile screen.
    await _loadProfileImage();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 6,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Row(
        children: [
          // App logo
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Container(
              width: 32,
              height: 32,
              color: Colors.transparent,
              child: Image.asset(
                'assets/images/AppIcon.png',
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) {
                  return const Icon(
                    Icons.wifi_tethering,
                    color: Colors.white,
                    size: 28,
                  );
                },
              ),
            ),
          ),

          const SizedBox(width: 12),

          // Centered title
          const Expanded(
            child: Text(
              'Aerolink',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1A2A3A),
                letterSpacing: 0.5,
              ),
            ),
          ),

          // Clickable profile avatar
          InkWell(
            onTap: _openProfile,
            borderRadius: BorderRadius.circular(24),
            child: ClipOval(
              child:
                  _profileImagePath != null &&
                      File(_profileImagePath!).existsSync()
                  ? Image.file(
                      File(_profileImagePath!),
                      width: 32,
                      height: 32,
                      fit: BoxFit.cover,
                    )
                  : Image.asset(
                      'assets/images/profile_avatar.png',
                      width: 32,
                      height: 32,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          width: 32,
                          height: 32,
                          color: const Color(0xFF1A2A3A),
                          child: const Icon(
                            Icons.person,
                            color: Colors.white,
                            size: 28,
                          ),
                        );
                      },
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
