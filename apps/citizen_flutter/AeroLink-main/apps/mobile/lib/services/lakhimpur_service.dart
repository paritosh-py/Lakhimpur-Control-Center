import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettlementInfo {
  final String id;
  final String name;
  final LatLng coordinates;

  const SettlementInfo({
    required this.id,
    required this.name,
    required this.coordinates,
  });
}

class LakhimpurDistrictService {
  static final LakhimpurDistrictService instance = LakhimpurDistrictService._();
  LakhimpurDistrictService._();

  // District Center & Basecamp
  static const LatLng districtCenter = LatLng(27.235, 94.103);
  static const LatLng basecampBorimuri = LatLng(27.2666, 94.1255);

  // Exact study IDs, names, order and coordinates from data/processed/settlements.geojson.
  static const List<SettlementInfo> settlements = [
    SettlementInfo(id: "geonames-12523887", name: "Kadam", coordinates: LatLng(27.31589, 94.14915)),
    SettlementInfo(id: "geonames-1261181", name: "North Lakhimpur", coordinates: LatLng(27.23517, 94.10357)),
    SettlementInfo(id: "geonames-1271818", name: "Gāgaldubi", coordinates: LatLng(27.36218, 94.18316)),
    SettlementInfo(id: "geonames-1272576", name: "Diju", coordinates: LatLng(27.28333, 94.05)),
    SettlementInfo(id: "geonames-1256404", name: "Siājuli", coordinates: LatLng(27.37565, 94.0954)),
    SettlementInfo(id: "geonames-1269537", name: "Jaihing", coordinates: LatLng(27.30466, 94.03132)),
    SettlementInfo(id: "geonames-1253881", name: "Ulubāri", coordinates: LatLng(27.18648, 94.09891)),
    SettlementInfo(id: "geonames-8431965", name: "Khuiārpom", coordinates: LatLng(27.19409, 94.00529)),
    SettlementInfo(id: "geonames-1278042", name: "Bachāgaon", coordinates: LatLng(27.13529, 94.11639)),
    SettlementInfo(id: "geonames-12524294", name: "Naobaicha", coordinates: LatLng(27.16977, 94.0104)),
    SettlementInfo(id: "geonames-8432293", name: "Pahumarāgāon", coordinates: LatLng(27.12377, 94.10988)),
    SettlementInfo(id: "geonames-1272266", name: "Dulāhātgaon", coordinates: LatLng(27.1618, 93.99384)),
    SettlementInfo(id: "geonames-1261412", name: "Nij Lāluk", coordinates: LatLng(27.11878, 93.92959)),
    SettlementInfo(id: "geonames-8985791", name: "Chinatoli", coordinates: LatLng(27.03705, 93.96361)),
    SettlementInfo(id: "geonames-1275713", name: "Bihpuriāgaon", coordinates: LatLng(27.01718, 93.91673)),
    SettlementInfo(id: "geonames-8985727", name: "Bihpuria", coordinates: LatLng(27.01693, 93.91502)),
  ];

  static const List<String> candidateHosts = [
    'http://10.10.0.170:8000',
    'http://10.10.0.170:8001',
    'http://192.168.137.1:8000',
    'http://10.0.2.2:8000',
    'http://127.0.0.1:8000',
  ];

  static const String _prefKeyDeviceId = 'lakhimpur_device_id';
  static const String _prefKeyApiUrl = 'lakhimpur_api_url';

  String? _cachedDeviceId;
  String? _cachedApiUrl;

  /// Get or lazily create a stable, unique device identifier for repeat detection.
  Future<String> getDeviceId() async {
    if (_cachedDeviceId != null) return _cachedDeviceId!;
    final prefs = await SharedPreferences.getInstance();
    String? id = prefs.getString(_prefKeyDeviceId);
    if (id == null || id.isEmpty) {
      final rand = Random.secure();
      final hex = List.generate(8, (_) => rand.nextInt(256).toRadixString(16).padLeft(2, '0')).join().toUpperCase();
      id = 'DEV-$hex';
      await prefs.setString(_prefKeyDeviceId, id);
    }
    _cachedDeviceId = id;
    return id;
  }

