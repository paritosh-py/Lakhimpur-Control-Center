import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

class BleService extends ChangeNotifier {
  BleService._();

  // ==================================================
  // UUIDS
  // ==================================================

  static const String aeroLinkServiceUuid =
      '4fafc201-1fb5-459e-8fcc-c5c9c331914b';

  static const String sosCharacteristicUuid =
      'beb5483e-36e1-4688-b7f5-ea07361b26a8';

  static const String ackCharacteristicUuid =
      'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

  // ==================================================
  // SINGLETON
  // ==================================================

  static final BleService instance = BleService._();

  // ==================================================
  // STATE
  // ==================================================

  final List<ScanResult> _scanResults = [];

  BluetoothDevice? _connectedDevice;

  BluetoothConnectionState _connectionState =
      BluetoothConnectionState.disconnected;

  bool _isScanning = false;

  // ==================================================
  // CHARACTERISTICS
  // ==================================================

  BluetoothCharacteristic? _sosCharacteristic;
  BluetoothCharacteristic? _ackCharacteristic;

  // ==================================================
  // STREAM SUBSCRIPTIONS
  // ==================================================

  StreamSubscription<List<ScanResult>>? _scanSubscription;

  StreamSubscription<BluetoothConnectionState>? _connectionSubscription;

  StreamSubscription<List<int>>? _ackSubscription;

  // ==================================================
  // ACK WAITING
  // ==================================================

  final _messages = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get messages => _messages.stream;
  final List<int> _receiveBuffer = [];
  Future<void> _writeQueue = Future.value();

  // ==================================================
  // GETTERS
  // ==================================================

  List<ScanResult> get scanResults => List.unmodifiable(_scanResults);

  BluetoothDevice? get connectedDevice => _connectedDevice;

  BluetoothConnectionState get connectionState => _connectionState;

  bool get isConnected =>
      _connectionState == BluetoothConnectionState.connected;

  bool get isScanning => _isScanning;

  // ==================================================
  // PERMISSIONS
  // ==================================================

  Future<bool> requestPermissions() async {
    final statuses = await [
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.locationWhenInUse,
    ].request();

    return statuses[Permission.bluetoothScan]?.isGranted == true &&
        statuses[Permission.bluetoothConnect]?.isGranted == true;
  }

  // ==================================================
  // BLUETOOTH STATUS
  // ==================================================

  Future<bool> isBluetoothOn() async {
    final state = await FlutterBluePlus.adapterState.first;

    return state == BluetoothAdapterState.on;
  }

  // ==================================================
  // SCAN
  // ==================================================

  Future<List<ScanResult>> scanForAeroLinkDevices() async {
    _scanResults.clear();

    final permissionsGranted = await requestPermissions();

    if (!permissionsGranted) {
      throw Exception('Bluetooth permissions were not granted.');
    }

    final bluetoothOn = await isBluetoothOn();

    if (!bluetoothOn) {
      throw Exception('Bluetooth is turned off.');
    }

    await _scanSubscription?.cancel();

    _isScanning = true;
    notifyListeners();

    _scanSubscription = FlutterBluePlus.scanResults.listen((results) {
      final aeroLinkResults = results.where((result) {
        final deviceName = result.device.platformName;

        return deviceName.toLowerCase().contains('aerolink');
      }).toList();

      _scanResults
        ..clear()
        ..addAll(aeroLinkResults);

      notifyListeners();
    });

    try {
      await FlutterBluePlus.startScan(timeout: const Duration(seconds: 10));

      await Future.delayed(const Duration(seconds: 10));
    } finally {
      await FlutterBluePlus.stopScan();

      _isScanning = false;
      notifyListeners();
    }

    return List.unmodifiable(_scanResults);
  }

  // ==================================================
  // CONNECT
  // ==================================================

  Future<void> connect(BluetoothDevice device) async {
    // Already connected to this device.
    if (_connectedDevice?.remoteId == device.remoteId && isConnected) {
      return;
    }

    await _connectionSubscription?.cancel();

    _connectionSubscription = device.connectionState.listen((state) {
      _connectionState = state;

      if (state == BluetoothConnectionState.connected) {
        _connectedDevice = device;
      }

      if (state == BluetoothConnectionState.disconnected) {
        _connectedDevice = null;

        _sosCharacteristic = null;
        _ackCharacteristic = null;

        _receiveBuffer.clear();
      }

      notifyListeners();
    });

    try {
      await device.connect(timeout: const Duration(seconds: 15));
    } catch (e) {
      // FlutterBluePlus can throw when
      // the device is already connected.
      if (!isConnected) {
        rethrow;
      }
    }

    _connectedDevice = device;

    // Discover all AeroLink characteristics.
    await _discoverAeroLinkCharacteristics();

    // Start listening for ESP32 ACK messages.
    await _setupAckListener();

    notifyListeners();
  }

