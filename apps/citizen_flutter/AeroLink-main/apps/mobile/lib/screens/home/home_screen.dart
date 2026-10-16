import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../../l10n/app_localizations.dart';

import '../sos/sos_screen.dart';
import '../more/more_screen.dart';
import '../more/aerolink/aerolink_device_screen.dart';

import '../../services/location_service.dart';
import '../../services/communication_service.dart';
import '../../services/ble_service.dart';
import '../../services/weather_service.dart';
import '../../services/lakhimpur_service.dart';

import 'widgets/header.dart';
import '../../widgets/slide_fade_in.dart';
import 'widgets/map_module.dart';
import 'widgets/communication_readiness.dart';
import 'widgets/weather_alerts.dart';
import 'widgets/weather_alerts_screen.dart';

import '../../widgets/app_bottom_navigation.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final LocationService _locationService = LocationService();
  final CommunicationService _communicationService = CommunicationService();
  final WeatherService _weatherService = WeatherService();
  final BleService _bleService = BleService.instance;

  Position? _currentPosition;

  String _gpsTimestamp = '';
  String _temperature = '--';
  String _weatherCondition = '';

  int _weatherCode = -1;

  bool _internetReady = false;
  bool _baseStationReady = false;
  bool _isLoadingLocation = false;

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeHomeScreen();
    });
  }

  // ===============================
  // NAVIGATION
  // ===============================

  void _openWeatherAlerts() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => WeatherAlertsScreen(
          temperature: _temperature,
          condition: _weatherCondition,
          weatherCode: _weatherCode,
        ),
      ),
    );
  }

  void _openAeroLinkDevice() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const AeroLinkDeviceScreen()),
    );
  }

  // ===============================
  // INITIALIZE HOME
  // ===============================

  Future<void> _initializeHomeScreen() async {
    await _getWeather();
    await _getLocation();
    await _checkCommunication();
  }

  // ===============================
  // LOCATION
  // ===============================

  Future<void> _getLocation() async {
    if (_isLoadingLocation) return;

    final l10n = AppLocalizations.of(context)!;

    if (mounted) {
      setState(() {
        _isLoadingLocation = true;
        _gpsTimestamp = l10n.acquiringGpsLocation;
      });
    }

    try {
      final Position position = await _locationService.getCurrentPosition();

      if (!mounted) return;

      setState(() {
        _currentPosition = position;
        _gpsTimestamp = l10n.updatedJustNow;
      });

      await _getWeather();
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _gpsTimestamp = l10n.locationUnavailable;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '${l10n.gps}: '
            '${e.toString().replaceFirst('Exception: ', '')}',
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingLocation = false;
        });
      }
    }
  }

  // ===============================
  // COMMUNICATION
  // ===============================

  Future<void> _checkCommunication() async {
    final bool internetAvailable = await _communicationService
        .checkInternetConnection();

    if (!mounted) return;

    setState(() {
      _internetReady = internetAvailable;
      _baseStationReady = false;
    });
  }

  // ===============================
  // WEATHER
  // ===============================

  Future<void> _getWeather() async {
    final double lat = _currentPosition?.latitude ?? LakhimpurDistrictService.districtCenter.latitude;
    final double lon = _currentPosition?.longitude ?? LakhimpurDistrictService.districtCenter.longitude;

    final l10n = AppLocalizations.of(context)!;

    try {
      final weather = await _weatherService.getCurrentWeather(
        latitude: lat,
        longitude: lon,
      );

      if (!mounted) return;

      setState(() {
        _temperature = '${weather.temperature.round()}°C';

        // Weather condition comes from the API.
        _weatherCondition = weather.condition;

        _weatherCode = weather.weatherCode;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _temperature = '--';
        _weatherCondition = l10n.weatherUnavailable;
        _weatherCode = -1;
      });
    }
  }

  // ===============================
  // PULL TO REFRESH
  // ===============================

  Future<void> _refreshHome() async {
    await Future.wait([_getLocation(), _checkCommunication()]);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    // Localized defaults when screen is first shown.
    if (_gpsTimestamp.isEmpty) {
      _gpsTimestamp = l10n.acquiring;
    }

    if (_weatherCondition.isEmpty) {
      _weatherCondition = l10n.loadingWeather;
    }

    return ListenableBuilder(
      listenable: _bleService,
      builder: (context, child) {
        return Scaffold(
          body: SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const HomeHeader(),

                Expanded(
                  child: RefreshIndicator(
                    color: const Color(0xFFFF6B35),
                    backgroundColor: Colors.white,
                    onRefresh: _refreshHome,
                    child: SingleChildScrollView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // LIVE MAP
                          SlideFadeIn(
                            delayMs: 200,
                            child: MapModule(
                              position: _currentPosition,
                              gpsTimestamp: _gpsTimestamp,
                              onRefresh: _refreshHome,
                            ),
                          ),

                          const SizedBox(height: 12),

                          // WEATHER & ALERTS
                          SlideFadeIn(
                            delayMs: 300,
                            child: WeatherAlerts(
                              temperature: _temperature,
                              condition: _weatherCondition,
                              weatherCode: _weatherCode,
                              alert: l10n.noEmergencyAlerts,
                              onMore: _openWeatherAlerts,
                              onWeatherTap: _openWeatherAlerts,
                            ),
                          ),

                          const SizedBox(height: 24),

                          // EMERGENCY READINESS
                          SlideFadeIn(
                            delayMs: 300,
                            child: CommunicationReadiness(
                              internetReady: _internetReady,
                              aeroLinkReady: _bleService.isConnected,
                              baseStationReady: _baseStationReady,
                              onAeroLinkTap: _openAeroLinkDevice,
                            ),
                          ),

                          const SizedBox(height: 16),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          bottomNavigationBar: AppBottomNavigation(
            currentIndex: 0,

            onHome: () {},

            onSOS: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SOSScreen()),
              );
            },

            onMore: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MoreScreen()),
              );
            },
          ),
        );
      },
    );
  }
}
