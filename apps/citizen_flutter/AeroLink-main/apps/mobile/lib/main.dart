import 'package:flutter/material.dart';

import 'screens/splash_screen.dart';
import 'screens/sos/widgets/sos_completion_listener.dart';
import 'services/locale_controller.dart';
import 'l10n/app_localizations.dart';

final appNavigatorKey = GlobalKey<NavigatorState>();

final LocaleController localeController = LocaleController();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await localeController.loadSavedLocale();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: localeController,
      builder: (context, child) {
        return SOSCompletionListener(
          navigatorKey: appNavigatorKey,
          child: MaterialApp(
            navigatorKey: appNavigatorKey,
            title: 'AeroLink',
            debugShowCheckedModeBanner: false,

            locale: localeController.locale,

            localizationsDelegates: AppLocalizations.localizationsDelegates,

            supportedLocales: AppLocalizations.supportedLocales,

            theme: ThemeData(
              scaffoldBackgroundColor: const Color(0xFFF5F5F5),
              fontFamily: 'Roboto',
              colorScheme: ColorScheme.fromSeed(
                seedColor: const Color(0xFFFF6B35),
                primary: const Color(0xFF1A2A3A),
              ),
            ),

            home: const SplashScreen(),
          ),
        );
      },
    );
  }
}
