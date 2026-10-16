import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/services/sos_service.dart';

void main() {
  late StreamController<Map<String, dynamic>> events;
  late SOSService service;
  late List<Map<String, dynamic>> sent;
  String? sosAck;
  bool replyToChat = true;
  bool replyToCompletion = true;

  void emit(
    String type, {
    String? status,
    String? id,
    Map<String, dynamic> extra = const {},
  }) {
    events.add({
      'type': type,
      'sosId': id ?? service.sosId,
      'status': status,
      ...extra,
    });
  }

  setUp(() {
    events = StreamController.broadcast(sync: true);
    sent = [];
    sosAck = 'SOS_RECEIVED';
    replyToChat = true;
    replyToCompletion = true;
    service = SOSService(
      events: events.stream,
      checkOnline: () async => false,
      ackTimeout: const Duration(milliseconds: 25),
      sendPacket: (packet) async {
        sent.add(packet);
        final type = packet['type'];
        final status = type == 'SOS'
            ? sosAck
            : type == 'CHAT' && replyToChat
            ? 'CHAT_RECEIVED'
            : type == 'COMPLETION_RESPONSE' && replyToCompletion
            ? 'COMPLETION_RESPONSE_RECEIVED'
            : null;
        if (status != null) {
          emit(
            'ACK',
            status: status,
            extra: {'messageId': packet['messageId']},
          );
        }
      },
    );
  });
  tearDown(() async {
    service.dispose();
    await events.close();
  });

  test(
    'oversized SOS leaves the form editable without creating a request',
    () async {
      final details = List.filled(1200, 'x').join();
      await expectLater(
        service.sendSOS('{"additionalDetails":"$details"}'),
        throwsException,
      );
      expect(service.stage, SOSStage.idle);
      expect(service.sosId, isNull);
      expect(sent, isEmpty);
    },
  );

  test(
    'lost completion reply cannot be retried with a contradictory answer',
    () async {
      await service.sendSOS('{}');
      emit('COMPLETION_REQUEST', extra: {'messageId': 'close'});
      replyToCompletion = false;
      await expectLater(service.respondToCompletion(true), throwsException);
      final count = sent.length;
      await expectLater(service.respondToCompletion(false), throwsException);
      expect(sent.length, count);
      replyToCompletion = true;
      await service.respondToCompletion(true);
      expect(service.stage, SOSStage.completed);
    },
  );

  test('device ACK confirms; only base ACK acknowledges; late device ACK cannot regress', () async {
    await service.sendSOS('{"peopleAffected":2}');
    expect(service.sosId, matches(RegExp(r'^SOS-[A-F0-9]{24}$')));
    expect(
      sent.single['timestamp'],
      service.createdAt!.toUtc().toIso8601String(),
    );
    expect(service.stage, SOSStage.confirmed);
    emit('ACK', status: 'BASE_STATION_RECEIVED', id: 'another-request');
    expect(service.stage, SOSStage.confirmed);
    emit('ACK', status: 'BASE_STATION_RECEIVED');
    expect(service.stage, SOSStage.acknowledged);
    emit('ACK', status: 'SOS_RECEIVED');
    expect(service.stage, SOSStage.acknowledged);
  });

  test('base ACK arriving before local ACK is sufficient', () async {
    sosAck = 'BASE_STATION_RECEIVED';
    await service.sendSOS('{}');
    expect(service.stage, SOSStage.acknowledged);
    expect(service.aeroLinkConfirmed, isTrue);
  });

  test('timeout and retry retain request ID, time and payload', () async {
    sosAck = null;
    await service.sendSOS('{"peopleAffected":3}');
    final id = service.sosId;
    final time = service.createdAt;
    expect(service.stage, SOSStage.failed);
    sosAck = 'SOS_RECEIVED';
    await service.retry();
    expect(service.sosId, id);
    expect(service.createdAt, time);
    expect(sent.last['peopleAffected'], 3);
    expect(sent.first['messageId'], isNot(sent.last['messageId']));
  });

  test('unavailable base still confirms local receipt', () async {
    sosAck = 'SOS_RECEIVED_BASE_STATION_UNAVAILABLE';
    await service.sendSOS('{}');
    expect(service.stage, SOSStage.confirmed);
    expect(service.baseStationAcknowledged, isFalse);
    expect(service.errorMessage, contains('unavailable'));
  });

  test(
    'chat uses separate acknowledgements and deduplicates authority replies',
    () async {
      await service.sendSOS('{}');
      await service.sendChat('We need water');
      expect(service.messages.single.delivery, MessageDelivery.delivered);
      expect(service.stage, SOSStage.confirmed);
      final reply = {
        'messageId': 'authority-1',
        'sender': 'authority',
        'text': 'Help is coming',
      };
      emit('CHAT', extra: reply);
      emit('CHAT', extra: reply);
      emit('CHAT', id: 'wrong', extra: {...reply, 'messageId': 'authority-2'});
      expect(service.messages.length, 2);
      expect(service.messages.last.fromAuthority, isTrue);
    },
  );

  test('chat timeout is unconfirmed and retries the same message ID', () async {
    await service.sendSOS('{}');
    replyToChat = false;
    await expectLater(service.sendChat('Need help'), throwsException);
    final message = service.messages.single;
    expect(message.delivery, MessageDelivery.unconfirmed);
    replyToChat = true;
    await service.sendChat(message.text, retryMessage: message);
    expect(service.messages.length, 1);
    expect(service.messages.single.delivery, MessageDelivery.delivered);
    expect(sent[1]['messageId'], sent[2]['messageId']);
  });

  test('closure requires victim approval and base receipt; rejection keeps SOS open', () async {
    sosAck = 'BASE_STATION_RECEIVED';
    await service.sendSOS('{}');
    emit('COMPLETION_REQUEST', extra: {'messageId': 'close-1'});
    expect(service.stage, SOSStage.completionRequested);
    await service.respondToCompletion(false);
    expect(service.stage, SOSStage.acknowledged);
    emit('COMPLETION_REQUEST', extra: {'messageId': 'close-1'});
    expect(service.completionId, isNull);
    emit('COMPLETION_REQUEST', extra: {'messageId': 'close-2'});
    replyToCompletion = false;
    await expectLater(service.respondToCompletion(true), throwsException);
    expect(service.stage, SOSStage.completionRequested);
    replyToCompletion = true;
    await service.respondToCompletion(true);
    expect(service.stage, SOSStage.completed);
    emit('ACK', status: 'SOS_RECEIVED');
    expect(service.stage, SOSStage.completed);
  });

  test(
    'cannot clear an active request; new completed request gets a new ID',
    () async {
      await service.sendSOS('{}');
      final original = service.sosId;
      service.reset();
      expect(service.sosId, original);
      emit('COMPLETION_REQUEST', extra: {'messageId': 'close'});
      await service.respondToCompletion(true);
      service.reset();
      expect(service.stage, SOSStage.idle);
      await service.sendSOS('{}');
      expect(service.sosId, isNot(original));
    },
  );

  test('uncorrelated completion requests are ignored', () async {
    await service.sendSOS('{}');
    events.add({'type': 'COMPLETION_REQUEST', 'messageId': 'missing-sos'});
    emit('COMPLETION_REQUEST', id: 'wrong', extra: {'messageId': 'wrong-sos'});
    expect(service.completionId, isNull);
  });
}
