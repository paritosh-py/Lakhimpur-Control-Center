import 'package:geolocator/geolocator.dart';

class LocationService {
  /// Get the user's current GPS position
  Future<Position> getCurrentPosition() async {
    // 1. Check whether location services are enabled
    final bool serviceEnabled = await Geolocator.isLocationServiceEnabled();

    if (!serviceEnabled) {
      throw Exception('Location services are disabled. Please enable GPS.');
    }

    // 2. Check current permission
    LocationPermission permission = await Geolocator.checkPermission();

    // 3. Request permission if necessary
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();

      if (permission == LocationPermission.denied) {
        throw Exception('Location permission was denied.');
      }
    }

    // 4. Handle permanently denied permission
    if (permission == LocationPermission.deniedForever) {
      throw Exception(
        'Location permission is permanently denied. '
        'Please enable it from app settings.',
      );
    }

    // 5. Get current position
    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
      ).timeout(
        const Duration(seconds: 15),
        onTimeout: () {
          throw Exception('Unable to get GPS location. Please try again.');
        },
      );
    } catch (e) {
      throw Exception('Failed to get current location: $e');
    }
  }

  /// Open device location settings
  Future<void> openLocationSettings() async {
    await Geolocator.openLocationSettings();
  }

  /// Open application settings
  Future<void> openAppSettings() async {
    await Geolocator.openAppSettings();
  }
}