  // ==================================================
  // DISCOVER CHARACTERISTICS
  // ==================================================

  Future<void> _discoverAeroLinkCharacteristics() async {
    if (_connectedDevice == null) {
      throw Exception('No AeroLink device is connected.');
    }

    _sosCharacteristic = null;
    _ackCharacteristic = null;

    final services = await _connectedDevice!.discoverServices();

    for (final service in services) {
      if (service.uuid.toString().toLowerCase() !=
          aeroLinkServiceUuid.toLowerCase()) {
        continue;
      }

      for (final characteristic in service.characteristics) {
        final uuid = characteristic.uuid.toString().toLowerCase();

        if (uuid == sosCharacteristicUuid.toLowerCase()) {
          _sosCharacteristic = characteristic;
        }

        if (uuid == ackCharacteristicUuid.toLowerCase()) {
          _ackCharacteristic = characteristic;
        }
      }
    }

    if (_sosCharacteristic == null) {
      throw Exception('AeroLink SOS characteristic was not found.');
    }

    if (_ackCharacteristic == null) {
      throw Exception('AeroLink ACK characteristic was not found.');
    }
  }

  // ==================================================
  // ACK LISTENER
  // ==================================================

  Future<void> _setupAckListener() async {
    if (_ackCharacteristic == null) {
      throw Exception('ACK characteristic is not available.');
    }

    await _ackSubscription?.cancel();

    _receiveBuffer.clear();
    // Avoid replaying a cached ACK on reconnect.
    _ackSubscription = _ackCharacteristic!.onValueReceived.listen(
      (value) {
        for (final byte in value) {
          if (byte == 10) {
            if (_receiveBuffer.isEmpty) continue;
            try {
              final decoded = jsonDecode(utf8.decode(_receiveBuffer));
              if (decoded is Map<String, dynamic>) _messages.add(decoded);
            } catch (_) {
              debugPrint('Ignored malformed AeroLink packet.');
            }
            _receiveBuffer.clear();
          } else {
            _receiveBuffer.add(byte);
            if (_receiveBuffer.length > 4096) _receiveBuffer.clear();
          }
        }
      },
      onError: (Object error) {
        debugPrint('AeroLink notification error: $error');
      },
    );
    await _ackCharacteristic!.setNotifyValue(true);
  }

  /// Newline-delimited JSON, split into 20-byte BLE frames.
  /// Serialize writes so simultaneous chat/SOS packets cannot interleave.
  Future<void> sendPacket(Map<String, dynamic> packet) {
    final operation = _writeQueue.then((_) async {
      final characteristic = _sosCharacteristic;
      if (!isConnected || characteristic == null) {
        throw Exception(
          'AeroLink is disconnected. Reconnect from the device screen.',
        );
      }
      final data = utf8.encode('${jsonEncode(packet)}\n');
      if (data.length > 1024) {
        throw Exception(
          'Message is too large. Shorten the additional details.',
        );
      }
      // Discard any partial previous frame after a failed write/reconnect.
      await characteristic.write([10], withoutResponse: false);
      for (var offset = 0; offset < data.length; offset += 20) {
        final end = offset + 20 < data.length ? offset + 20 : data.length;
        await characteristic.write(
          data.sublist(offset, end),
          withoutResponse: false,
        );
      }
    });
    _writeQueue = operation.catchError((Object _) {});
    return operation;
  }
  // ==================================================
  // DISCONNECT
  // ==================================================

  Future<void> disconnect() async {
    if (_connectedDevice != null) {
      await _connectedDevice!.disconnect();
    }

    await _ackSubscription?.cancel();

    _ackSubscription = null;

    _connectedDevice = null;

    _sosCharacteristic = null;

    _ackCharacteristic = null;

    _connectionState = BluetoothConnectionState.disconnected;

    _receiveBuffer.clear();

    notifyListeners();
  }

  // ==================================================
  // CLEANUP
  // ==================================================

  Future<void> disposeService() async {
    await _scanSubscription?.cancel();

    await _connectionSubscription?.cancel();

    await _ackSubscription?.cancel();

    _scanSubscription = null;
    _connectionSubscription = null;
    _ackSubscription = null;
  }
}
