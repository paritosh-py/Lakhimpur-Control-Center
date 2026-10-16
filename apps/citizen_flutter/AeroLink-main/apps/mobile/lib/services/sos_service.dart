import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';

import 'ble_service.dart';
import 'communication_service.dart';
import 'lakhimpur_service.dart';

enum SOSStage {
  idle,
  preparing,
  sendingToAeroLink,
  waitingForAcknowledgment,
  confirmed,
  acknowledged,
  completionRequested,
  completed,
  failed,
}

enum MessageDelivery { sending, delivered, unconfirmed }
enum SOSDeliveryPath { checking, internet, mesh }

class SOSChatMessage {
  SOSChatMessage({
    required this.id,
    required this.text,
    required this.fromAuthority,
    required this.createdAt,
    this.delivery = MessageDelivery.sending,
  });
  final String id;
  final String text;
  final bool fromAuthority;
  final DateTime createdAt;
  MessageDelivery delivery;
}

/// One active request, retained across navigation for the current app session.
class SOSService extends ChangeNotifier {
  SOSService({
    required Stream<Map<String, dynamic>> events,
    required this.sendPacket,
    this.ackTimeout = const Duration(seconds: 20),
    this.checkOnline,
    this.sendOnline,
    this.closeOnline,
    this.fetchReportStatus,
  }) {
    _subscription = events.listen(_receive);
  }
  static final SOSService instance = SOSService(
    events: BleService.instance.messages,
    sendPacket: BleService.instance.sendPacket,
  );
  final Future<void> Function(Map<String, dynamic>) sendPacket;
  final Duration ackTimeout;
  final Future<bool> Function()? checkOnline;
  final Future<Map<String, dynamic>> Function(Map<String, dynamic>)? sendOnline;
  final Future<bool> Function(String)? closeOnline;
  final Future<Map<String, dynamic>?> Function(String)? fetchReportStatus;
  SOSDeliveryPath _deliveryPath = SOSDeliveryPath.checking;
  SOSDeliveryPath get deliveryPath => _deliveryPath;
  late final StreamSubscription<Map<String, dynamic>> _subscription;
  final Map<String, Completer<void>> _pending = {};
  final List<SOSChatMessage> _messages = [];
  final Set<String> _handledCompletionIds = {};
  Map<String, dynamic>? _payload;
  Timer? _baseTimer;
  Timer? _statusPollTimer;
  SOSStage _stage = SOSStage.idle;
  String? _errorMessage;
  String? _completionId;
  bool? _completionDecision;
  bool _sending = false;
  bool _responding = false;
  bool aeroLinkConfirmed = false;
  bool baseStationAcknowledged = false;
  bool _isDeliveredOnline = false;
  String? _serverReportId;
  Map<String, dynamic>? _lastTriageResult;
  DateTime? createdAt;

  void _startStatusPolling() {
    _statusPollTimer?.cancel();
    if (!_isDeliveredOnline || _serverReportId == null) {
      return;
    }
    _statusPollTimer = Timer.periodic(const Duration(seconds: 3), (_) async {
      final idToCheck = _serverReportId;
      if (idToCheck == null ||
          !_isDeliveredOnline ||
          _stage == SOSStage.completed ||
          _stage == SOSStage.idle ||
          _stage == SOSStage.failed) {
        _statusPollTimer?.cancel();
        return;
      }
      try {
        final report = await (fetchReportStatus?.call(idToCheck) ??
            LakhimpurDistrictService.instance.getReport(idToCheck));
        if (report != null) {
          final status = report['status']?.toString().toLowerCase();
          if (status == 'closed' || status == 'resolved') {
            _statusPollTimer?.cancel();
            _stage = SOSStage.completed;
            _errorMessage = null;
            notifyListeners();
          }
        }
      } catch (_) {}
    });
  }


  SOSStage get stage => _stage;
  String? get errorMessage => _errorMessage;
  String? get sosId => _payload?['sosId'] as String?;
  String? get serverReportId => _serverReportId;
  String? get completionId => _completionId;
  bool get isTransmitting => _sending;
  bool get respondingToCompletion => _responding;
  bool get isDeliveredOnline => _isDeliveredOnline;
  Map<String, dynamic>? get lastTriageResult => _lastTriageResult;
  List<SOSChatMessage> get messages => List.unmodifiable(_messages);
  bool get canChat =>
      sosId != null && !_isDeliveredOnline && aeroLinkConfirmed && _stage != SOSStage.completed;