  /// Check if a specific host URL is reachable
  Future<bool> probeHost(String host) async {
    try {
      final res = await http
          .get(Uri.parse('$host/api/health'))
          .timeout(const Duration(milliseconds: 1200));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Get the control center API URL, auto-probing reachable LAN hosts if needed
  Future<String> getApiUrl() async {
    if (_cachedApiUrl != null) return _cachedApiUrl!;
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefKeyApiUrl);
    if (saved != null && saved.trim().isNotEmpty) {
      _cachedApiUrl = saved.trim();
      return _cachedApiUrl!;
    }

    if (kIsWeb) {
      _cachedApiUrl = 'http://127.0.0.1:8000';
      return _cachedApiUrl!;
    }

    // Auto-probe candidate LAN hosts
    for (final host in candidateHosts) {
      if (await probeHost(host)) {
        _cachedApiUrl = host;
        await prefs.setString(_prefKeyApiUrl, host);
        return host;
      }
    }

    // Default to the known laptop Wi-Fi address
    _cachedApiUrl = candidateHosts.first;
    return _cachedApiUrl!;
  }

  /// Update the backend URL if testing over another LAN IP (e.g. http://192.168.1.50:8000)
  Future<void> setApiUrl(String url) async {
    final clean = url.trim().replaceAll(RegExp(r'/+$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKeyApiUrl, clean);
    _cachedApiUrl = clean;
  }

  /// Snap given lat/lon to nearest Lakhimpur settlement
  SettlementInfo? snapNearestSettlement(double? lat, double? lon) {
    if (lat == null || lon == null) return null;
    SettlementInfo? nearest;
    double minDistance = double.infinity;
    for (final s in settlements) {
      final dLat = lat - s.coordinates.latitude;
      final dLon = lon - s.coordinates.longitude;
      final dist = sqrt(dLat * dLat + dLon * dLon);
      if (dist < minDistance) {
        minDistance = dist;
        nearest = s;
      }
    }
    return nearest;
  }

  /// Send a Live Report directly to the backend over internet HTTP POST
  Future<Map<String, dynamic>> sendReportOnline({
    required String incidentType,
    required String description,
    String? settlementId,
    double? latitude,
    double? longitude,
    int peopleAffected = 1,
    String? roadStatus,
    double? waterDepthCm,
    String? waterTrend,
    List<String> conditions = const [],
    String? senderName,
    String? senderPhone,
  }) async {
    final primaryUrl = await getApiUrl();
    final deviceId = await getDeviceId();
    final selected = settlementId == null ? null : settlements.where((s) => s.id == settlementId).firstOrNull;
    if (settlementId != null && selected == null) {
      throw Exception('Selected settlement is not in the study area. Select a settlement again.');
    }
    final nearest = selected ?? snapNearestSettlement(latitude, longitude);

    final payload = {
      'device_id': deviceId,
      'incident_type': incidentType,
      'description': description,
      'latitude': latitude ?? districtCenter.latitude,
      'longitude': longitude ?? districtCenter.longitude,
      'settlement_id': nearest?.id,
      'settlement_name': nearest?.name ?? 'North Lakhimpur',
      'people_affected': peopleAffected,
      'road_status': roadStatus ?? 'unknown',
      'water_depth_cm': waterDepthCm,
      'water_trend': waterTrend ?? 'unknown',
      'conditions': conditions,
      'sender_name': senderName,
      'sender_phone': senderPhone,
      'timestamp': DateTime.now().toUtc().toIso8601String(),
    };

    // Try primary URL first, then cycle through candidate hosts if network shifted
    final hostsToTry = [primaryUrl, ...candidateHosts.where((h) => h != primaryUrl)];
    Object? lastError;

    for (final host in hostsToTry) {
      try {
        final uri = Uri.parse('$host/api/reports?context=live');
        final response = await http
            .post(
              uri,
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode(payload),
            )
            .timeout(const Duration(seconds: 25));

        if (response.statusCode == 200 || response.statusCode == 201) {
          _cachedApiUrl = host;
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(_prefKeyApiUrl, host);
          return jsonDecode(response.body) as Map<String, dynamic>;
        }
        lastError = 'Server $host returned HTTP ${response.statusCode}. Check the report fields and server configuration.';
      } catch (e) {
        lastError = e;
      }
    }

    throw Exception('Failed to connect to Command Dashboard at $primaryUrl ($lastError)');
  }

  /// Close or resolve a report directly from the citizen mobile app
  Future<bool> closeReportOnline(String reportId) async {
    final primaryUrl = await getApiUrl();
    final hostsToTry = [primaryUrl, ...candidateHosts.where((h) => h != primaryUrl)];

    for (final host in hostsToTry) {
      try {
        final uri = Uri.parse('$host/api/reports/${Uri.encodeComponent(reportId)}/status?context=live');
        final response = await http
            .post(
              uri,
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'status': 'closed',
                'note': 'Closed by citizen from mobile app',
              }),
            )
            .timeout(const Duration(seconds: 8));

        if (response.statusCode == 200) {
          return true;
        }
      } catch (_) {}
    }
    throw Exception('Could not confirm request closure at $primaryUrl. Check the server address and Wi-Fi, then retry.');
  }

  /// Fetch the latest status and data of a submitted report from the Control Center
  Future<Map<String, dynamic>?> getReport(String reportId) async {
    final primaryUrl = await getApiUrl();
    final hostsToTry = [primaryUrl, ...candidateHosts.where((h) => h != primaryUrl)];

    for (final host in hostsToTry) {
      try {
        final uri = Uri.parse('$host/api/reports/${Uri.encodeComponent(reportId)}?context=live');
        final response = await http.get(uri).timeout(const Duration(seconds: 4));
        if (response.statusCode == 200) {
          _cachedApiUrl = host;
          return jsonDecode(response.body) as Map<String, dynamic>;
        }
      } catch (_) {}
    }
    return null;
  }
}

