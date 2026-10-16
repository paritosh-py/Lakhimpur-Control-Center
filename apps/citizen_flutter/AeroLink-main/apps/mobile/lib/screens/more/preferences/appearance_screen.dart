import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

import 'widgets/appearance_option_card.dart';
import '../../../main.dart';

class AppearanceScreen extends StatefulWidget {
  const AppearanceScreen({super.key});

  @override
  State<AppearanceScreen> createState() => _AppearanceScreenState();
}

class _AppearanceScreenState extends State<AppearanceScreen> {
  String _selectedTheme = 'system';
  double _textScale = 1.0;
  bool _isLanguageExpanded = false;
  String _languageName(String code, AppLocalizations l10n) {
    switch (code) {
      case 'hi':
        return l10n.hindi;
      case 'mr':
        return l10n.marathi;
      case 'en':
      default:
        return l10n.english;
    }
  }

  String _textSizeLabel(AppLocalizations l10n) {
    if (_textScale < 0.93) return l10n.small;
    if (_textScale < 1.08) return l10n.defaultSize;
    if (_textScale < 1.23) return l10n.large;
    return l10n.extraLarge;
  }

  Widget _languageOption({
    required String code,
    required String label,
    required String nativeLabel,
  }) {
    final bool selected = localeController.languageCode == code;

    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () async {
          await localeController.changeLocale(code);

          if (!mounted) return;

          setState(() {
            _isLanguageExpanded = false;
          });
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: selected ? const Color(0xFFFFE5D6) : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? const Color(0xFFFFC3A5) : Colors.grey.shade200,
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    color: Colors.black87,
                  ),
                ),
              ),

              Text(
                nativeLabel,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                  color: Colors.grey[700],
                ),
              ),

              if (selected) ...[
                const SizedBox(width: 10),

                const Icon(
                  Icons.check_circle_rounded,
                  size: 18,
                  color: Color(0xFFE57A44),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: Colors.white,

      body: SafeArea(
        child: Column(
          children: [
            // ================= HEADER =================

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
                          Navigator.pop(context);
                        },
                        icon: const Icon(Icons.arrow_back_rounded, size: 22),
                      ),
                    ),

                    Text(
                      l10n.appearance,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 22, 16, 30),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.appearanceIntro,
                      style: TextStyle(
                        fontSize: 12,
                        height: 1.5,
                        color: Colors.grey[600],
                      ),
                    ),

                    const SizedBox(height: 26),

                    // ================= THEME =================
                    Text(
                      l10n.theme,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 10),

                    AppearanceOptionCard(
                      title: l10n.light,
                      subtitle: l10n.useBrightAppearance,
                      icon: Icons.light_mode_outlined,
                      selected: _selectedTheme == 'light',
                      onTap: () {
                        setState(() {
                          _selectedTheme = 'light';
                        });
                      },
                    ),

                    const SizedBox(height: 10),

                    AppearanceOptionCard(
                      title: l10n.dark,
                      subtitle: l10n.reduceBrightness,
                      icon: Icons.dark_mode_outlined,
                      selected: _selectedTheme == 'dark',
                      onTap: () {
                        setState(() {
                          _selectedTheme = 'dark';
                        });
                      },
                    ),

                    const SizedBox(height: 10),

                    AppearanceOptionCard(
                      title: l10n.systemDefault,
                      subtitle: l10n.matchDeviceAppearance,
                      icon: Icons.brightness_auto_rounded,
                      selected: _selectedTheme == 'system',
                      onTap: () {
                        setState(() {
                          _selectedTheme = 'system';
                        });
                      },
                    ),

                    const SizedBox(height: 30),

                    // ================= DISPLAY =================
                    Text(
                      l10n.display,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 10),

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
                          Row(
                            children: [
                              Container(
                                width: 42,
                                height: 42,
                                decoration: BoxDecoration(
                                  color: Colors.black.withValues(alpha: 0.05),
                                  borderRadius: BorderRadius.circular(13),
                                ),
                                child: const Icon(
                                  Icons.text_fields_rounded,
                                  size: 21,
                                ),
                              ),

                              const SizedBox(width: 13),

                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      l10n.textSize,
                                      style: const TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),

                                    const SizedBox(height: 3),

                                    Text(
                                      l10n.adjustTextSize,
                                      style: const TextStyle(
                                        fontSize: 10,
                                        color: Colors.grey,
                                      ),
                                    ),
                                  ],
                                ),
                              ),

                              Text(
                                _textSizeLabel(l10n),
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 18),

                          Row(
                            children: [
                              const Text(
                                'A',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),

                              Expanded(
                                child: Slider(
                                  value: _textScale.clamp(0.85, 1.3).toDouble(),
                                  min: 0.85,
                                  max: 1.3,
                                  divisions: 3,
                                  activeColor: const Color(0xFFE53935),
                                  inactiveColor: Colors.grey.shade200,
                                  onChanged: (double value) {
                                    setState(() {
                                      _textScale = value
                                          .clamp(0.85, 1.3)
                                          .toDouble();
                                    });
                                  },
                                ),
                              ),

                              const Text(
                                'A',
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 8),

                          AnimatedDefaultTextStyle(
                            duration: const Duration(milliseconds: 180),
                            style: TextStyle(
                              fontSize: 13 * _textScale,
                              color: Colors.black87,
                              fontWeight: FontWeight.w600,
                            ),
                            child: Text(l10n.textPreview),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    Text(
                      l10n.language,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 10),

                    Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(color: Colors.grey.shade200),
                      ),
                      child: Column(
                        children: [
                          // ================= LANGUAGE HEADER =================
                          Material(
                            color: Colors.transparent,
                            borderRadius: BorderRadius.circular(18),
                            child: InkWell(
                              borderRadius: BorderRadius.circular(18),
                              onTap: () {
                                setState(() {
                                  _isLanguageExpanded = !_isLanguageExpanded;
                                });
                              },
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Row(
                                  children: [
                                    Container(
                                      width: 42,
                                      height: 42,
                                      decoration: BoxDecoration(
                                        color: Colors.black.withValues(
                                          alpha: 0.05,
                                        ),
                                        borderRadius: BorderRadius.circular(13),
                                      ),
                                      child: const Icon(
                                        Icons.language_rounded,
                                        size: 21,
                                      ),
                                    ),

                                    const SizedBox(width: 13),

                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            l10n.appLanguage,
                                            style: const TextStyle(
                                              fontSize: 13,
                                              fontWeight: FontWeight.w700,
                                            ),
                                          ),

                                          const SizedBox(height: 3),

                                          Text(
                                            _languageName(
                                              localeController.languageCode,
                                              l10n,
                                            ),
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.grey[600],
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),

                                    AnimatedRotation(
                                      turns: _isLanguageExpanded ? 0.5 : 0,
                                      duration: const Duration(
                                        milliseconds: 220,
                                      ),
                                      child: const Icon(
                                        Icons.keyboard_arrow_down_rounded,
                                        color: Colors.grey,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),

                          // ================= LANGUAGE OPTIONS =================
                          AnimatedSize(
                            duration: const Duration(milliseconds: 250),
                            curve: Curves.easeInOut,
                            child: _isLanguageExpanded
                                ? Padding(
                                    padding: const EdgeInsets.fromLTRB(
                                      16,
                                      0,
                                      16,
                                      16,
                                    ),
                                    child: Column(
                                      children: [
                                        Divider(
                                          height: 1,
                                          color: Colors.grey.shade200,
                                        ),

                                        const SizedBox(height: 12),

                                        _languageOption(
                                          code: 'en',
                                          label: l10n.english,
                                          nativeLabel: 'English',
                                        ),

                                        const SizedBox(height: 8),

                                        _languageOption(
                                          code: 'hi',
                                          label: l10n.hindi,
                                          nativeLabel: 'हिन्दी',
                                        ),

                                        const SizedBox(height: 8),

                                        _languageOption(
                                          code: 'mr',
                                          label: l10n.marathi,
                                          nativeLabel: 'मराठी',
                                        ),
                                      ],
                                    ),
                                  )
                                : const SizedBox.shrink(),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 22),

                    Text(
                      l10n.appearanceFooter,
                      style: TextStyle(
                        fontSize: 10,
                        height: 1.5,
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