  static String randomId(String prefix) {
    final random = Random.secure();
    return '$prefix-${List.generate(12, (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0')).join().toUpperCase()}';
  }

  Future<void> sendSOS(String sosJson) async {
    if (_sending || (_payload != null && _stage != SOSStage.failed)) return;
    if (_payload == null) {
      final decoded = jsonDecode(sosJson) as Map<String, dynamic>;
      final time = DateTime.now();
      final payload = {
        ...decoded,
        'type': 'SOS',
        'sosId': randomId('SOS'),
        'timestamp': time.toUtc().toIso8601String(),
      };
      if (utf8
              .encode(jsonEncode({...payload, 'messageId': randomId('MSG')}))
              .length >
          1023) {
        throw Exception(
          'SOS is too large. Shorten the additional details and try again.',
        );
      }
      createdAt = time;
      _payload = payload;
    }
    await retry();
  }

  Future<void> retry() async {
    if (_payload == null ||
        _sending ||
        _stage == SOSStage.completed ||
        _completionId != null) {
      return;
    }
    _sending = true;
    _errorMessage = null;
    _deliveryPath = SOSDeliveryPath.checking;
    _stage = SOSStage.preparing;
    notifyListeners();

    // 1. Direct Internet Delivery (No ESP32 node required when online)
    final bool hasInternet;
    try {
      hasInternet = await (checkOnline?.call() ?? CommunicationService().checkInternetConnection());
    } catch (_) {
      _errorMessage = 'Could not check the network connection. Retry after checking Wi-Fi or mobile data.';
      _stage = SOSStage.failed;
      _sending = false;
      notifyListeners();
      return;
    }
    if (hasInternet) {
      _deliveryPath = SOSDeliveryPath.internet;
      _stage = SOSStage.waitingForAcknowledgment;
      notifyListeners();
      try {
        final res = sendOnline != null ? await sendOnline!(_payload!) : await LakhimpurDistrictService.instance.sendReportOnline(
          settlementId: _payload?['settlementId'] as String?,
          incidentType: _payload?['incidentType'] ?? _payload?['type'] ?? 'rescue_sos',
          description: _payload?['additionalDetails'] ?? _payload?['description'] ?? '',
          latitude: (_payload?['latitude'] as num?)?.toDouble(),
          longitude: (_payload?['longitude'] as num?)?.toDouble(),
          peopleAffected: (_payload?['peopleAffected'] as num?)?.toInt() ?? 1,
          roadStatus: _payload?['roadStatus'] as String?,
          waterDepthCm: (_payload?['waterDepthCm'] as num?)?.toDouble(),
          waterTrend: _payload?['waterTrend'] as String?,
          conditions: (_payload?['conditions'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? const [],
          senderName: _payload?['senderName'] as String?,
          senderPhone: _payload?['senderPhone'] as String?,
        );

        final reportId = (res['report']?['id'] ?? res['id']) as String?;
        if (reportId == null || reportId.isEmpty) {
          throw Exception('The server did not confirm a report reference. Check the dashboard before retrying.');
        }
        _isDeliveredOnline = true;
        _serverReportId = reportId;
        _lastTriageResult = res['gemini_triage'] as Map<String, dynamic>?;
        _stage = SOSStage.acknowledged;
        _sending = false;
        _startStatusPolling();
        notifyListeners();
        return;
      } catch (err) {
        _errorMessage = 'Internet transmission error: ${err.toString().replaceFirst('Exception: ', '')}';
        _stage = SOSStage.failed;
        _sending = false;
        notifyListeners();
        return;
      }
    }

    // 2. Off-grid BLE / ESP-NOW node fallback (ONLY when there is NO internet)
    _deliveryPath = SOSDeliveryPath.mesh;
    _stage = aeroLinkConfirmed ? SOSStage.confirmed : SOSStage.waitingForAcknowledgment;
    _isDeliveredOnline = false;
    notifyListeners();
    try {
      await _sendAndWait({..._payload!, 'messageId': randomId('MSG')}, 'SOS');
      if (!baseStationAcknowledged && _completionId == null) {
        _stage = SOSStage.confirmed;
        _baseTimer?.cancel();
        _baseTimer = Timer(ackTimeout, () {
          if (!baseStationAcknowledged && _stage != SOSStage.completed) {
            _errorMessage = 'No response from AeroLink node. Ensure ESP32 node is powered and in range.';
            notifyListeners();
          }
        });
      }
    } catch (error) {
      if (!baseStationAcknowledged && _completionId == null) {
        _errorMessage = error.toString().replaceFirst('Exception: ', '');
        _stage = aeroLinkConfirmed ? SOSStage.confirmed : SOSStage.failed;
      }
    } finally {
      _sending = false;
      notifyListeners();
    }
  }

  /// Close or resolve this report directly online
  Future<bool> closeOnlineReport() async {
    final idToClose = _serverReportId;
    if (!_isDeliveredOnline || idToClose == null || _sending) return false;
    _sending = true;
    notifyListeners();
    try {
      final ok = await (closeOnline?.call(idToClose) ?? LakhimpurDistrictService.instance.closeReportOnline(idToClose));
      if (ok) {
        _statusPollTimer?.cancel();
        _stage = SOSStage.completed;
        _errorMessage = null;
        notifyListeners();
        return true;
      }
      _errorMessage = 'The server did not confirm closure. The request remains open; check the connection and retry.';
    } catch (e) {
      _errorMessage = 'Failed to close report on server: $e';
    } finally {
      _sending = false;
      notifyListeners();
    }
    return false;
  }

  Future<void> _sendAndWait(Map<String, dynamic> packet, String kind) async {
    final id = packet['messageId'] as String;
    final completer = Completer<void>();
    _pending['$kind:$id'] = completer;
    final wait = completer.future.timeout(ackTimeout);
    try {
      await Future.wait<void>([sendPacket(packet), wait], eagerError: true);
    } on TimeoutException {
      throw Exception('Delivery was not confirmed. Check AeroLink and retry.');
    } finally {
      _pending.remove('$kind:$id');
    }
  }

  void _complete(String kind, Object? id, [String? error]) {
    final pending = _pending['$kind:$id'];
    if (pending == null || pending.isCompleted) return;
    if (error == null) {
      pending.complete();
    } else {
      pending.completeError(Exception(error));
    }
  }

  void _receive(Map<String, dynamic> packet) {
    if (_deliveryPath != SOSDeliveryPath.mesh) return;
    if (sosId == null ||
        packet['sosId'] != sosId ||
        _stage == SOSStage.completed) {
      return;
    }
    final type = packet['type'];
    final status = packet['status'];
    if (type == 'ACK') {
      if (status == 'SOS_RECEIVED' ||
          status == 'SOS_FORWARDED_TO_BASE_STATION' ||
          status == 'SOS_RECEIVED_BASE_STATION_UNAVAILABLE') {
        aeroLinkConfirmed = true;
        if (!baseStationAcknowledged && _completionId == null) {
          _stage = SOSStage.confirmed;
        }
        _complete('SOS', packet['messageId']);
        if (status == 'SOS_RECEIVED_BASE_STATION_UNAVAILABLE' &&
            !baseStationAcknowledged) {
          _errorMessage = 'AeroLink received your SOS, but the base station is unavailable. Retry when in range.';
        }
      } else if (status == 'BASE_STATION_RECEIVED') {
        aeroLinkConfirmed = true;
        baseStationAcknowledged = true;
        _baseTimer?.cancel();
        _errorMessage = null;
        if (_completionId == null) _stage = SOSStage.acknowledged;
        _complete('SOS', packet['messageId']);
      } else if (status == 'CHAT_RECEIVED') {
        _complete('CHAT', packet['messageId']);
        for (final message in _messages) {
          if (message.id == packet['messageId'] && !message.fromAuthority) {
            message.delivery = MessageDelivery.delivered;
          }
        }
      } else if (status == 'COMPLETION_RESPONSE_RECEIVED') {
        _complete('COMPLETION_RESPONSE', packet['messageId']);
      } else if (status == 'BASE_STATION_UNAVAILABLE') {
        for (final kind in ['CHAT', 'COMPLETION_RESPONSE']) {
          _complete(
            kind,
            packet['messageId'],
            'Base station unavailable. Please retry.',
          );
        }
      }
    } else if (type == 'CHAT' &&
        packet['sender'] == 'authority' &&
        packet['messageId'] is String &&
        packet['text'] is String) {
      final id = packet['messageId'] as String;
      if (!_messages.any((message) => message.id == id)) {
        _messages.add(
          SOSChatMessage(
            id: id,
            text: packet['text'],
            fromAuthority: true,
            createdAt: DateTime.now(),
            delivery: MessageDelivery.delivered,
          ),
        );
      }
    } else if (type == 'COMPLETION_REQUEST' && packet['messageId'] is String) {
      final id = packet['messageId'] as String;
      if (_completionId == null && !_handledCompletionIds.contains(id)) {
        _completionId = id;
        _stage = SOSStage.completionRequested;
      }
    }
    notifyListeners();
  }

  Future<void> sendChat(String text, {SOSChatMessage? retryMessage}) async {
    text = text.trim();
    if (!canChat) {
      throw Exception('Wait for AeroLink confirmation before chatting.');
    }
    if (text.isEmpty || utf8.encode(text).length > 600) {
      throw Exception('Enter a message of up to 600 UTF-8 bytes.');
    }
    final message =
        retryMessage ??
        SOSChatMessage(
          id: randomId('MSG'),
          text: text,
          fromAuthority: false,
          createdAt: DateTime.now(),
        );
    if (message.delivery == MessageDelivery.delivered) return;
    if (_pending.containsKey('CHAT:${message.id}')) return;
    if (retryMessage == null) _messages.add(message);
    message.delivery = MessageDelivery.sending;
    notifyListeners();
    try {
      await _sendAndWait({
        'type': 'CHAT',
        'sosId': sosId,
        'messageId': message.id,
        'sender': 'victim',
        'text': message.text,
      }, 'CHAT');
      message.delivery = MessageDelivery.delivered;
    } catch (_) {
      if (message.delivery != MessageDelivery.delivered) {
        message.delivery = MessageDelivery.unconfirmed;
      }
      rethrow;
    } finally {
      notifyListeners();
    }
  }

  Future<void> respondToCompletion(bool resolved) async {
    final id = _completionId;
    if (id == null || _responding) return;
    if (_completionDecision != null && _completionDecision != resolved) {
      throw Exception(
        'Your previous answer may already have arrived. Retry the same answer to confirm delivery.',
      );
    }
    _completionDecision = resolved;
    _responding = true;
    notifyListeners();
    try {
      await _sendAndWait({
        'type': 'COMPLETION_RESPONSE',
        'sosId': sosId,
        'messageId': randomId('MSG'),
        'requestId': id,
        'resolved': resolved,
      }, 'COMPLETION_RESPONSE');
      _handledCompletionIds.add(id);
      _completionId = null;
      _completionDecision = null;
      _stage = resolved
          ? SOSStage.completed
          : (baseStationAcknowledged
                ? SOSStage.acknowledged
                : SOSStage.confirmed);
      _errorMessage = null;
      if (resolved) _baseTimer?.cancel();
    } finally {
      _responding = false;
      notifyListeners();
    }
  }

  void reset({bool force = false}) {
    if (!force && (_sending || _responding || (_payload != null && _stage != SOSStage.completed && _stage != SOSStage.failed))) {
      return;
    }
    _statusPollTimer?.cancel();
    _baseTimer?.cancel();
    _payload = null;
    createdAt = null;
    _completionId = null;
    _completionDecision = null;
    _serverReportId = null;
    _messages.clear();
    _handledCompletionIds.clear();
    aeroLinkConfirmed = false;
    baseStationAcknowledged = false;
    _isDeliveredOnline = false;
    _deliveryPath = SOSDeliveryPath.checking;
    _lastTriageResult = null;
    _errorMessage = null;
    _stage = SOSStage.idle;
    notifyListeners();
  }

  @override
  void dispose() {
    _statusPollTimer?.cancel();
    _baseTimer?.cancel();
    _subscription.cancel();
    super.dispose();
  }
}
